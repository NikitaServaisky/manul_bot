import logging
from utils.image_processor import process_image_for_api
from services.llm_clients import call_gemini_20_flash, call_gemini_15_flash, call_groq_llama

def analyze_mechanic_work(image_path, instruction=None, current_text=None):
    """
    Main Router function - manages the post generation workflow and model failover.
    """
    
    # 1. Build the prompt (Business logic remains here for clarity)
    base_prompt = """
    אתה כותב פוסטים לדף הפייסבוק של 'Manul Garage'. 
    הסגנון שלך: קצר, קולע, גברי ומקצועי. בלי חפירות.
    
    כללים:
    1. תתמקד בתיקון הספציפי שבוצע!
    2. זהה את הרכב מהתמונה או מהטקסט.
    3. תסיים בכתובת וטלפון: 📍 אליהו נאווי 6, באר שבע | 📞 054-688-2479.
    4. האשטאגים רלוונטיים בסוף.
    """

    if instruction and current_text:
        full_prompt = f"{base_prompt}\nTask: Edit an existing post.\nOriginal Post: {current_text}\nRequested Update: {instruction}"
    elif instruction:
        full_prompt = f"{base_prompt}\nNew Task: Create a post based on the following information:\n{instruction}"
    else:
        full_prompt = base_prompt

    # 2. Process image into binary data (using the new utility)
    image_data, mime_type = None, None
    if image_path:
        image_data, mime_type = process_image_for_api(image_path)

    # 3. Chain of Responsibility (Model Failover)
    
    # Attempt 1: Gemini 2.0 Flash (Primary Multimodal Model)
    logging.info("Attempting Gemini 2.0 Flash...")
    result = call_gemini_20_flash(full_prompt, image_data, mime_type)
    if result:
        return result

    # Attempt 2: Gemini 1.5 Flash (Fallback for Quota/API issues)
    logging.info("Gemini 2.0 failed or quota hit. Trying Gemini 1.5 Flash...")
    result = call_gemini_15_flash(full_prompt, image_data, mime_type)
    if result:
        return result

    # Attempt 3: Groq / Llama 3.3 (Final Safety Net - Text Only)
    logging.info("Gemini family failed. Falling back to Groq (Text Only)...")
    # Add a note to prevent hallucinations since vision is unavailable
    fallback_prompt = f"{full_prompt}\n(Note: Image analysis is unavailable, rely only on the provided text)."
    result = call_groq_llama(fallback_prompt)
    
    if result:
        return result + "\n\n(Note: Image analysis unavailable)"

    return "Error: All models failed to process the request."

def analyze_lead_relevance(post_text):
    """
    Analyzes Facebook posts to filter potential automotive leads using Groq.
    Returns 'YES' or 'NO' based on relevance.
    """
    
    # 1. Define a strict prompt for binary classification
    # We keep it in English as Llama 3.3 handles instructions better this way,
    # even when analyzing Hebrew text.
    prompt = f"""
    Analyze the following Facebook post and determine if the author is looking for:
    - Car repairs or mechanic services
    - Vehicle diagnostics or troubleshooting
    - Specific automotive parts installation
    - Recommendations for a garage or mechanic

    Reply with ONLY 'YES' or 'NO'.

    Post: {post_text}
    """

    try:
        # 2. Use the new clean pipeline for Groq
        # This keeps the main logic decoupled from the API implementation
        result = call_groq_llama(prompt)

        if result:
            # Clean the output to ensure we get a strict 'YES' or 'NO'
            cleaned_result = result.strip().upper()
            if 'YES' in cleaned_result:
                return "YES"
            if 'NO' in cleaned_result:
                return "NO"

        return "NO"

    except Exception as e:
        logging.error(f"Lead relevance analysis failed: {e}")
        return "NO"