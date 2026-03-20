import os
import random
import requests
import re
from apify_client import ApifyClient
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize API clients
apify_client = ApifyClient(os.getenv("APIFY_TOKEN"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Helper Functions ---


def load_list_from_file(file_path):
    """Generic loader for keywords or groups."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def escape_markdown(text):
    """Escapes ALL special characters for Telegram MarkdownV2."""
    if not text:
        return ""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", str(text))


def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {"chat_id": chat_id, "text": message, "parse_mode": "MarkdownV2"}

    try:
        response = requests.post(url, json=payload)
        result = response.json()
        if not result.get("ok"):
            payload.pop("parse_mode")
            requests.post(url, json=payload)
            print(
                f"⚠️ Sent as plain text due to Markdown error: {result.get('description')}"
            )
        return result
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


# --- Core Logic ---


def analyze_post_with_ai(post_text, keywords):
    """Hybrid analysis using keywords from file + AI."""
    found_keywords = [
        kw for kw in keywords if re.search(rf"\b{kw}\b", post_text, re.IGNORECASE)
    ]

    if not found_keywords:
        return "Relevant: No\nReason: No matching keywords found."

    prompt = f"""
    Identify if this person needs mechanical help or has a car problem.
    POST: "{post_text}"
    
    Return only:
    Relevant: [Yes/No]
    Reason: [Short English explanation]
    """
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"


def fetch_and_filter_leads():
    """Main workflow."""
    groups = load_list_from_file("groups.txt")
    keywords = load_list_from_file("keywords.txt")

    if not groups or not keywords:
        print("Error: Missing groups.txt or keywords.txt")
        return

    # Selecting groups to scan
    selected_groups = random.sample(groups, min(3, len(groups)))
    print(f"🚀 Hunting in: {selected_groups}")

    run_input = {
        "startUrls": [{"url": url} for url in selected_groups],
        "resultsLimit": 5,
    }

    try:
        run = apify_client.actor("apify/facebook-posts-scraper").call(
            run_input=run_input
        )

        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            text = item.get("text")
            post_url = item.get("url", "No URL")

            if text:
                analysis = analyze_post_with_ai(text, keywords)

                if "Yes" in analysis:
                    # שימוש במשתנים הנכונים והזחה תקינה
                    clean_text = escape_markdown(text[:300])
                    clean_analysis = escape_markdown(analysis)
                    clean_url = escape_markdown(post_url)

                    msg = (
                        f"🎯 *NEW LEAD FOUND\\!*"
                        f"\n\n*Post:* {clean_text}\.\.\."
                        f"\n\n*Analysis:*\n{clean_analysis}"
                        f"\n\n[Link to Post]({clean_url})"
                    )

                    send_telegram_message(msg)
                    print(f"✅ Lead sent to Telegram from: {post_url}")

    except Exception as e:
        print(f"Scraper Error: {e}")


if __name__ == "__main__":
    fetch_and_filter_leads()
