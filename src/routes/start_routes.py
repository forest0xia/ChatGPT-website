from flask import Blueprint, request, jsonify, abort, current_app
from datetime import datetime
from pytz import utc

from ..database.db_config import db_collection_player
from ..config.settings import (
    DELTA_N_DAYS_SECONDS,
    DEFAULT_MAX_FRETBOTS_DIFF
)
from ..utils.version_utils import get_version_timestamp_from_request
from ..utils.ip_utils import get_ip_location

start_bp = Blueprint("start", __name__, url_prefix="/")

def get_workshop_update_time():
    import requests
    from ..config.settings import WORKSHOP_ID, WORKSHOP_DETAILS_URL
    payload = {
        'itemcount': 1,
        'publishedfileids[0]': WORKSHOP_ID
    }
    response = requests.post(WORKSHOP_DETAILS_URL, data=payload)
    if response.status_code == 200:
        data = response.json()
        if 'publishedfiledetails' in data['response']:
            return data['response']['publishedfiledetails'][0]['time_updated']
    return None

@start_bp.route("/start", methods=["POST"])
def start():
    response_data = None
    try:
        req_data = request.get_json()
        current_app.logger.info(f"Api start request data: {req_data}")

        if not req_data:
            return jsonify({"error": "Invalid or missing JSON data"}), 400

        local_version = req_data.get("version", "")
        players = req_data.get("pinfo", [])
        host_id = req_data.get("host_id")
        fretbots = req_data.get("fretbots", {})
        fretbots_diff = fretbots.get('difficulty', 0)
        fretbots_ally_scale = fretbots.get('allyScale', 1)

        local_version_timestamp = get_version_timestamp_from_request(local_version)
        update_time = get_workshop_update_time()

        updates_behind = 0
        if update_time and (update_time - DELTA_N_DAYS_SECONDS) > local_version_timestamp:
            updates_behind = 1

        response_data = {
            "updates_behind": updates_behind,
            "last_update_time": update_time
        }

        ip_addr = get_ip_location(request)
        utc_time = datetime.now(utc)

        # Just an example check for host's difficulty
        if host_id is not None and fretbots_ally_scale <= 1:
            current_app.logger.info(f"Validating host: {host_id} with fretbots diff: {fretbots_diff}.")
            for player in players:
                if player.get('steamId') == host_id:
                    tracking_record = db_collection_player.find_one({"steamId": host_id})
                    if tracking_record:
                        allowed_diff = min(fretbots_diff, tracking_record.get("allowed_diff", DEFAULT_MAX_FRETBOTS_DIFF))
                    else:
                        allowed_diff = min(fretbots_diff, DEFAULT_MAX_FRETBOTS_DIFF)
                    fretbots_diff = allowed_diff
                    response_data['allowed_diff'] = allowed_diff
                    response_data['needed_wins'] = 1
                    break

        for player in players:
            steamId = player.get('steamId')
            player_name = player.get('name')
            new_db_record = {
                "steamId": steamId,
                "createdTime": utc_time,
                "updatedTime": utc_time,
                "name": player_name,
                "fretbots_difficulty": fretbots_diff,
                "fretbots_allyScale": fretbots_ally_scale,
                "duplicateCount": 1
            }
            if ip_addr['is_valid']:
                new_db_record['ipAddr'] = ip_addr['ip']
                new_db_record['location'] = ip_addr['location']

            from pymongo import errors
            try:
                db_collection_player.insert_one(new_db_record)
            except errors.DuplicateKeyError:
                db_collection_player.update_one(
                    {"steamId": steamId},
                    {
                        "$set": {
                            "name": player_name,
                            "updatedTime": utc_time,
                            "fretbots_difficulty": fretbots_diff,
                            "fretbots_allyScale": fretbots_ally_scale,
                            "ipAddr": ip_addr['ip'] if ip_addr['is_valid'] else None,
                            "location": ip_addr['location'] if ip_addr['is_valid'] else None,
                        },
                        "$inc": {"duplicateCount": 1}
                    },
                    upsert=True
                )

    except Exception as e:
        current_app.logger.error(f"Api start error: {e}")
        abort(500, description=str(e))

    return jsonify(response_data), 200
