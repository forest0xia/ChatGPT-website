import os
import json
from src.utils.gcp_utils import (
    ENV_STAGE,
    ENV_DB_PASS,
    ENV_IP_KEY
)

# Environment
STAGE = os.environ.get('STAGE') or ENV_STAGE or 'prod'

# OpenAi api key
OPENAI_API_KEY = ""

# OpenAi api
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
# Gemini api
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

# GPT Models
GPT_MODEL_4mini = "gpt-4o-mini"
GPT_MODEL_4o = "gpt-4o"
GOT_MODEL_3d5 = "gpt-3.5-turbo"
GEMINI_MODEL_1_5_FLASH = "gemini-1.5-flash"

# Max tokens per GPT request
MAX_TOKEN_PER_REQUEST = 1000


# Steam Workshop
WORKSHOP_ID = 3246316298
WORKSHOP_DETAILS_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

# only allow x requests for individual dota2 (from a steam client) user per min.
MAX_USER_REQUESTS_PER_MIN = 5
# only allow x requests across all dota2 (from a steam client) users per min.
MAX_SERVICE_REQUESTS_PER_MIN = 15
# only allow x requests across all dota2 (from a steam client) users per hour.
MAX_REQUEST_PER_HOUR = 60
# only allow x requests for individual dota2 (from a steam client) user per hour.
MAX_USER_REQUESTS_PER_HOUR = 30
# only allow x requests across all website users (not from a steam client) per hour.
MAX_WEBSITE_REQUESTS_PER_HOUR = 6
# only allow x requests for individual website user (not from a steam client) per hour.
MAX_WEBSITE_USER_REQUESTS_PER_HOUR = 3

# Ensure the total number of messages does not exceed x, should always keep the default prompts at the top
MAX_MESSAGES_COUNT_PER_REQUEST = 8

# Ports, timeouts
PRODUCTION_SERVER_PORT = 8080
DEV_SERVER_PORT = 8080
REQUEST_TIMEOUT = 10

# Difficulty logic
DEFAULT_MAX_FRETBOTS_DIFF = 3
MAX_FRETBOTS_DIFF = 10

# Time offsets
DELTA_N_DAYS_SECONDS = 3 * 86400

# Keep server alive
BACKGROUND_REFRESH_URL = 'https://chatgpt-with-dota2bot.onrender.com/ping'
URL_TO_KEEP_VISITING = "https://steamcommunity.com/sharedfiles/filedetails/?id=3246316298"
PERIODIC_DURATION = 20

# Database
DB_PASS = os.environ.get('DB_PASS') or ENV_DB_PASS
if DB_PASS is None:
    print('DB_PASS is None. Check your environment settings.')

# IP info key
IPINFO_KEY = os.environ.get('IP_KEY') or ENV_IP_KEY
if IPINFO_KEY is None:
    print('IPINFO_KEY is None. Check your environment settings.')

# Path to country names JSON
COUNTRY_NAMES_JSON = os.path.join(os.path.dirname(__file__), '..', 'config', 'country_names.json')
# Load country names from the JSON file once
with open(COUNTRY_NAMES_JSON, 'r') as f:
    COUNTRY_NAMES = json.load(f)
