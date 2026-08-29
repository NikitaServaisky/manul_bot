import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# Set the client
apify = ApifyClient(os.getenv("APIFY_TOKEN"))
