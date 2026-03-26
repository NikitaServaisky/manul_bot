import os
import sqlite3
import urllib.parse
from pathlib import Path
from PIL import Image
from google import genai
from groq import Groq
import logging

# Initialize Clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def init_all_dbs():
    """Initializes all necessary tables with CRM-ready fields."""
    Path("uploads").mkdir(exist_ok=True)

    with sqlite3.connect("manul_leads.db") as conn:
        # Users table for authorization
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                role TEXT DEFAULT 'mechanic',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Leads table for Facebook scraping
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
        
        # Marketing table for vision-based posts
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
        
        # Auto-update timestamp trigger
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_lead_timestamp 
            AFTER UPDATE ON leads
            BEGIN
                UPDATE leads SET updated_at = CURRENT_TIMESTAMP WHERE id = old.id;
            END;
        """)
    print("✅ Database initialized and CRM-ready.")

def is_user_authorized(user_id):
    """Check if user exists in the system and is active."""
    try:
        with sqlite3.connect("manul_leads.db") as conn:
            cursor = conn.execute("SELECT is_active FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result is not None and result[0] == 1
    except Exception as e:
        logging.error(f"Auth Check Error: {e}")
        return False

def generate_marketing_post(image_path):
    """Vision-based marketing post generation in HEBREW using Gemini."""
    try:
        img = Image.open(image_path)
        prompt = """
        You are a social media manager for a car garage (VAG specialists).
        Write a professional, catchy marketing post in HEBREW based on this image.
        Include: What's being fixed, why expertise matters, and a call to action.
        Use emojis.
        """
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        return response.text
    except Exception as e:
        logging.error(f"Gemini Vision Error: {e}")
        return None

def create_facebook_deep_link(post_text):
    """Generate a Facebook sharing link with the post content."""
    page_id = os.getenv("FB_PAGE_ID", "MANUL_GARAGE")
    encoded_text = urllib.parse.quote(post_text)
    return f"https://www.facebook.com/sharer/sharer.php?u=https://facebook.com/{page_id}&quote={encoded_text}"