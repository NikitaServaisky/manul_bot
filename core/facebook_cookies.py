import json
import os
import logging

logger = logging.getLogger(__name__)


# Loading  facebook cookies
def load_facebook_cookies():
    file_path = "config/facebook_cookies.json"
    if not os.path.exists(file_path):
        logger.error(
            f"❌ Cookies file missing at {file_path}! Run will be unauthorized."
        )
        return []

    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Failed to parse cookies JSON: {e}")
        return []
