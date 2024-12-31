import requests
from flask import request, abort, current_app
from ..config.settings import IPINFO_KEY
from ..utils.cache_utils import ipResultCache
from ..config.settings import COUNTRY_NAMES

def get_ip_address(flask_request):
    # If behind a proxy, you might want to handle X-Forwarded-For
    client_ip = flask_request.access_route[0]
    return client_ip

def get_ip_location(flask_request):
    client_ip = get_ip_address(flask_request)

    # Check cache
    if client_ip in ipResultCache:
        current_app.logger.info(f"Client ip `{client_ip}` exists in cache.")
        return ipResultCache[client_ip]

    current_app.logger.info(f"Client ip `{client_ip}` does not exist in cache.")

    if not IPINFO_KEY:
        # If your service depends on this key, handle gracefully
        return {"is_valid": False, "ip": client_ip, "location": "Unknown IP_KEY missing"}

    try:
        geolocation_res = requests.get(
            f"https://ipinfo.io/{client_ip}/json?token={IPINFO_KEY}", timeout=5
        )
        geolocation = geolocation_res.json()

        country_code = geolocation.get("country")
        country = COUNTRY_NAMES.get(country_code, country_code)
        region = geolocation.get("region")
        city = geolocation.get("city")

        ip_addr = {
            "is_valid": country is not None,
            "ip": client_ip,
            "location": f"country: {country}, region: {region}, city: {city}",
        }

        # Cache the result
        ipResultCache[client_ip] = ip_addr
        return ip_addr

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error fetching location data: {e}")
        return {"is_valid": False, "ip": client_ip, "location": "Unknown"}
