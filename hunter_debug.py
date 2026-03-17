import os
import requests
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq for AI analysis
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Fake data for testing (3 posts: 1 VAG, 1 General, 1 Junk)
MOCK_POSTS = [
    {
        "text": "היי חברים, יש לי אאודי A3 שנת 2018 ויש רעש מוזר מהגיר DSG. מישהו מכיר מוסך מומחה באזור הדרום?",
        "url": "https://facebook.com/groups/fake_post_1"
    },
    {
        "text": "למכירה שולחן סלון בבאר שבע, במצב מצוין.",
        "url": "https://facebook.com/groups/fake_post_2"
    },
    {
        "text": "צריך המלצה למוסך לטיפול 15,000 לסיאט לאון שלי, מעדיף מישהו שמבין ב-VAG.",
        "url": "https://facebook.com/groups/fake_post_3"
    }
]

def send_telegram_message(message):
    """Sends notification to Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Telegram Error: {e}")

def analyze_post_with_ai(post_text):
    """Aggressive Few-Shot Prompting to force VAG detection."""
    prompt = f"""
    You are a specialized lead filter for a car garage.
    
    TARGET BRANDS: Audi, VW, Volkswagen, Seat, Skoda.
    TARGET TOPICS: Repairs, DSG, TSI, Mechanic recommendations, noises, engine light.

    EXAMPLES:
    1. "Looking for Audi mechanic" -> Relevant: Yes
    2. "My Skoda has a DSG noise" -> Relevant: Yes
    3. "Selling my VW Golf" -> Relevant: No (It's a sale)
    4. "Recommendation for Seat garage" -> Relevant: Yes
    5. "Looking for a table" -> Relevant: No

    USER POST: "{post_text}"

    Does this person need a garage or repair for a VAG car?
    Answer ONLY in this format:
    Relevant: [Yes/No]
    Reason: [Why]
    """
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional sales lead identifier. Be decisive."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
            temperature=0.1, # Extremely focused
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

def run_debug_test():
    """Main test loop using mock data instead of Apify."""
    print("🚀 Starting Debug Test with Mock Data...")
    
    for post in MOCK_POSTS:
        print(f"\nChecking post: {post['text'][:40]}...")
        
        # Analyze with AI (this still uses Groq tokens, but they are very cheap/free)
        analysis = analyze_post_with_ai(post['text'])
        
        if "Relevant: Yes" in analysis:
            print("✅ AI marked as RELEVANT. Sending to Telegram...")
            msg = f"🧪 *DEBUG LEAD FOUND!*\n\n*Post:* {post['text']}\n\n*Analysis:* {analysis}\n\n*URL:* {post['url']}"
            send_telegram_message(msg)
        else:
            print("❌ AI marked as NOT RELEVANT.")

if __name__ == "__main__":
    run_debug_test()