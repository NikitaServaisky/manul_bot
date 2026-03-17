import os
import base64
import requests
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_and_post(image_path):
    if not os.path.exists(image_path):
        return f"Error: The file {image_path} was not found!"

    base64_image = encode_image(image_path)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # שלב 1: ניתוח התמונה
    data = {
        "model":"llama3.2-11b-vision-previwe" ,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What car part is this and what is wrong with it?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    res_json = response.json()

    if 'choices' not in res_json:
        print("--- API ERROR IN VISION STAGE ---")
        print(json.dumps(res_json, indent=2))
        return "Failed at Vision stage."

    analysis = res_json['choices'][0]['message']['content']
    print(f"Technical Analysis: {analysis}")

    # שלב 2: כתיבת הפוסט
    post_data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": f"Write a funny Facebook post in Hebrew for 'Manul Garage' about this: {analysis}"}
        ]
    }
    
    post_res = requests.post(url, headers=headers, json=post_data).json()
    return post_res['choices'][0]['message']['content']

try:
    final_post = analyze_and_post("job.jpg")
    print("\n--- RESULT ---")
    print(final_post)
except Exception as e:
    print(f"General Error: {e}")
