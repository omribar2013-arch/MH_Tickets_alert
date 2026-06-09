import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TARGET_URL = "https://mhaifafc.com/news"
BASE_URL = "https://mhaifafc.com"

def fetch_maccabi_news():
    """
    שולף את ה-HTML מאתר מכבי חיפה.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch data from {TARGET_URL}")
        print(f"Details: {e}")
        return None

def extract_ticket_articles(soup):
   
    ticket_articles = []
    
    article_links = soup.find_all('a', href=re.compile(r'/news/\d+'))
    
    for link in article_links:
        text = link.get_text(strip=True)
        
        if not text:
            continue
            
        if "מכירת כרטיסים" in text:
            href = link.get('href')
            full_url = urljoin(BASE_URL, href)
            
            if not any(article['url'] == full_url for article in ticket_articles):
                ticket_articles.append({
                    "title": text,
                    "url": full_url
                })
                
    return ticket_articles


def fetch_article_content(article_url):
    """
    נכנס לתוך הלינק של הכתבה ושואב את כל טקסט הפסקאות מתוכה,
    כדי שנוכל להגיש אותו ל-LLM לחילוץ זכאויות ותאריכים.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # רוב הכתבות באינטרנט מאורגנות בתוך תגיות <p> (פסקאות)
        paragraphs = soup.find_all('p')
        
        # חיבור כל הפסקאות לטקסט אחד ארוך וניקוי רווחים מיותרים
        article_text = " ".join([p.get_text(strip=True) for p in paragraphs])
        
        # מנגנון אל-כשל: אם אין פסקאות מסיבה כלשהי, נמשוך את כל הטקסט (ה-LLM יידע לסנן את רעשי הרקע)
        if not article_text:
             article_text = soup.get_text(separator=' ', strip=True)
             
        return article_text
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch content from {article_url}")
        print(f"Details: {e}")
        return ""