# from google.cloud import secretmanager

_secret_cache = {}  # Initialize a dictionary to hold cached secrets

def get_secret_value(secret_name):
    """Retrieves the value of a Secret Manager secret, using cache."""

    # Don't use GCP yet.
    return None

    if secret_name in _secret_cache:
        return _secret_cache[secret_name]

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/dota2bots/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        value = response.payload.data.decode('UTF-8')
        return value
    except Exception as e:
        print(f"Error calling GCP API: {e}")
    _secret_cache[secret_name] = None # Store value in cache
    return None

OPENAI_API_KEY = get_secret_value("envvar-OPENAI_API_KEY")
GEMINI_API_KEY = get_secret_value("envvar-GEMINI_API_KEY")

ENV_STAGE = get_secret_value("envvar-STAGE")
ENV_DB_PASS = get_secret_value("envvar-DB_PASS")
ENV_IP_KEY = get_secret_value("envvar-IP_KEY")

if __name__ == "__main__":
    print(f"Keys from GCP:")
    print(f"API Key: {OPENAI_API_KEY}")
    print(f"DB Pass: {ENV_DB_PASS}")
    print(f"IP Key: {ENV_IP_KEY}")
    print(f"GEMINI API Key: {GEMINI_API_KEY}")
    print(f"Stage: {ENV_STAGE}")
