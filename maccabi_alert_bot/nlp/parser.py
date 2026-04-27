import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

def parse_ticket_info(article_text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY is missing in .env file.")
        return None

    client = genai.Client(api_key=api_key)

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
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        raw_result = response.text.replace('```json', '').replace('```', '').strip()
        parsed_data = json.loads(raw_result)
        return parsed_data

    except json.JSONDecodeError:
        print("[ERROR] The LLM did not return valid JSON.")
        print("Raw LLM output:", response.text)
        return None
    except Exception as e:
        print(f"[ERROR] Failed to parse with LLM. Details: {e}")
        return None