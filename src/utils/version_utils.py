import time
from datetime import datetime

def get_version_timestamp_from_request(local_version: str) -> int:
    """
    Extract a date from the version string, parse it, return Unix timestamp.
    Example local_version format: "0.7.37c - 2024/8/31"
    """
    # Date substring is typically the last part
    date_str = local_version.split()[-1]  # e.g. "2024/8/31"
    date_format = "%Y/%m/%d"
    datetime_obj = datetime.strptime(date_str, date_format)
    timestamp = int(time.mktime(datetime_obj.timetuple()))
    return timestamp
