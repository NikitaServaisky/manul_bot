# Internal imports
import os
import requests
import json

# External imports
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("Error: No GROQ_API_KEY found in .env")
else:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Say 'Manul Garage is Live' in Hebrew"}],
         "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        if 'choices' in result:
            content = result['choices'][0]['message']['content']
            print("-" * 20)
            print("Success! Groq/Mistral is working.")
            print("Response: " + content)
            print("-" * 20)
        else:
            print("API Error Response:")
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print("Network or Code Error: " + str(e))
