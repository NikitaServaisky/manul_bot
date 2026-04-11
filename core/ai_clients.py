import os

# Try a more explicit import path
try:
    from google.genai import Client
except ImportError:
    from genai import Client

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

google_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
gemini = Client(api_key=google_key, http_options={'api_version': 'v1'}) if google_key else None

groq_key = os.getenv("GROQ_API_KEY")
groq = Groq(api_key=groq_key) if groq_key else None
