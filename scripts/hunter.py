import time
import random
import logging
from datetime import datetime
from core.utils import load_list
from services.scrapper_services import get_facebook_posts
from services.lead_service import check_and_save_lead

# 1. Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def run_hunt():
    """Executes a single hunting cycle: fetch, analyze, and save leads."""
    groups = load_list("config/groups.txt")
    if not groups:
        logging.error("No groups found in config/groups.txt")
        return

    # Select 3 random groups to scan
    selected = random.sample(groups, min(3, len(groups)))
    logging.info(f"🚀 Starting hunt in: {selected}")

    try:
        posts = get_facebook_posts(selected)
        for post in posts:
            text = post.get("text")
            url = post.get("url", "No URL")

            if text and url != "No URL":
                if check_and_save_lead(text, url):
                    logging.info(f"🎯 Lead Captured: {url}")
    except Exception as e:
        logging.error(f"Error during hunting cycle: {e}")


def start_service():
    """Main loop that manages the Sunday-Friday schedule."""
    logging.info("🤖 Manul Hunter Service is live.")

    while True:
        now = datetime.now()
        weekday = now.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun
        hour = now.hour

        # Schedule Logic: Start Sunday 08:00, End Friday 13:00
        is_sunday_start = weekday == 6 and hour >= 8
        is_standard_workday = 0 <= weekday <= 3  # Mon-Thu
        is_friday_before_cutoff = weekday == 4 and hour < 13

        if is_sunday_start or is_standard_workday or is_friday_before_cutoff:
            run_hunt()
            logging.info("😴 Cycle complete. Sleeping for 2 hours...")
            time.sleep(7200)
        else:
            current_time = now.strftime("%A %H:%M")
            logging.info(
                f"⏳ Weekend mode active (Current: {current_time}). Waiting..."
            )
            time.sleep(3600)  # Check again in 1 hour


if __name__ == "__main__":
    start_service()
