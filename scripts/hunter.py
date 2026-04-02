import random
import logging
from core.utils import load_list
from services.scrapper_services import get_facebook_posts
from services.lead_service import check_and_save_lead

# Configure logging to display only the message
logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_hunt():
    """Main execution function for the lead hunting process."""
    
    # 1. Prepare input: Load target groups from file
    groups = load_list("groups.txt")
    if not groups: 
        logging.error("No groups found in groups.txt")
        return
        
    # Select a random sample of groups to avoid repetitive scanning
    selected = random.sample(groups, min(3, len(groups)))

    # 2. Fetch raw data: Get posts via the Scrapper Service (Apify)
    logging.info(f"🚀 Starting hunt in: {selected}")
    posts = get_facebook_posts(selected)

    # 3. Process data: Filter and save relevant leads via Lead Service
    for post in posts:
        text = post.get("text")
        url = post.get("url", "No URL")
        
        if text and url != "No URL":
            # check_and_save_lead handles deduplication, AI analysis, and DB storage
            if check_and_save_lead(text, url):
                logging.info(f"🎯 Lead Captured: {url}")

if __name__ == "__main__":
    run_hunt()