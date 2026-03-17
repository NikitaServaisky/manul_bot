import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("רשימת מודלים זמינים")
print("-" * 30)

# loop run on the all models my key is avaible
for model in client.models.list():
    print(f"Name: {model.name}")
    print(f"Supported Methods: {model.supported_generation_methods}")
    print("-" * 10)