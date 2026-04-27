import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# טעינת משתני הסביבה (כדי לקבל את המפתח)
load_dotenv()

def parse_ticket_info(article_text):
    """
    מקבל את טקסט הכתבה המלא, שולח ל-Gemini, 
    ומחזיר מילון (JSON) עם התאריכים והזכאויות.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is missing in .env file.")
        return None

    # הגדרת המפתח מול הספרייה של גוגל
    genai.configure(api_key=api_key)
    
    # נשתמש במודל הפלאש - הוא הכי מהיר, זול, ומצוין למשימות חילוץ טקסט
    model =  genai.GenerativeModel('gemini-2.5-flash')
    
    # הפרומפט באנגלית לדיוק מקסימלי, עם הוראה להחזיר ערכים בעברית
    prompt = f"""
    You are a system bot whose task is to read articles from the Maccabi Haifa FC website and extract data regarding ticket sales.
    Read the provided text and return *STRICTLY* a valid JSON object. Do not include any markdown formatting (like ```json), preceding text, or comments.
    
    Important: The output values inside the JSON must be written in Hebrew.

    Required JSON structure:
    {{
        "sale_start": "Date and time when the ticket sale begins for the first eligible group (if mentioned. If not, write 'לא צוין')",
        "eligibility": [
            "Eligibility 1 (e.g., מנויי חוץ - יום א' 10:00)",
            "Eligibility 2 (e.g., גרין פלוס - יום ב' 12:00)"
        ],
        "summary": "One short sentence summarizing who the match is against and where"
    }}

    Text to extract:
    {article_text}
    """
    
    try:
        # שליחה למודל
        response = model.generate_content(prompt)
        
        # ניקוי בסיסי: לפעמים ה-LLM עוטף את התשובה ב-```json ... ```
        raw_result = response.text.replace('```json', '').replace('```', '').strip()
        
        # המרה מטקסט לאובייקט מילון של פייתון
        parsed_data = json.loads(raw_result)
        return parsed_data
        
    except json.JSONDecodeError:
        print("[ERROR] The LLM did not return valid JSON.")
        print("Raw LLM output:", response.text)
        return None
    except Exception as e:
        print(f"[ERROR] Failed to parse with LLM. Details: {e}")
        return None