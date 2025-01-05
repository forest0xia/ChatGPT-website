from datetime import datetime, timedelta
from collections import defaultdict
import json
from flask import request, jsonify, current_app

from src.utils.message_filter_utils import verify_is_chat_command

from ..config.settings import (
    MAX_USER_REQUESTS_PER_MIN,
    MAX_SERVICE_REQUESTS_PER_MIN,
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

class RateExceededException(Exception): ...

class ChatRequestHandler:
    def __init__(self):
        self.max_requests_per_hour = MAX_REQUEST_PER_HOUR
        self.max_user_requests_per_hour = MAX_USER_REQUESTS_PER_HOUR
        self.total_requests_count_per_hour = 0
        self.user_requests_count_per_hour = defaultdict(int)
        self.start_time = datetime.now()
        self.user_start_times = defaultdict(datetime.now)
        
        # Add new rate limit attributes
        self.max_user_requests_per_min = MAX_USER_REQUESTS_PER_MIN
        self.max_service_requests_per_min = MAX_SERVICE_REQUESTS_PER_MIN
        self.total_requests_count_per_min = 0
        self.user_requests_count_per_min = defaultdict(int)
        self.start_time_per_min = datetime.now()
        self.user_start_times_per_min = defaultdict(datetime.now)


    def validate_request(self, req_data, get_workshop_update_time):
        try:
            local_version = req_data.get("version", "")
            local_version_timestamp = get_version_timestamp_from_request(local_version)
            scriptID = req_data.get("scriptID", "")
            nameSuffix = req_data.get("nameSuffix", "")

            if scriptID != WORKSHOP_ID:
                raise Exception(f"Wrong script id: {scriptID}")

            update_time = get_workshop_update_time()
            if update_time and (update_time - DELTA_N_DAYS_SECONDS) > local_version_timestamp:
                raise Exception(f"Wrong version timestamp: {local_version}")

            if nameSuffix != "OHA":
                raise Exception(f"Wrong bot's name suffix: {nameSuffix}")

        except Exception as e:
            current_app.logger.error(f"Request validation failed: {e}")
            return False
        return True

    def chat_handle_request(self, flask_request, get_workshop_update_time, filter_user_messages, process_gpt_request):
        try:
            current_time = datetime.now()
            req_data = flask_request.get_json()

            current_app.logger.info(f"Api chat request data: {req_data}")

            if not req_data:
                return jsonify({"error": "Invalid or missing JSON data"}), 400

            if not self.validate_request(req_data, get_workshop_update_time):
                return jsonify({"error": "Invalid request. Update the script or check the Workshop page."}), 400

            last_message = req_data.get("prompts", [{}])[-1]
            user_agent = str(flask_request.user_agent)

            if "Steam" in user_agent:
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

            # Grab IP location
            ip_addr = get_ip_location(flask_request)
            user_tracking_id = ip_addr['ip'] # user ip instead of steam id to track user request count because steam id could be modified easily.
            current_app.logger.info(f"Chat caller IP: {ip_addr}, steam_id: {steam_id}")

            # Reset hourly counters if an hour has passed
            if current_time - self.start_time >= timedelta(hours=1):
                self.total_requests_count_per_hour = 0
                self.start_time = current_time
                current_app.logger.info("Hourly total request count reset")

            user_start_time = self.user_start_times[user_tracking_id]
            if current_time - user_start_time >= timedelta(hours=1):
                self.user_requests_count_per_hour[user_tracking_id] = 0
                self.user_start_times[user_tracking_id] = current_time
                current_app.logger.info(f"Hourly user request count reset, user: {steam_id}")

            # Reset per minute counters
            if current_time - self.start_time_per_min >= timedelta(minutes=1):
                self.total_requests_count_per_min = 0
                self.start_time_per_min = current_time
                current_app.logger.info("Minute total request count reset")

            user_start_time_per_min = self.user_start_times_per_min[user_tracking_id]
            if current_time - user_start_time_per_min >= timedelta(minutes=1):
                self.user_requests_count_per_min[user_tracking_id] = 0
                self.user_start_times_per_min[user_tracking_id] = current_time
                current_app.logger.info(f"Minute user request count reset, user: {steam_id}")


            # Enforce request limits (per min)
            if self.user_requests_count_per_min[user_tracking_id] >= self.max_user_requests_per_min:
                time_since_start = current_time - user_start_time_per_min
                formatted_time_remaining = str(timedelta(minutes=1) - time_since_start).split('.')[0]
                current_app.logger.warning(
                    f'User request limit reached (per min): {self.max_user_requests_per_min}, user: {steam_id}'
                )
                err_msg = f"User request limit reached. Try again in {formatted_time_remaining}"
                raise RateExceededException(err_msg)

            if self.total_requests_count_per_min >= self.max_service_requests_per_min:
                time_since_start = current_time - self.start_time_per_min
                formatted_time_remaining = str(timedelta(minutes=1) - time_since_start).split('.')[0]
                current_app.logger.warning(
                    f'Server total request limit reached (per min): {self.max_service_requests_per_min}, user: {steam_id}'
                )
                err_msg = f"Total request limit reached. Try again in {formatted_time_remaining}"
                raise RateExceededException(err_msg)
            
            # Enforce request limits (per hour)
            if self.user_requests_count_per_hour[user_tracking_id] >= self.max_user_requests_per_hour:
                time_since_start = current_time - user_start_time
                formatted_time_remaining = str(timedelta(hours=1) - time_since_start).split('.')[0]
                current_app.logger.warning(
                    f'User request limit reached (per hour): {self.max_user_requests_per_hour}, user: {steam_id}'
                )
                err_msg = f"User request limit reached. Try again in {formatted_time_remaining}"
                raise RateExceededException(err_msg)

            if self.total_requests_count_per_hour >= self.max_requests_per_hour:
                time_since_start = current_time - self.start_time
                formatted_time_remaining = str(timedelta(hours=1) - time_since_start).split('.')[0]
                current_app.logger.warning(
                    f'Server total request limit reached (per hour): {self.max_requests_per_hour}, user: {steam_id}'
                )
                err_msg = f"Total request limit reached. Try again in {formatted_time_remaining}"
                raise RateExceededException(err_msg)


            # If limits not exceeded, increment usage
            self.user_requests_count_per_hour[user_tracking_id] += 1
            self.total_requests_count_per_hour += 1
            self.user_requests_count_per_min[user_tracking_id] += 1
            self.total_requests_count_per_min += 1


            # Finally process the request => forward to the OpenAI service
            return self.process_request(flask_request, steam_id, filter_user_messages, process_gpt_request)

        except RateExceededException as e:
            e_msg = str(e)
            current_app.logger.exception(f'Error: {e_msg}')
            return jsonify({"error": e_msg, "message": e_msg}), 200
        except Exception as e:
            e_msg = str(e)
            current_app.logger.exception(f'Error: {e_msg}')
            return jsonify({"error": "Internal Server Error", "message": e_msg}), 400

    def process_request(self, flask_request, steam_id, filter_user_messages, process_gpt_request):
        req_data = flask_request.get_json()
        if req_data is None:
            return jsonify({"error": "Invalid or missing JSON data"}), 400

        messages = req_data.get("prompts", [])
        messages = filter_user_messages(messages)

        if not messages:
            return jsonify({"error": "Missing 'prompts' in JSON data"}), 400

        if 'How do you feel at this very moment' in messages[-1].get("content", ""):
            return jsonify({"ping": "pong"}), 200

        # Persist last user message to DB
        from datetime import datetime
        from pytz import utc
        utc_time = datetime.now(utc)
        last_message = messages[-1].get('content', '')

        last_message_said = json.loads(last_message)["said"]
        if verify_is_chat_command(last_message_said):
            current_app.logger.warning(f"Message contains chat command: {last_message_said}. Stop processing.")
            return ""

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

        gpt_response = process_gpt_request(flask_request, messages)
        chat_item_for_log = {
            "user_message": last_message_said,
            "gpt_response": gpt_response
        }
        current_app.logger.info(f"Processed chat request: {chat_item_for_log}")
        return gpt_response
