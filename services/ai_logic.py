import logging
from core.ai_clients import groq, gemini
from PIL import Image

def analyze_mechanic_work(image_path, instruction=None, current_text=None):
    """
    Analyzes car repair images using the LATEST Gemini 2.0 SDK.
    """
    base_prompt = """
    אתה כותב פוסטים לדף הפייסבוק של 'Manul Garage'. 
    הסגנון שלך: קצר, קולע, גברי ומקצועי. בלי "חלק בלתי נפרד מחייכם" ובלי חפירות מיותרות.
    
    כללים:
    1. תתמקד בתיקון הספציפי שבוצע (אם רשום לך 'החלפת צינורות בלם', תכתוב על זה!).
    2. תן כבוד לרכב הספציפי שבו אתה מטפל (זהה אותו מהתמונה או מהטקסט).
    3. תסיים תמיד ב: 📍 אליהו נאווי 6, באר שבע | 📞 054-688-2479.
    4. תוסיף האשטאגים רלוונטיים בסוף.
    
    אם אתה לא רואה את התמונה, תסתמך אך ורק על מה שהמוסכניק כתב לך.
    """

    if instruction and current_text:
        full_prompt = f"{base_prompt}\n\nCURRENT POST: {current_text}\nINSTRUCTION: {instruction}"
    elif instruction:
        full_prompt = f"{base_prompt}\n\nMECHANIC NOTE: {instruction}"
    else:
        full_prompt = base_prompt

    try:
        # Using the NEW SDK syntax for Gemini 2.0
        # gemini is the Client we imported from core.ai_clients
        img = Image.open(image_path)
        
        response = gemini.models.generate_content(
            model="gemini-2.0-flash",
            contents=[full_prompt, img]
        )
        
        if response.text:
            return response.text

    except Exception as e:
        logging.warning(f"Gemini failed: {e}. Falling back to Groq...")

    # Final Fallback to Groq (Text Only)
    try:
        fallback_prompt = f"{base_prompt}\n(Vision failed. Context): {instruction if instruction else 'Car repair'}"
        response = groq.chat.completions.create(
            messages=[{"role": "user", "content": fallback_prompt}],
            model="llama-3.3-70b-versatile"
        )
        return response.choices[0].message.content + "\n\n(Note: Image analysis unavailable)"
    except Exception as e:
        return f"Error: All models failed. {e}"

def analyze_lead_relevance(post_text):
    """
    Analyzes Facebook posts for potential leads.
    Returns 'YES' or 'NO'.
    """
    prompt = f"""
    Analyze the following Facebook post and determine if the person is looking for
    car repairs, mechanic services, or has a vehicle problem.
    Reply with ONLY 'YES' or 'NO'.

    Post: {post_text}
    """
    try:
        # Using groq.chat (with a dot, not a slash)
        response = groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        return response.choices[0].message.content.strip().upper()
    except Exception as e:
        logging.error(f"Lead analysis failed: {e}")
        return "NO"