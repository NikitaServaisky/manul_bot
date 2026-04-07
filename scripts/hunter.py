import time
import random
import logging
from datetime import datetime
from core.utils import load_list
from services.scrapper_services import get_facebook_posts
from services.lead_service import check_and_save_lead

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_hunt():
    """Executes a single hunting cycle: fetch, analyze, and save leads."""
    try:
        groups = load_list("config/groups.txt")
        if not groups:
            logging.error("No groups found in config/groups.txt")
            return

        # Increase sample size slightly for better coverage
        sample_size = min(5, len(groups))
        selected = random.sample(groups, sample_size)
        logging.info(f"🚀 Starting hunt in {sample_size} groups: {selected}")

        posts = get_facebook_posts(selected)
        
        found_count = 0
        for post in posts:
            text = post.get("text")
            url = post.get("url", "No URL")

            if text and url != "No URL":
                if check_and_save_lead(text, url):
                    logging.info(f"🎯 Lead Captured: {url}")
                    found_count += 1
        
        logging.info(f"🏁 Cycle finished. Found {found_count} new potential leads.")
        
    except Exception as e:
        logging.error(f"❌ Critical error during hunting cycle: {e}")

def is_work_time(now):
    """Checks if the current time falls within Sunday 08:00 to Friday 13:00."""
    weekday = now.weekday() # 0=Mon, 6=Sun
    hour = now.hour

    # Sunday: After 08:00
    if weekday == 6 and hour >= 8: return True
    # Monday - Thursday: All day
    if 0 <= weekday <= 3: return True
    # Friday: Before 13:00
    if weekday == 4 and hour < 13: return True
    
    return False

def start_service():
    logging.info("🤖 Manul Hunter Service is live and monitoring schedule.")

    while True:
        now = datetime.now()
        
        if is_work_time(now):
            run_hunt()
            # Reduced sleep to 45 minutes for faster response to customers
            wait_time = 2700 
            logging.info(f"😴 Sleeping for {wait_time//60} minutes...")
        else:
            logging.info(f"⏳ Weekend mode (Current: {now.strftime('%A %H:%M')}). Waiting...")
            wait_time = 3600 # Check every hour during weekend

        time.sleep(wait_time)

if __name__ == "__main__":
    start_service()