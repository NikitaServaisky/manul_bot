import logging
from google.genai import types
from core.ai_clients import gemini, groq

# Set logger for catch logs
logger = logging.getLogger(__name__)

def call_gemini_20_flash(prompt,image_data=None, mime_type="image/jpeg"):
    """
    Gemini 2.0 flash request with image supports (Bytes)
    """
    if not gemini:
        return None

    try:
        contents = [prompt]
        
        if image_data:
            contents.append(types.Part.from_bytes(data=image_data, mime_type=mime_type))

        response = gemini.models.generate_content(
            model = "gemini-2.0-flash",
            contents = contents
        )
        return response.text if response else None

    except Exception as e:
        logger.warning(f"Gemini 2.0 Flash filed: {e}")
        return None

def call_gemini_15_flash(prompt, image_data=None, mime_type="image/jpeg"):
    """
    Gemini 1.5 flash requets with image support
    """
    if not gemini:
        return None

    try:
        contents = [prompt]

        if image_data:
            contents.append(types.Part.from_bytes(data=image_data, mime_type=mime_type))

        response = gemini.models.generate_content(
            model="gemini-1.5-flash-v1beta",
            contents=contents
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini 1.5 API Error: {e}")
        return None

def call_groq_llama(prompt):
    """
    Groq llama request without supported image
    """
    if not groq:
        return None

    try:
        response = groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        return None