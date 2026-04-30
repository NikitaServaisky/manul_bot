from core.apify_client import apify


def get_facebook_posts(urls, limits=5):
    """
    Executes the Apify actor and returns a generator of raw items.
    Using iterate_items() to handle data streams efficiently.
    """
    try:
        # Triggering the actor with the URLs and limits
        run = apify.actor("apify/facebook-posts-scraper").call(
            run_inputs={
                "startUrls": [{"url": u} for u in urls],
                "resultsLimit": limits,
                "viewAssets": False,
                # Set proxies it's a critical for successfuly scruper
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                    "apifyProxyCountryCode": "IL"
                },
                "useStealth": True,
                "minDelaySecs": 5,
                "maxDelaySecs": 15
            }
        )

        # Returns a generator, perfect for the loop in your main hunt cycle
        return apify.dataset(run["defaultDatasetId"]).iterate_items()

    except Exception as e:
        # Minimalist error handling to keep the flow in main.py
        print(f"Scruper error: {e}")
        return []
