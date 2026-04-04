from core.apify_client import apify


def get_facebook_posts(urls, limits=5):
    """Executes the Apify actor and returns raw items."""
    run = apify.actor("apify/facebook-posts-scraper").call(
        run_input={"startUrls": [{"url": u} for u in urls], "resultsLimit": limit}
    )
    return apify.dataset(run["defaultDatasetId"]).iterate_items()
