import json
from scraper.site_reader import fetch_maccabi_news, extract_ticket_articles, fetch_article_content
from nlp.parser import parse_ticket_info
from database.state_manager import (
    init_db, process_new_article, unmark_article,
    needs_seeding, seed_articles, record_fetch_failure,
)
from notifications.email_alert import send_alert_email
from apscheduler.schedulers.blocking import BlockingScheduler

# כמה מחזורים מחכים לתוכן הכתבה לפני ששולחים התראה בסיסית בלי פרטים
MAX_CONTENT_RETRIES = 3


def build_extraction_text(parsed_data):
    """הופך את ה-JSON של Gemini לטקסט קריא. מחזיר "" אם המבנה לא תקין."""
    if not isinstance(parsed_data, dict):
        print("[WARNING] AI returned an unexpected structure. Proceeding with basic alert.")
        return ""

    start_time = parsed_data.get("sale_start", "לא צוין")
    eligibility_list = parsed_data.get("eligibility", [])
    if not isinstance(eligibility_list, list):
        eligibility_list = [eligibility_list]
    eligibility_text = "\n".join([f"• {e}" for e in eligibility_list])
    summary = parsed_data.get("summary", "")

    return f"🏟️ {summary}\n\n⏰ פתיחת מכירה: {start_time}\n\n🎫 זכאויות:\n{eligibility_text}"


def handle_article(article):
    """
    מטפל בכתבה אחת. מחזיר True אם הכתבה טופלה (נשלחה התראה או שכבר נשלחה),
    ו-False אם צריך לנסות שוב במחזור הבא (במקרה כזה הקורא משחרר את הסימון).
    """
    title = article['title']
    url = article['url']
    print(f"\n[INFO] Processing: '{title}'")

    # 3. התייעצות עם מסד הנתונים - האם זו כתבה שכבר שלחנו?
    if not process_new_article(url):
        print("[SKIP] Alert already sent for this article. Skipping.")
        return True

    # מכאן והלאה הכתבה מסומנת - כל כישלון חייב לשחרר אותה (ראו run_pipeline)
    print("[ACTION] Brand new ticket sale! Fetching details...")

    # 4. חילוץ עומק של טקסט הכתבה
    content = fetch_article_content(url)
    extraction_text = ""

    if not content:
        failures = record_fetch_failure(url)
        if failures < MAX_CONTENT_RETRIES:
            print(f"[ERROR] Could not extract text (attempt {failures}/{MAX_CONTENT_RETRIES}). Will retry next cycle.")
            return False
        print("[ERROR] Could not extract text after several attempts. Sending a basic alert.")
    else:
        # 5. עיבוד שפה באמצעות Gemini
        print("[ACTION] Analyzing text with Gemini AI...")
        parsed_data = parse_ticket_info(content)

        if parsed_data:
            extraction_text = build_extraction_text(parsed_data)
            if extraction_text:
                print("\n[SUCCESS] Extracted Data Ready for Email!")
        else:
            print("[WARNING] AI parsing failed. Proceeding with basic alert.")

    # 6. שליחת ההודעה במייל
    print("[ACTION] Sending email alert...")
    result = send_alert_email(title, url, extraction_text)

    if result["ok"]:
        print("[SUCCESS] Email alert sent successfully!")
        return True

    print(f"[ERROR] Failed to send email alert. Reason: {result['reason']}")
    return False


def run_pipeline():
    print("--------------------------------------------------")
    print("[INFO] Starting Full System Check Cycle...")

    # 1. משיכת הנתונים מהאתר
    soup = fetch_maccabi_news()
    if not soup:
        print("[ERROR] Could not fetch site data.")
        return

    # 2. חילוץ כתבות על כרטיסים
    articles = extract_ticket_articles(soup)

    # הרצה ראשונה אי-פעם: מסמנים את הכתבות הקיימות בלי לשלוח, כדי למנוע הצפה
    if needs_seeding():
        print(f"[SYSTEM] First run detected. Marking {len(articles)} existing article(s) as seen without alerting.")
        seed_articles([a['url'] for a in articles])
        return

    if not articles:
        print("[INFO] No relevant ticket articles found in this cycle.")
        return

    print(f"\n[SUCCESS] Found {len(articles)} target(s).")

    for article in articles:
        try:
            done = handle_article(article)
        except Exception as e:
            print(f"[ERROR] Unexpected failure while processing '{article['title']}': {e}")
            done = False

        if not done:
            # אין ערוץ גיבוי - משחררים את הכתבה כדי שהמחזור הבא ינסה שוב
            print("[ACTION] Unmarking article so the next cycle retries it.")
            try:
                unmark_article(article['url'])
            except Exception as e:
                print(f"[ERROR] Could not unmark article: {e}")

    print("--------------------------------------------------")


if __name__ == "__main__":
    # 1. הפעלת מסד הנתונים
    init_db()

    # 2. הרצה אחת מיידית ברגע שמפעילים את הקוד (כדי שלא נחכה 15 דקות לחינם)
    print("[SYSTEM] Performing initial startup check...")
    run_pipeline()

    # 3. הגדרת הסדרן (Scheduler)
    scheduler = BlockingScheduler()

    # הוספת המשימה: תריץ את run_pipeline כל 15 דקות
    scheduler.add_job(run_pipeline, 'interval', minutes=15)

    print("\n==================================================")
    print("🤖 [SYSTEM] Bot is now LIVE and running in the background.")
    print("⏳ [SYSTEM] Next check will occur in 15 minutes.")
    print("🛑 [SYSTEM] Press Ctrl+C in this terminal to stop.")
    print("==================================================\n")

    # 4. התנעת המנוע (מכאן הקוד "נתקע" וממשיך לרוץ בלולאה נצחית)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[SYSTEM] Bot shut down gracefully.")
