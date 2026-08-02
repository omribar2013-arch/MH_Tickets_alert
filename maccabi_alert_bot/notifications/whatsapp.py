import os
import requests
from dotenv import load_dotenv

# טעינת משתני הסביבה (הטוקן של בוט הטלגרם)
load_dotenv()

def _result(ok, reason="", sid=None, status=None, error_code=None):
    return {"ok": ok, "reason": reason, "sid": sid, "status": status, "error_code": error_code}

def send_whatsapp_alert(title, url, extraction_text=""):
    """
    שולח התראה דרך Telegram Bot API.
    מקבל כותרת, קישור, ואת טקסט החילוץ של ה-AI (זכאויות ותאריכים).
    מחזיר dict: {ok, reason, sid, status, error_code}.
    """
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    to_number = os.getenv('MY_PHONE_NUMBER')

    # הגנת מפתחים: מוודא שהמפתחות קיימים לפני שמנסים לשלוח
    if not all([bot_token, chat_id]):
        print("[ERROR] Missing Telegram credentials in .env file.")
        return _result(False, reason="Missing Telegram credentials in .env file.")

    # בניית ההודעה - משלבים את הכל יחד להודעה אחת יפה
    message_body = f"🟢 *התראת מכבי חיפה!*\n\n"
    message_body += f"*{title}*\n\n"

    if extraction_text:
         message_body += f"{extraction_text}\n\n"

    message_body += f"🔗 קישור:\n{url}"

    try:
        # שיגור ההודעה דרך Telegram Bot API (התשובה מיידית ומכריעה)
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": message_body,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        data = response.json()

        if response.status_code == 200 and data.get("ok"):
            message_id = data["result"]["message_id"]
            return _result(True, sid=str(message_id), status="sent")

        # Telegram מחזיר תיאור שגיאה ברור בגוף התשובה
        reason = f"Telegram delivery failed (status={response.status_code}, description={data.get('description')})"
        print(f"[ERROR] {reason}")
        return _result(False, reason=reason, status="failed", error_code=data.get("error_code"))

    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message.")
        print(f"Details: {e}")
        return _result(False, reason=f"Exception during send: {e}")
