from flask import Blueprint, request, jsonify, abort, current_app
from datetime import datetime
from pytz import utc

from ..database.db_config import db_collection_tracking, db_collection_player
from ..config.settings import (
    DEFAULT_MAX_FRETBOTS_DIFF,
    MAX_FRETBOTS_DIFF
)

end_bp = Blueprint("end", __name__, url_prefix="/")

@end_bp.route("/end", methods=["POST"])
def end_game():
    try:
        req_data = request.get_json()
        current_app.logger.info(f"Api end request data: {req_data}")

        if not req_data:
            return jsonify({"error": "Invalid or missing JSON data"}), 400

        host_id = req_data.get("host_id")
        winning_team = req_data.get("winning_team")
        fretbots_data = req_data.get("fretbots", {})
        cheat_list = req_data.get("cheated_list", [])
        time_passed = req_data.get("time_passed", 0)
        difficulty = fretbots_data.get("difficulty")
        ally_scale = fretbots_data.get("ally_scale")
        players = req_data.get("players", [])

        if not host_id or difficulty is None:
            return jsonify({"error": "Missing required fields: 'host_id' or 'fretbots.difficulty'"}), 400

        now = datetime.now(utc)
        game_record = {
            "host_id": host_id,
            "players": players,
            "teams": req_data.get("teams", {}),
            "mode": req_data.get("mode", ""),
            "winning_team": winning_team,
            "time_passed": time_passed,
            "version": req_data.get("version", ""),
            "cheated_list": cheat_list,
            "fretbots_difficulty": difficulty,
            "fretbots_ally_scale": ally_scale,
            "createdTime": now,
        }

        db_collection_tracking.insert_one(game_record)
        current_app.logger.info(
            f"Inserted post-game record for steamId: {host_id}, difficulty: {difficulty}, ally_scale: {ally_scale}"
        )

        for player in players:
            steam_id = player.get('steam_id')
            if not steam_id:
                continue
            player_doc = db_collection_player.find_one({"steamId": steam_id})
            if player_doc:
                previous_allowed_diff = player_doc.get("allowed_diff", DEFAULT_MAX_FRETBOTS_DIFF)
                time_started_in_db = player_doc.get("updatedTime", now)
                # Make sure time_started is timezone aware:
                if time_started_in_db.tzinfo is None:
                    time_started_in_db = time_started_in_db.replace(tzinfo=utc)
            else:
                previous_allowed_diff = DEFAULT_MAX_FRETBOTS_DIFF
                time_started_in_db = now

            allowed_diff = previous_allowed_diff
            begin_ally_scale = player_doc.get("fretbots_allyScale", 1) if player_doc else 1
            begin_diff = player_doc.get("fretbots_difficulty", 0) if player_doc else 0

            # Logic from function check_diff_increase_eligiable
            if begin_ally_scale == ally_scale and begin_diff == difficulty:
                if _check_diff_increase_eligible(winning_team, time_passed, player.get('team'), cheat_list, ally_scale, now, time_started_in_db):
                    allowed_diff = max(previous_allowed_diff, difficulty + 1)
            else:
                current_app.logger.warning(
                    f"Fretbots mismatch: start allyScale: {begin_ally_scale}, end allyScale: {ally_scale},"
                    f" start diff: {begin_diff}, end diff: {difficulty}"
                )
            allowed_diff = min(allowed_diff, MAX_FRETBOTS_DIFF)

            update_fields = {
                "steamId": steam_id,
                "name": player.get('player_name'),
                "updatedTime": now,
                "allowed_diff": allowed_diff
            }

            db_collection_player.update_one(
                {"steamId": steam_id},
                {
                    "$set": update_fields,
                    "$inc": {"duplicateCount": 1}
                },
                upsert=True
            )
            current_app.logger.info(
                f"Updated player-data for steamId: {steam_id}, allowed_diff: {allowed_diff}"
            )

        return jsonify({"message": "Post-game data processed.", "allowed_diff": allowed_diff}), 200

    except Exception as e:
        current_app.logger.error(f"Api end error: {e}")
        abort(500, description=str(e))

def _check_diff_increase_eligible(winning_team, time_passed, player_team, cheat_list, ally_scale, now, time_started):
    if not winning_team:
        current_app.logger.info("Cannot increase diff: winning team is invalid.")
        return False
    if time_passed < 900:
        current_app.logger.info("Cannot increase diff: match time < 15 minutes.")
        return False
    if (now - time_started).total_seconds() < 900:
        current_app.logger.info("Cannot increase diff: start time in DB was not valid.")
        return False
    if winning_team != player_team:
        current_app.logger.info(f"Cannot increase diff: player lost. player_team={player_team}")
        return False
    if ally_scale > 0.5:
        current_app.logger.info(f"Cannot increase diff: ally scale too high: {ally_scale}")
        return False
    if cheat_list:
        current_app.logger.info(f"Cannot increase diff: player cheated. cheat_list={cheat_list}")
        return False
    return True
