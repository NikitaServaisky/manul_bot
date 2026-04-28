import os
from google.genai import Client
from dotenv import load_dotenv

# load key
load_dotenv()
google_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# check v1
client = Client(api_key=google_key, http_options={"api_version": "v1"})

print("🔍 Checking available models for your API key...")
try:
    models = client.models.list()
    for m in models:
        # we find names statr with: /models
        print(f"✅ Found: {m.name}")
except Exception as e:
    print(f"❌ Error: {e}")
