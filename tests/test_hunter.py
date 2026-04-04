import logging
from services.lead_service import check_and_save_lead
from core.database import get_db

# Configure logging for test output
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Mock data for testing (VAG related and non-related)
MOCK_POSTS = [
    {
        "text": "היי חברים, יש לי אאודי A3 שנת 2018 ויש רעש מוזר מהגיר DSG. מחפש מוסך מומחה.",
        "url": "https://fb.com/test_vag_1",
    },
    {
        "text": "У меня проблема с коробкой передач в Шкоде Октавия. Нужен механик VAG.",
        "url": "https://fb.com/test_vag_2",
    },
    {
        "text": "Looking for a good pizza place in Tel Aviv, any recommendations?",
        "url": "https://fb.com/test_pizza",
    },
]


def run_test_hunt():
    """Tests the lead hunting logic using mock data."""
    print("🚀 Starting Modular Debug Hunt...")

    for post in MOCK_POSTS:
        text, url = post["text"], post["url"]
        print(f"\n🔍 Testing Post: {url}")

        # This calls: Lead Service -> AI Logic -> Groq -> DB
        is_saved = check_and_save_lead(text, url)

        if is_saved:
            print(f"✅ SUCCESS: Lead was identified as VAG and saved.")
        else:
            print(f"⏭️ SKIPPED: Lead was either duplicate or not relevant.")


def verify_db_results():
    """Quickly check the database to see if the test leads are there."""
    print("\n📊 Checking Database Content:")
    with get_db() as conn:
        rows = conn.execute(
            "SELECT post_url FROM leads ORDER BY id DESC LIMIT 5"
        ).fetchall()
        for row in rows:
            print(f"Stored URL: {row['post_url']}")


if __name__ == "__main__":
    run_test_hunt()
    verify_db_results()
