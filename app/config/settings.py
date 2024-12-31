import os
import json

# Environment
STAGE = os.environ.get('STAGE', 'prod')

# SECRET_KEY（flask项目密钥,不用管,也用不到）
SECRET_KEY = ""
# openAi api key
OPENAI_API_KEY = ""

# openAi 官方 api
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
# openAi 代理 api
# OPENAI_API_URL = "https://open.aiproxy.xyz/v1/chat/completions"

# GPT Models
GPT_MODEL_4mini = "gpt-4o-mini"
GPT_MODEL_4o = "gpt-4o"
GOT_MODEL_3d5 = "gpt-3.5-turbo"

# Max tokens per GPT request
MAX_TOKEN_PER_REQUEST = 1000


# Workshop
WORKSHOP_ID = 3246316298
WORKSHOP_DETAILS_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

# only allow x requests across all dota2 (from a steam client) users per hour.
MAX_REQUEST_PER_HOUR = 90
# only allow x requests for individual dota2 (from a steam client) user per hour.
MAX_USER_REQUESTS_PER_HOUR = 30
# only allow x requests across all website users (not from a steam client) per hour.
MAX_WEBSITE_REQUESTS_PER_HOUR = 6
# only allow x requests for individual website user (not from a steam client) per hour.
MAX_WEBSITE_USER_REQUESTS_PER_HOUR = 3

# Ensure the total number of messages does not exceed x, should always keep the default prompts at the top
MAX_MESSAGES_COUNT_PER_REQUEST = 10

# Ports, timeouts
PRODUCTION_SERVER_PORT = 5000
DEV_SERVER_PORT = 5000
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
DB_PASS = os.environ.get('DB_PASS')
if DB_PASS is None:
    print('DB_PASS is None. Check your environment settings.')

# IP info key
IPINFO_KEY = os.environ.get('IP_KEY')
if IPINFO_KEY is None:
    print('IPINFO_KEY is None. Check your environment settings.')

# Path to country names JSON
COUNTRY_NAMES_JSON = os.path.join(os.path.dirname(__file__), '..', 'config', 'country_names.json')
# Load country names from the JSON file once
with open(COUNTRY_NAMES_JSON, 'r') as f:
    COUNTRY_NAMES = json.load(f)
