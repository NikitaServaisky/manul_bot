import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# טעינת המפתח
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("--- מודלים זמינים בחשבון שלך ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"ID: {m.name} | Display Name: {m.display_name}")
except Exception as e:
    print(f"Error: {e}")