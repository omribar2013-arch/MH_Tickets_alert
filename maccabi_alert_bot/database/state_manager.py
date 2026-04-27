import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    url = urlparse(os.environ['SUPABASE_URL'])
    return psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],
        user=url.username,
        password=url.password,
        sslmode='require'
    )

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_articles (
            url TEXT PRIMARY KEY,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def process_new_article(url):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT 1 FROM processed_articles WHERE url = %s', (url,))
    exists = cursor.fetchone()

    if exists:
        conn.close()
        return False

    try:
        cursor.execute('INSERT INTO processed_articles (url) VALUES (%s)', (url,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False
