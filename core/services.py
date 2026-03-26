import os
import sqlite3
import urllib.parse
import logging
from pathlib import Path
from PIL import Image
from google import genai
from dotenv import load_dotenv

load_dotenv()

# אתחול הלקוח - פעם אחת לכל המערכת
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_db_connection():
    """פונקציית עזר לחיבור למסד הנתונים"""
    conn = sqlite3.connect("manul_leads.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_all_dbs():
    """מאתחל את כל הטבלאות הנדרשות - כולל ה-Seen Leads"""
    Path("uploads").mkdir(exist_ok=True)

    with get_db_connection() as conn:
        # משתמשים (מכונאים)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                role TEXT DEFAULT 'mechanic',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # לידים שנמצאו בסריקה
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                post_content TEXT, 
                post_url TEXT UNIQUE, 
                status TEXT DEFAULT 'new',
                assigned_to INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(assigned_to) REFERENCES users(user_id)
            )
        """)
        
        # טבלת היסטוריית סריקה (מונעת כפילויות של ה-Hunter)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_leads (
                url TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # פוסטים שיווקיים (Vision)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS marketing_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                image_path TEXT,
                generated_content TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
    print("✅ All databases (CRM + Hunter) initialized.")

# --- לוגיקת AI מרכזית (Middleware) ---

def _call_gemini(prompt, image_path=None):
    """המעטפת המרכזית לדיבור עם Gemini"""
    try:
        contents = [prompt]
        if image_path:
            img = Image.open(image_path)
            contents.append(img)
            
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=contents
        )
        return response.text
    except Exception as e:
        logging.error(f"Gemini AI Error: {e}")
        return None

# --- פונקציות שירות (API למשתמשים חיצוניים) ---

def is_user_authorized(user_id):
    """בודק אם המשתמש מורשה ופעיל"""
    try:
        with get_db_connection() as conn:
            res = conn.execute("SELECT is_active FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return res is not None and res['is_active'] == 1
    except Exception as e:
        logging.error(f"Auth Error: {e}")
        return False

def generate_marketing_post(image_path, instruction=None):
    """יצירת פוסט שיווקי - משתמש במעטפת המרכזית"""
    base_prompt = "You are a social media manager for 'Manul Garage'. Write a catchy marketing post in HEBREW."
    if instruction:
        prompt = f"{base_prompt}\nUpdate the draft based on: {instruction}"
    else:
        prompt = f"{base_prompt}\nExplain the repair and use emojis."
        
    return _call_gemini(prompt, image_path)

def analyze_lead_content(text):
    """ניתוח טקסט של פוסט מפייסבוק - האם רלוונטי לתיקון?"""
    prompt = f"Analyze this post. Is it someone looking for a car mechanic (VAG)? Answer 'Yes' or 'No':\n{text}"
    result = _call_gemini(prompt)
    return result and "yes" in result.lower()

def create_facebook_deep_link(post_text):
    encoded_text = urllib.parse.quote(post_text)
    return f"https://www.facebook.com/sharer/sharer.php?u=https://facebook.com/MANUL_GARAGE&quote={encoded_text}"