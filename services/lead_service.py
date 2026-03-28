import os
import requests
from core.database import get_db
from services.ai_logic import analyze_lead_relevance
from core.utils import escape_md

def send_telegram_notification(text, url):
    """Sends a formatted message to the admin via Telegram API."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_ID")
    
    # Building the notification message
    message = f"🎯 *New Lead Found!*\n\n{escape_md(text[:300])}\n\n🔗 [Link to Post]({url})"
    
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2"
    }
    
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")

def check_and_save_lead(text, url):
    """Handles deduplication, AI analysis, DB saving, and notification."""
    with get_db() as conn:
        # 1. Uniqueness check (Avoid double processing)
        if conn.execute("SELECT 1 FROM seen_leads WHERE url = ?", (url,)).fetchone():
            return False
            
        # 2. AI Relevance analysis
        if "Yes" in analyze_lead_relevance(text):
            # 3. Save to database
            conn.execute("INSERT INTO seen_leads (url) VALUES (?)", (url,))
            conn.execute("INSERT INTO leads (post_content, post_url) VALUES (?, ?)", (text, url))
            conn.commit()
            
            # 4. Notify admin via Telegram
            send_telegram_notification(text, url)
            return True
            
    return False