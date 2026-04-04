import os
import logging
from core.ai_clients import groq, gemini
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")


def test_groq_connection():
    """Tests if Groq (Llama) is reachable and responding."""
    print("\n☁️ Testing Groq Connection...")
    try:
        res = groq.chat.completions.create(
            messages=[{"role": "user", "content": "Say 'Groq is Online'"}],
            model="llama-3.3-70b-versatile",
        )
        content = res.choices[0].message.content
        print(f"✅ Groq Response: {content}")
        return True
    except Exception as e:
        print(f"❌ Groq Error: {e}")
        return False


def test_gemini_connection():
    """Tests if Gemini is reachable and responding."""
    print("\n☁️ Testing Gemini Connection...")
    try:
        # Simple text generation test
        response = gemini.models.generate_content(
            model="gemini-2.0-flash", contents=["Say 'Gemini is Online'"]
        )
        print(f"✅ Gemini Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting AI Connectivity Tests...")

    groq_ok = test_groq_connection()
    gemini_ok = test_gemini_connection()

    print("\n" + "=" * 30)
    if groq_ok and gemini_ok:
        print("🎉 All AI systems are GO!")
    else:
        print("⚠️ Some systems failed. Check your .env file and API quotas.")
    print("=" * 30)
