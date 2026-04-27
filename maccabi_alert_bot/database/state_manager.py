import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    return psycopg2.connect(
        host=os.environ['SUPABASE_HOST'],
        port=int(os.environ['SUPABASE_PORT']),
        database=os.environ['SUPABASE_DB'],
        user=os.environ['SUPABASE_USER'],
        password=os.environ['SUPABASE_PASSWORD'],
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
