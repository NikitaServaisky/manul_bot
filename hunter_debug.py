import os
import requests
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

try:
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    print(f"Failed to initialize Groq: {e}")

def load_list_from_file(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def escape_markdown(text):
    """Escapes ALL special characters for Telegram MarkdownV2."""
    if not text:
        return ""
    # רשימת התווים שחובה לברוח מהם ב-MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2"
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        if result.get("ok"):
            print("✅ Message sent successfully with MarkdownV2")
        else:
            print(f"❌ TELEGRAM ERROR: {result.get('description')}")
            # Fallback: אם נכשל, שלח טקסט נקי בלי עיצוב בכלל
            payload.pop("parse_mode")
            requests.post(url, json=payload)
        return result
    except Exception as e:
        print(f"Error: {e}")

# --- Mock Data ---
MOCK_POSTS = [
    {"text": "היי חברים, יש לי אאודי A3 שנת 2018 ויש רעש מוזר מהגיר DSG. מישהו מכיר מוסך מומחה באזור הדרום?", "id": "HEB_VAG", "url": "https://fb.com/1"},
    {"text": "У меня проблема с коробкой передач в Шкоде. Нужен механик.", "id": "RUS_VAG", "url": "https://fb.com/2"},
    {"text": "عندي مشكلة في جير الأودي. حد بيعرف كراج متخصص؟", "id": "ARB_VAG", "url": "https://fb.com/3"},
    {"text": "My Volkswagen Golf has a check engine light on.", "id": "ENG_VAG", "url": "https://fb.com/4"}
]

def analyze_post_with_ai(post_text, keywords):
    found_keywords = [kw for kw in keywords if re.search(rf"\b{kw}\b", post_text, re.IGNORECASE)]
    if not found_keywords:
        return "Relevant: No\nReason: No matching keywords found."

    prompt = f"Is this person looking for a mechanic? POST: '{post_text}'. Return only: Relevant: [Yes/No]\nReason: [Short English]"
    
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

def run_debug_test():
    print("🚀 Starting Multilingual Debug Test...")
    keywords = load_list_from_file("keywords.txt")
    
    for post in MOCK_POSTS:
        print(f"\n--- Checking [{post['id']}] ---")
        analysis = analyze_post_with_ai(post['text'], keywords)
        
        if "Yes" in analysis:
            # כאן קורה הקסם - אנחנו בורחים מכל הטקסטים
            clean_text = escape_markdown(post['text'][:200])
            clean_analysis = escape_markdown(analysis)
            clean_url = escape_markdown(post['url'])
            
            # בניית הודעה בפורמט MarkdownV2 תקין
            msg = (
                f"🎯 *NEW LEAD FOUND\\!*"
                f"\n\n*Post:* {clean_text}"
                f"\n\n*Analysis:* {clean_analysis}"
                f"\n\n[Link to Post]({clean_url})"
            )
            send_telegram_message(msg)
        else:
            print(f"❌ Not Relevant: {analysis}")

if __name__ == "__main__":
    run_debug_test()