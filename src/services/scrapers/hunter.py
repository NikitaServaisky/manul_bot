import time
import random
import logging
from datetime import datetime
from src.utils.helpers import load_list
from src.services.scrapers.scraper import get_facebook_posts
from src.services.lead_service import check_and_save_lead

# Logger Setup for this file
logger = logging.getLogger(__name__)


def run_hunt():
    """Executes a single hunting cycle: fetch, analyze, and save leads."""
    try:
        groups = load_list("config/groups.txt")
        if not groups:
            logger.error("No groups found in config/groups.txt")
            return

        # Increase sample size slightly for better coverage
        sample_size = min(5, len(groups))
        selected = random.sample(groups, sample_size)
        logger.info(f"🚀 Starting hunt in {sample_size} groups: {selected}")

        posts = get_facebook_posts(selected)

        found_count = 0
        for post in posts:
            text = post.get("text")
            url = post.get("url", "No URL")

            if text and url != "No URL":
                if check_and_save_lead(text, url):
                    logger.info(f"🎯 Lead Captured: {url}")
                    found_count += 1
                    time.sleep(random.uniform(1.0, 3.0))

        logger.info(f"🏁 Cycle finished. Found {found_count} new potential leads.")

    except Exception as e:
        logger.exception(f"❌ Critical error during hunting cycle: {e}")


def is_work_time(now):
    """Checks if the current time falls within Sunday 08:00 to Friday 13:00."""
    weekday = now.weekday()  # 0=Mon, 6=Sun
    hour = now.hour

    # Sunday: After 08:00
    if weekday == 6 and hour >= 8:
        return True
    # Monday - Thursday: All day
    if 0 <= weekday <= 3:
        return True
    # Friday: Before 13:00
    if weekday == 4 and hour < 13:
        return True

    return False


def start_service():
    logger.info("🤖 Manul Hunter Service is live and monitoring schedule.")

    while True:
        now = datetime.now()

        if is_work_time(now):
            run_hunt()
            # Reduced sleep to 45 minutes for faster response to customers
            wait_minutes = random.randint(30, 60)
            wait_time = wait_minutes * 60
            logger.info(f"😴 Next hunt in {wait_minutes} minutes (Randomized).")
        else:
            logger.info(f"⏳ Weekend mode. Waiting...")
            wait_time = 3600  # Check every hour during weekend

        time.sleep(wait_time)


if __name__ == "__main__":
    start_service()
