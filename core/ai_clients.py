import os
from google import genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))