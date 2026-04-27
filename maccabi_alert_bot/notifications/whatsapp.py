import os
from twilio.rest import Client
from dotenv import load_dotenv

# טעינת משתני הסביבה (המפתחות של טוויליו)
load_dotenv()

def send_whatsapp_alert(title, url, extraction_text=""):
    """
    שולח התראת וואטסאפ דרך Twilio.
    מקבל כותרת, קישור, ואת טקסט החילוץ של ה-AI (זכאויות ותאריכים).
    """
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    to_number = os.getenv('MY_PHONE_NUMBER')

    # הגנת מפתחים: מוודא שכל המפתחות קיימים לפני שמנסים לשלוח
    if not all([account_sid, auth_token, from_number, to_number]):
        print("[ERROR] Missing Twilio credentials in .env file.")
        return False

    client = Client(account_sid, auth_token)

    # בניית ההודעה - משלבים את הכל יחד להודעה אחת יפה
    message_body = f"🟢 *התראת מכבי חיפה!*\n\n"
    message_body += f"*{title}*\n\n"
    
    if extraction_text:
         message_body += f"{extraction_text}\n\n"
         
    message_body += f"🔗 קישור:\n{url}"

    try:
        # שיגור ההודעה
        message = client.messages.create(
            from_=from_number,
            body=message_body,
            to=to_number
        )
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send WhatsApp message.")
        print(f"Details: {e}")
        return False