from core.ai_clients import genai, groq
from PIL import Image

def analyze_lead_relevance(text):
    """Fast text analysis using Groq"""
    prompt = f"Is this Facebook post looking a car mechanic? Answer 'Yes' or 'No'"
    res = groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )
    return res.choices[0].message.content

def analyze_mechinic_worck(image_path, instruction=None):
    """Deep vision analysis using Gemini"""
    img = Image.open(image_path)
    base_prompt = "You are the technical assistant of 'Manul garage' analyze the repair in the picture and write a marketing post for the garage's Facebook in Hebrew."
    prompt = f"{base_prompt}\nUpdate: {instruction}" if instruction else base_prompt

    response = gemini.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt, img]
    )
    return response.text