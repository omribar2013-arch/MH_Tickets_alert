import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# טעינת משתני הסביבה (פרטי ה-Gmail)
load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_failure_email(title, url, content, reason):
    """
    שולח מייל התראה כאשר שליחת הוואטסאפ נכשלה.
    המייל כולל את תוכן ההתראה המלא כך שהוא משמש גם כגיבוי.
    מחזיר True אם המייל נשלח, אחרת False (לעולם לא מפיל את ה-pipeline).
    """
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_APP_PASSWORD")
    to_addr = os.getenv("ALERT_TO", user)

    if not all([user, password, to_addr]):
        print("[ERROR] Missing email credentials (EMAIL_USER / EMAIL_APP_PASSWORD).")
        return False

    # Subject נשאר ASCII כדי להימנע מבעיות קידוד בכותרת
    subject = "Maccabi Bot: WhatsApp alert FAILED"

    body = (
        "A WhatsApp alert could NOT be delivered.\n\n"
        f"Reason: {reason}\n\n"
        "--- Alert content (fallback) ---\n"
        f"{title}\n\n"
        f"{content}\n\n"
        f"link: {url}\n"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to_addr], msg.as_string())
        print("[SUCCESS] Failure email sent.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send failure email.")
        print(f"Details: {e}")
        return False
