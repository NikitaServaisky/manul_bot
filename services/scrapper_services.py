import logging
from core.apify_client import apify
from core.facebook_cookies import load_facebook_cookies

# Logger setup for this file
logger = logging.getLogger(__name__)


# Getting facebook posts
def get_facebook_posts(urls, limits=5):
    """
    Executes the Apify actor and returns a generator of raw items.
    Using iterate_items() to handle data streams efficiently.
    """
    try:
        # Call to cookies function
        cookies = load_facebook_cookies()
        # Triggering the actor with the URLs and limits
        run = apify.actor("apify/facebook-groups-scraper").call(
            run_input={
                "startUrls": [{"url": u} for u in urls],
                "resultsLimit": limits,
                "cookieSandbox": cookies,
                "proxyConfiguration": {"useApifyProxy": False},
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64; rv:150.0) Gecko/20100101 Firefox/150.0",
                "useStealth": True,
                "minDelaySecs": 10,
                "maxDelaySecs": 25,
            }
        )

        # Returns a generator, perfect for the loop in your main hunt cycle
        return apify.dataset(run["defaultDatasetId"]).iterate_items()

    except Exception as e:
        # Minimalist error handling to keep the flow in main.py
        logger.exception(f"❌ Scrapper error: {e}")
        return []
