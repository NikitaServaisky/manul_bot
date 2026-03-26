from core.utils import load_list, escape_md
from core.services import analyze_with_ai, send_telegram_lead, save_lead
from dotenv import load_dotenv

load_dotenv()

MOCK_POSTS = [
    {"text": "היי חברים, יש לי אאודי A3 שנת 2018 ויש רעש מוזר מהגיר DSG.", "url": "https://fb.com/mock1"},
    {"text": "У меня проблема с коробкой передач в Шкоде. Нужен механик.", "url": "https://fb.com/mock2"}
]

def run_debug_hunter():
    print("🚀 Starting Debug Hunt...")
    keywords = load_list("keywords.txt")
    
    for post in MOCK_POSTS:
        text, url = post['text'], post['url']
        analysis = analyze_with_ai(text, keywords, lang="Russian")
        
        if "Yes" in analysis:
            # Note: Using debug status and debug DB name
            save_lead(text, url, db_name="debug_leads.db", status="debug")
            send_telegram_lead(escape_md(text[:200]), escape_md(analysis), url, is_debug=True)
            print(f"✅ Debug Lead Processed: {url}")

if __name__ == "__main__":
    run_debug_hunter()