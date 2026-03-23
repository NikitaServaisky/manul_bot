import os
import sqlite3
import requests
import base64
from groq import Groq
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def init_all_dbs():
    """Initializes all necessary tables with CRM-ready fields."""
    with sqlite3.connect("manul_leads.db") as conn:
        # Leads table - Advanced for CRM
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                post_content TEXT, 
                post_url TEXT UNIQUE, 
                status TEXT DEFAULT 'new',
                source TEXT DEFAULT 'facebook',
                car_model_guess TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Marketing table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS marketing_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT,
                generated_content TEXT,
                platform TEXT DEFAULT 'facebook',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trigger to automatically update the 'updated_at' timestamp
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_lead_timestamp 
            AFTER UPDATE ON leads
            BEGIN
                UPDATE leads SET updated_at = CURRENT_TIMESTAMP WHERE id = old.id;
            END;
        """)
    print("✅ Database initialized and CRM-ready.")

def analyze_with_ai(post_text, keywords, lang="Russian"):
    prompt = f"""
    Identify if this person needs mechanical help for their car.
    POST: "{post_text}"
    KEYWORDS: {keywords}
    Provide 'Reason' ONLY in {lang}.
    Format:
    Relevant: [Yes/No]
    Reason: [Explanation in {lang}]
    """
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

def save_lead(content, url, db_name="manul_leads.db", status="new"):
    with sqlite3.connect(db_name) as conn:
        conn.execute("INSERT INTO leads (post_content, post_url, status) VALUES (?, ?, ?)", 
                     (content[:500], url, status))

def generate_marketing_post(image_path):
    """Vision-based marketing post generation in HEBREW."""
    try:
        with open(image_path, "rb") as img:
            base64_image = base64.b64encode(img.read()).decode('utf-8')
        
        prompt = """
        You are a social media manager for a car garage (VAG specialists).
        Write a professional, catchy marketing post in HEBREW based on this image.
        Include: What's being fixed, why expertise matters, and a call to action.
        Use emojis.
        """
        
        completion = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            model="llama-3.2-11b-vision-preview",
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Vision Error: {e}"

def send_telegram_lead(text, analysis, post_url, is_debug=False):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    header = "🎯 *НОВЫЙ КЛИЕНТ\\!*" if not is_debug else "🧪 *DEBUG LEAD FOUND\\!*"
    
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"accept_{post_url[-15:]}"),
         InlineKeyboardButton("❌ Игнорировать", callback_data="ignore")],
        [InlineKeyboardButton("🔗 Открыть оригинал", url=post_url)]
    ]
    
    message = f"{header}\n\n*Пост:* {text}\\.\\.\\.\n\n*Анализ:* {analysis}\n"
    payload = {
        "chat_id": chat_id, "text": message, "parse_mode": "MarkdownV2",
        "reply_markup": InlineKeyboardMarkup(keyboard).to_dict()
    }
    return requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload)