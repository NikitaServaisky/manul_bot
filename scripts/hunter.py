import os
import random
import logging
from apify_client import ApifyClient
from core.utils import load_list, escape_md
from core.services import analyze_with_ai, send_telegram_lead, save_lead
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
client = ApifyClient(os.getenv("APIFY_TOKEN"))

def fetch_and_filter_leads():
    groups = load_list("groups.txt")
    keywords = load_list("keywords.txt")
    
    selected_groups = random.sample(groups, min(3, len(groups)))
    logging.info(f"🚀 Real Hunt Started: {selected_groups}")

    try:
        run = client.actor("apify/facebook-posts-scraper").call(run_input={"startUrls": [{"url": u} for u in selected_groups], "resultsLimit": 5})

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            text, url = item.get("text"), item.get("url", "No URL")

            if text:
                analysis = analyze_with_ai(text, keywords, lang="Russian")
                if "Yes" in analysis:
                    save_lead(text, url)
                    send_telegram_lead(escape_md(text[:200]), escape_md(analysis), url)
                    logging.info(f"✅ Lead sent: {url}")

    except Exception as e:
        logging.error(f"Hunter Error: {e}")

if __name__ == "__main__":
    fetch_and_filter_leads()