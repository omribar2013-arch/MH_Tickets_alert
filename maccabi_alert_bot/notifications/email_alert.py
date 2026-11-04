import os
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from dotenv import load_dotenv

# טעינת משתני הסביבה (פרטי ה-Gmail)
load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _result(ok, reason=""):
    return {"ok": ok, "reason": reason}


def send_alert_email(title, url, extraction_text=""):
    """
    שולח את התראת הכרטיסים במייל. זהו ערוץ ההתראה היחיד של הבוט.
    מקבל כותרת, קישור, ואת טקסט החילוץ של ה-AI (זכאויות ותאריכים).
    מחזיר dict: {ok, reason}.
    """
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_APP_PASSWORD")
    # "or" ולא ברירת מחדל של getenv: ב-GitHub Actions סוד חסר מגיע כמחרוזת ריקה
    to_addr = os.getenv("ALERT_TO") or user

    if not all([user, password, to_addr]):
        reason = "Missing email credentials (EMAIL_USER / EMAIL_APP_PASSWORD / ALERT_TO)."
        print(f"[ERROR] {reason}")
        return _result(False, reason=reason)

    body = f"🟢 התראת מכבי חיפה!\n\n{title}\n\n"
    if extraction_text:
        body += f"{extraction_text}\n\n"
    body += f"🔗 קישור:\n{url}\n"

    msg = MIMEText(body, "plain", "utf-8")
    # הכותרת בעברית מקודדת ל-UTF-8 כדי שלקוחות מייל יציגו אותה נכון
    msg["Subject"] = Header(f"התראת מכבי חיפה: {title}", "utf-8")
    msg["From"] = user
    msg["To"] = to_addr

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to_addr], msg.as_string())
        return _result(True)
    except Exception as e:
        reason = f"Exception during email send: {e}"
        print(f"[ERROR] Failed to send alert email.")
        print(f"Details: {e}")
        return _result(False, reason=reason)
