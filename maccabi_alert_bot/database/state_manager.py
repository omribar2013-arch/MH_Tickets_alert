import os
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

def get_db():
    client = MongoClient(os.environ['MONGO_CONNECTION_STR'])
    return client['maccabi_bot']

def init_db():
    db = get_db()
    db.processed_articles.create_index('url', unique=True)

def process_new_article(url, check_only=False):
    db = get_db()
    if check_only:
        return db.processed_articles.find_one({'url': url}) is None
    try:
        db.processed_articles.insert_one({
            'url': url,
            'discovered_at': datetime.now(timezone.utc)
        })
        return True
    except DuplicateKeyError:
        return False
