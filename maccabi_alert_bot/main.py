import json
from scraper.site_reader import fetch_maccabi_news, extract_ticket_articles, fetch_article_content
from nlp.parser import parse_ticket_info
from database.state_manager import init_db, process_new_article
from notifications.whatsapp import send_whatsapp_alert
from apscheduler.schedulers.blocking import BlockingScheduler

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
    if not articles:
        print("[INFO] No relevant ticket articles found in this cycle.")
        return

    print(f"\n[SUCCESS] Found {len(articles)} target(s).")
    
    for article in articles:
        title = article['title']
        url = article['url']
        print(f"\n[INFO] Processing: '{title}'")
        
        # 3. התייעצות עם מסד הנתונים - האם זו כתבה שכבר שלחנו?
        is_new = process_new_article(url)
        
        if not is_new:
            print("[SKIP] Alert already sent for this article. Skipping.")
            continue
            
        print("[ACTION] Brand new ticket sale! Fetching details...")
        
        # 4. חילוץ עומק של טקסט הכתבה
        content = fetch_article_content(url)
        extraction_text = ""
        
        if not content:
            print("[ERROR] Could not extract text. Will send a basic alert.")
        else:
            # 5. עיבוד שפה באמצעות Gemini
            print("[ACTION] Analyzing text with Gemini AI...")
            parsed_data = parse_ticket_info(content)
            
            if parsed_data:
                # סידור ה-JSON לטקסט קריא ויפה עבור ההודעה בוואטסאפ
                start_time = parsed_data.get("sale_start", "לא צוין")
                eligibility_list = parsed_data.get("eligibility", [])
                eligibility_text = "\n".join([f"• {e}" for e in eligibility_list])
                summary = parsed_data.get("summary", "")
                
                extraction_text = f"🏟️ {summary}\n\n⏰ *פתיחת מכירה:* {start_time}\n\n🎫 *זכאויות:*\n{eligibility_text}"
                print("\n[SUCCESS] Extracted Data Ready for WhatsApp!")
            else:
                print("[WARNING] AI parsing failed. Proceeding with basic alert.")
            
        # 6. שליחת ההודעה דרך Twilio
        print("[ACTION] Sending WhatsApp alert...")
        success = send_whatsapp_alert(title, url, extraction_text)
        
        if success:
            print("[SUCCESS] WhatsApp Alert sent successfully!")
        else:
            print("[ERROR] Failed to send WhatsApp alert.")

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