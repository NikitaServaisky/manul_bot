import os
import requests
import logging
from core.database import get_db
from services.ai_logic import analyze_lead_relevance
from core.utils import escape_md

# Setup logger for this file
logger = logging.getLogger(__name__)


def send_telegram_notification(text, url):
    """Sends a formatted message to the admin via Telegram API."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_ID")

    # Building the notification message
    message = (
        f"<b>🎯 New Lead Found!</b>\n\n"
        f"{text[:300]}...\n\n"
        f"<a href='{url}'>🔗 Link to Post</a>"
    )

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        logger.exception(f"Failed to send Telegram notification: {e}")


def check_and_save_lead(text, url):
    """Handles deduplication, AI analysis, DB saving, and notification."""
    with get_db() as conn:
        try:
            cursor = conn.cursor()
            # 1. Faster uniquenss check
            # We only check 'seen_leads' to decide if we proceed
            cursor.execute("SELECT 1 FROM seen_leads WHERE url = %s", (url,))
            if cursor.fetchone():
                return False

            # 2. AI Relevance analysis (only if new)
            if analyze_lead_relevance(text) != "YES":
                # Optional: Mark as seen if not relevant to avoid re-analyzing
                cursor.execute("INSERT INTO seen_leads (url) VALUES (%s)", (url,))
                conn.commit()
                return False

            # 3. Save to database (Transaction safty)
            # using placeholders to prevent SQL injection (standart practice)
            cursor.execute("INSERT INTO seen_leads (url) VALUES (%s)", (url,))
            cursor.execute(
                "INSERT INTO LEADS (post_content, post_url) VALUES (%s, %s)",
                (text, url),
            )
            conn.commit()

            # 4. Notify admin via Telegram
            send_telegram_notification(text, url)
            return True

        except Exception as e:
            logger.exception(f"Error in check_and_save_lead: {e}")
            conn.rollback()
            return False
