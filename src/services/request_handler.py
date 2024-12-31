from datetime import datetime, timedelta
from collections import defaultdict
from flask import request, jsonify, current_app

from ..config.settings import (
    MAX_REQUEST_PER_HOUR,
    MAX_USER_REQUESTS_PER_HOUR,
    MAX_WEBSITE_REQUESTS_PER_HOUR,
    MAX_WEBSITE_USER_REQUESTS_PER_HOUR,
    WORKSHOP_ID,
    DELTA_N_DAYS_SECONDS
)
from ..utils.version_utils import get_version_timestamp_from_request
from ..utils.ip_utils import get_ip_location
from ..database.db_config import db_collection_chat
from pymongo import errors
from pytz import utc

class RequestHandler:
    def __init__(
        self,
        max_requests_per_hour=MAX_REQUEST_PER_HOUR,
        max_user_requests_per_hour=MAX_USER_REQUESTS_PER_HOUR
    ):
        self.max_requests_per_hour = max_requests_per_hour
        self.max_user_requests_per_hour = max_user_requests_per_hour
        self.total_requests_count = 0
        self.user_requests_count = defaultdict(int)
        self.start_time = datetime.now()
        self.user_start_times = defaultdict(datetime.now)

    def validate_request(self, req_data, get_workshop_update_time):
        try:
            local_version = req_data.get("version", "")
            local_version_timestamp = get_version_timestamp_from_request(local_version)
            scriptID = req_data.get("scriptID", "")
            nameSuffix = req_data.get("nameSuffix", "")

            if scriptID != WORKSHOP_ID:
                raise Exception(f"Wrong script id: {scriptID}")

            update_time = get_workshop_update_time()  # e.g. 1725174880
            # Validate if behind more than DELTA_N_DAYS_SECONDS
            if update_time and (update_time - DELTA_N_DAYS_SECONDS) > local_version_timestamp:
                raise Exception(f"Wrong version timestamp: {local_version}")

            if nameSuffix != "OHA":
                raise Exception(f"Wrong bot's name suffix: {nameSuffix}")

        except Exception as e:
            return False
        return True

    def handle_request(self, flask_request, get_workshop_update_time, filter_user_messages, process_openai_request):
        try:
            # Log the raw data
            # print(f'Received raw data: {request.data}')

            current_time = datetime.now()
            req_data = flask_request.get_json()

            current_app.logger.info(f"Api chat request data: {req_data}")

            if not req_data:
                return jsonify({"error": "Invalid or missing JSON data"}), 400

            # Check request validity
            if not self.validate_request(req_data, get_workshop_update_time):
                return jsonify({"error": "Invalid request. Update the script or check the Workshop page."}), 400

            last_message = req_data.get("prompts", [{}])[-1]
            user_agent = str(flask_request.user_agent)

            # Distinguish requests from Steam client vs website
            if "Steam" in user_agent:
                # In your code, you decode the last user message to find steamId
                import json
                json_message = json.loads(last_message.get('content', '{}'))
                steam_id = json_message.get('player', {}).get('steamId')
                if not steam_id:
                    return jsonify({"error": "Missing 'steamId' in JSON data"}), 400

                self.max_user_requests_per_hour = MAX_USER_REQUESTS_PER_HOUR
                self.max_requests_per_hour = MAX_REQUEST_PER_HOUR
            else:
                steam_id = user_agent
                self.max_user_requests_per_hour = MAX_WEBSITE_USER_REQUESTS_PER_HOUR
                self.max_requests_per_hour = MAX_WEBSITE_REQUESTS_PER_HOUR

            # Reset total requests count if an hour has passed
            if current_time - self.start_time >= timedelta(hours=1):
                self.total_requests_count = 0
                self.start_time = current_time

            # Reset user requests count if an hour has passed
            user_start_time = self.user_start_times[steam_id]
            if current_time - user_start_time >= timedelta(hours=1):
                self.user_requests_count[steam_id] = 0
                self.user_start_times[steam_id] = current_time

            # Enforce request limits
            if self.user_requests_count[steam_id] >= self.max_user_requests_per_hour:
                time_since_start = current_time - user_start_time
                formatted_time_remaining = str(timedelta(hours=1) - time_since_start).split('.')[0]
                current_app.logger.warning(
                    f'User request limit reached: {self.max_user_requests_per_hour}, user: {steam_id}'
                )
                err_msg = f"User request limit reached. Try again in {formatted_time_remaining}"
                raise Exception(err_msg)

            if self.total_requests_count >= self.max_requests_per_hour:
                time_since_start = current_time - self.start_time
                formatted_time_remaining = str(timedelta(hours=1) - time_since_start).split('.')[0]
                current_app.logger.warning(
                    f'Server total request limit reached: {self.max_requests_per_hour}, user: {steam_id}'
                )
                err_msg = f"Total request limit reached. Try again in {formatted_time_remaining}"
                raise Exception(err_msg)

            # If limits not exceeded, increment usage
            self.user_requests_count[steam_id] += 1
            self.total_requests_count += 1

            # Grab IP location
            ip_addr = get_ip_location(flask_request)
            current_app.logger.info(f"Chat caller IP: {ip_addr}, steam_id: {steam_id}")

            # Finally process the request => forward to the OpenAI service
            return self.process_request(flask_request, steam_id, filter_user_messages, process_openai_request)

        except Exception as e:
            current_app.logger.exception(f'Error: {str(e)}')
            return jsonify({"error": "Internal Server Error", "message": str(e)}), 400

    def process_request(self, flask_request, steam_id, filter_user_messages, process_openai_request):
        req_data = flask_request.get_json()
        if req_data is None:
            return jsonify({"error": "Invalid or missing JSON data"}), 400

        messages = req_data.get("prompts", [])
        messages = filter_user_messages(messages)

        if not messages:
            return jsonify({"error": "Missing 'prompts' in JSON data"}), 400

        # Quick sanity check/ping
        if 'How do you feel at this very moment' in messages[-1].get("content", ""):
            return jsonify({"ping": "pong"}), 200

        # Persist last user message to DB
        from datetime import datetime
        from pytz import utc
        utc_time = datetime.now(utc)
        last_message = messages[-1].get('content', '')

        current_app.logger.info(f"Last message: {last_message}")

        new_db_record = {
            "createdTime": utc_time,
            "updatedTime": utc_time,
            "message": last_message,
            "steamId": steam_id,
            "duplicateCount": 1
        }
        try:
            db_collection_chat.insert_one(new_db_record)
        except errors.DuplicateKeyError:
            db_collection_chat.update_one(
                {"steamId": steam_id},
                {
                    "$set": {"updatedTime": utc_time, "message": last_message},
                    "$inc": {"duplicateCount": 1}
                },
                upsert=True
            )
        except Exception as e:
            current_app.logger.error(f"Failed to persist to db: {str(e)}")

        # Offload actual OpenAI streaming logic to a separate function
        return process_openai_request(flask_request, messages)
