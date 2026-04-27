import sqlite3
import os

# הקובץ בו יישמרו הנתונים (ייווצר אוטומטית בתיקיית השורש של הפרויקט)
DB_PATH = "maccabi_alerts.db"

def init_db():
    """
    יוצר את מסד הנתונים והטבלה אם הם לא קיימים.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # יוצר טבלה ששומרת את כתובת הכתבה (כמפתח ראשי למניעת כפילויות) ואת זמן הגילוי
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_articles (
            url TEXT PRIMARY KEY,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def process_new_article(url):
    """
    בודק אם הכתבה חדשה. אם כן - שומר אותה ומחזיר True.
    אם היא כבר קיימת במסד הנתונים - מחזיר False.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # בודק אם ה-URL כבר קיים
    cursor.execute('SELECT 1 FROM processed_articles WHERE url = ?', (url,))
    exists = cursor.fetchone()
    
    if exists:
        conn.close()
        return False # הכתבה כבר טופלה בעבר
        
    # אם הגענו לכאן, הכתבה חדשה. נשמור אותה כדי לא לשלוח עליה התראה שוב
    try:
        cursor.execute('INSERT INTO processed_articles (url) VALUES (?)', (url,))
        conn.commit()
        conn.close()
        return True # כתבה חדשה בהצלחה
    except sqlite3.IntegrityError:
        conn.close()
        return False

# רץ רק אם נפעיל את הקובץ ישירות כדי לוודא שהטבלה נוצרת
if __name__ == "__main__":
    print("Initializing Database...")
    init_db()
    print("Testing functionality...")
    
    test_url = "https://mhaifafc.com/news/test-123"
    print(f"First insertion (should be True): {process_new_article(test_url)}")
    print(f"Second insertion (should be False): {process_new_article(test_url)}")