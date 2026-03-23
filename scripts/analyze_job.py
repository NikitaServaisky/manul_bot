import os
from google import genai
from dotenv import load_dotenv
from PIL import Image

# טעינת הגדרות
load_dotenv()

# אתחול הלקוח החדש (Client)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_mechanic_job(image_path):
    try:
        # טעינת התמונה
        img = Image.open(image_path)
        
        prompt = """
        אתה עוזר טכני מומחה למוסך 'מנול גארז'. 
        תסתכל על התמונה המצורפת ונתח אותה עבור הלקוח:
        1. מה רואים בתמונה? (חלק פגום, שלב בעבודה, רכב מסוים)
        2. מה לדעתך הבעיה הטכנית כאן?
        3. תכתוב פוסט קצר ושיווקי לטלגרם שמסביר על התיקון הזה.
        
        תענה בעברית מקצועית וקלילה.
        """
        
        # שליחה למודל בסינטקס החדש
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, img]
        )
        
        return response.text

    except Exception as e:
        return f"אופס, משהו השתבש: {e}"

if __name__ == "__main__":
    image_file = "job.jpg"
    
    if os.path.exists(image_file):
        print("מנתח את התמונה עם ה-SDK החדש...")
        result = analyze_mechanic_job(image_file)
        print("-" * 30)
        print(result)
        print("-" * 30)
    else:
        print(f"לא מצאתי את {image_file}")