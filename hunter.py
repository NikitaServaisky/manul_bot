import os
import random
import requests
from apify_client import ApifyClient
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize API clients
apify_client = ApifyClient(os.getenv("APIFY_TOKEN"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def send_telegram_message(message):
    """Sends a notification to Nikita's Telegram bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def load_groups_from_file(file_path="groups.txt"):
    """Reads the FB group URLs from groups.txt."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def analyze_post_with_ai(post_text):
    """Asks Llama 3 if this post is a relevant VAG lead."""
    prompt = f"""
    Analyze if this Facebook post is a potential car repair customer (VAG Group focus: VW, Audi, Skoda, Seat).
    Post: "{post_text}"
    Return: 'Relevant: Yes' or 'Relevant: No' and a short reason.
    """
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

def fetch_and_filter_leads():
    """Main function: Scrape, Analyze, and Notify."""
    all_groups = load_groups_from_file()
    if not all_groups:
        print("No groups found in groups.txt")
        return

    # Randomly select 3 groups
    selected_groups = random.sample(all_groups, min(3, len(all_groups)))
    print(f"Targeting groups: {selected_groups}")

    run_input = {
        "startUrls": [{"url": url} for url in selected_groups],
        "resultsLimit": 5
    }

    try:
        # Start Apify Scraper
        run = apify_client.actor("apify/facebook-posts-scraper").call(run_input=run_input)
        
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            text = item.get("text")
            post_url = item.get("url")
            
            if text:
                analysis = analyze_post_with_ai(text)
                
                # If AI says it's a hit, send to Telegram
                if "Relevant: Yes" in analysis:
                    lead_msg = f"🔥 *HOT LEAD FOUND!*\n\n*URL:* {post_url}\n\n*Analysis:* {analysis}"
                    print(f"Sending lead to Telegram...")
                    send_telegram_message(lead_msg)
                else:
                    print(f"Skipping non-relevant post.")
                    
    except Exception as e:
        print(f"Scraper Error: {e}")

if __name__ == "__main__":
    fetch_and_filter_leads()