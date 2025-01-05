from flask import Blueprint, request, current_app

from src.services.gemini_service import process_gemini_request
from ..services.chat_request_handler import ChatRequestHandler
from ..services.openai_service import process_openai_request
from ..utils.message_filter_utils import filter_user_messages

from ..config.settings import (
    WORKSHOP_ID
)

chat_bp = Blueprint("chat", __name__, url_prefix="/")

# The single instance of RequestHandler for your app
chat_request_handler = ChatRequestHandler()

def get_workshop_update_time():
    import requests
    from ..config.settings import WORKSHOP_ID
    url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    payload = {
        'itemcount': 1,
        'publishedfileids[0]': WORKSHOP_ID
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        data = response.json()
        if 'publishedfiledetails' in data['response']:
            time_updated = data['response']['publishedfiledetails'][0]['time_updated']
            return time_updated
    return None

@chat_bp.route("/chat", methods=["POST"])
def chat():
    return chat_request_handler.chat_handle_request(
        request,
        get_workshop_update_time,
        filter_user_messages,
        process_gemini_request
        # process_openai_request
    )
