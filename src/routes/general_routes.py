# app/routes/general_routes.py
from flask import Blueprint, request, jsonify

general_bp = Blueprint("general", __name__, url_prefix="/")

@general_bp.route("/ping", methods=["GET"])
def ping():
    return jsonify("pong"), 200

@general_bp.route("/uuid", methods=["GET"])
def get_uuid():
    import uuid
    unique_id = str(uuid.uuid4())
    return jsonify({"uuid": unique_id}), 200

@general_bp.route("/", methods=["GET"])
def index():
    from flask import render_template
    return render_template("chat.html")
