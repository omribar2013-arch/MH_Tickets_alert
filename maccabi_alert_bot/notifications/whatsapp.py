import os
import time
from twilio.rest import Client
from dotenv import load_dotenv

# טעינת משתני הסביבה (המפתחות של טוויליו)
load_dotenv()

# מצבים סופיים של הודעה ב-Twilio
TERMINAL_SUCCESS = {"sent", "delivered", "read"}
TERMINAL_FAILURE = {"failed", "undelivered"}

def _result(ok, reason="", sid=None, status=None, error_code=None):
    return {"ok": ok, "reason": reason, "sid": sid, "status": status, "error_code": error_code}

def send_whatsapp_alert(title, url, extraction_text=""):
    """
    שולח התראת וואטסאפ דרך Twilio ומוודא שההודעה אכן נמסרה.
    מקבל כותרת, קישור, ואת טקסט החילוץ של ה-AI (זכאויות ותאריכים).
    מחזיר dict: {ok, reason, sid, status, error_code}.
    """
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    to_number = os.getenv('MY_PHONE_NUMBER')

    # הגנת מפתחים: מוודא שכל המפתחות קיימים לפני שמנסים לשלוח
    if not all([account_sid, auth_token, from_number, to_number]):
        print("[ERROR] Missing Twilio credentials in .env file.")
        return _result(False, reason="Missing Twilio credentials in .env file.")

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

        sid = message.sid
        status = message.status
        error_code = message.error_code

        # Twilio מקבל את הקריאה מיד (status="queued") אבל כשלים בהמסירה
        # (למשל 63015 - סשן ה-sandbox פג) מגיעים אסינכרונית שניות אחר כך.
        # לכן נבצע polling קצר עד שנקבל מצב סופי.
        for _ in range(4):
            if error_code or status in TERMINAL_SUCCESS or status in TERMINAL_FAILURE:
                break
            time.sleep(2)
            fetched = client.messages(sid).fetch()
            status = fetched.status
            error_code = fetched.error_code

        if error_code or status in TERMINAL_FAILURE:
            reason = f"Twilio delivery failed (status={status}, error_code={error_code})"
            print(f"[ERROR] {reason}")
            return _result(False, reason=reason, sid=sid, status=status, error_code=error_code)

        # הצלחה, או עדיין queued/accepted (ניתן ליהנות מהספק כדי לא לשלוח מייל שווא)
        return _result(True, sid=sid, status=status, error_code=error_code)

    except Exception as e:
        print(f"[ERROR] Failed to send WhatsApp message.")
        print(f"Details: {e}")
        return _result(False, reason=f"Exception during send: {e}")