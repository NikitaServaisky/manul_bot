import logging
from core.ai_clients import genai, groq
from PIL import Image

def analyze_mechanic_work(image_path, instruction=None, current_text=None):
    """Deep vision analysis using Gemini"""
    img = Image.open(image_path)
    base_prompt = """
    אתה מנהל שיווק של מוסך 'Manul Garage'. 
    תפקידך לכתוב פוסט שיווקי על התיקון שבתמונה.
    דגשים:
    1. שפה: עברית בלבד.
    2. סגנון: מקצועי, חברי, של מוסכים (סלנג ישראלי).
    3. גיוון: אל תשתמש באותם משפטים בכל פעם. תהיה יצירתי. פעם תתחיל בבעיה, פעם בתוצאה, פעם בחוויה של הלקוח.
    4. אל תשתמש תמיד במשפט "החזרנו את הכלה". תשתמש בו רק אם זה באמת מתאים לרכב מיוחד.
    5. בנוסף תוסיף את פרטי ההתקשרות שלנו: כתובת אליהו נאווי 6 באר שבע (מתחם סולל בונה לשעבר), טלפון: 054-688-2479
    """

    if instruction and current_text:
        full_prompt = f"{base_prompt}\n\nThis is the current version:\n{current_text}\n\nUSER INSTRUCTION FOR EDIT: {instruction}\nRewrite the post according to the instruction, keeping the same style and context."
    else:
        full_prompt = base_prompt
    
    # Try Gemini 2.0 flash
    try:
        img = Image.open(image_path)
        response = genai.models.generate_content(model="gemini-2.0-flash", contents=[full_prompt, img])
        return response.text
    except Exception as e:
        logging.warning(f"Gemini 2.0 failed: {e}. Trying Gemini 1.5...")

    # Try Gemini 1.5 flash (Diffrent quota)
    try:
        response = genai.models.generate_content(model="gemini-1.5-flash", contents=[full_prompt, img])
        return response.text
    except Exception as e:
        logging.warning(f"Gemini 1.5 faild: {e}. Falling back to Groq (Text only)...")

    # Final Fallback: Groq (llama 3) - No vision, just text generation based on prompt
    try:
        response = groq.chat.completions.create(
            messages=[{"role": "user", "content": full_prompt}],
            model="llama-3.3-70b-versatile"
        )
        return response.choices[0].message.content + "\n\n(Note: Image analysis unavailable, generated based on prompt)"
    except Exception as e:
        return f"Error: All AI models are currently unavilable. {e}"

def analyze_lead_relevance(post_text):
    """Analyzes a Facebook post to see if it's apotential custumer."""
    
    prompt = F"""
    Analyze the following Facebook post and determine if the person is looking for
    car repairs, mechanic services, of has v vihicle problem.
    Reply with ONLY 'YES' or 'NO'.

    Post: {post_text}
    """

    try:
        response = groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        return response.choices[0].message.content.strip().upper()
    except Exception as e:
        logging.error(f"Lead analysis failed {e}")
        return "NO"