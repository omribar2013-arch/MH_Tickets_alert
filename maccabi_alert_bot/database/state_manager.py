import os
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_db():
    # לקוח יחיד לכל התהליך - מונע פתיחת חיבור חדש בכל קריאה
    global _client
    if _client is None:
        _client = MongoClient(os.environ['MONGO_CONNECTION_STR'])
    return _client['maccabi_bot']

def needs_seeding():
    """
    True רק בהרצה הראשונה אי-פעם (מסד ריק). במקרה כזה כל הכתבות הקיימות באתר
    יסומנו כמטופלות בלי לשלוח התראה, כדי שלא נקבל הצפה של כתבות ישנות.
    מסד קיים (עם כתבות) נחשב כבר מאותחל.
    """
    db = get_db()
    if db.meta.find_one({'_id': 'seeded'}):
        return False
    if db.processed_articles.find_one({}):
        db.meta.update_one({'_id': 'seeded'}, {'$set': {'at': datetime.now(timezone.utc)}}, upsert=True)
        return False
    return True

def seed_articles(urls):
    for url in urls:
        process_new_article(url)
    db = get_db()
    db.meta.update_one({'_id': 'seeded'}, {'$set': {'at': datetime.now(timezone.utc)}}, upsert=True)

def record_fetch_failure(url):
    """סופר כמה פעמים נכשלה משיכת תוכן הכתבה. מחזיר את המספר המצטבר."""
    db = get_db()
    doc = db.fetch_failures.find_one_and_update(
        {'url': url}, {'$inc': {'count': 1}},
        upsert=True, return_document=ReturnDocument.AFTER)
    return doc['count']

def init_db():
    db = get_db()
    db.processed_articles.create_index('url', unique=True)

def process_new_article(url):
    db = get_db()
    try:
        db.processed_articles.insert_one({
            'url': url,
            'discovered_at': datetime.now(timezone.utc)
        })
        return True
    except DuplicateKeyError:
        return False

def unmark_article(url):
    """
    מוחק כתבה מהמסד כדי שתיבדק שוב במחזור הבא.
    בשימוש כשההתראה נכשלה - אין ערוץ גיבוי, אז לא נאבד את הכתבה.
    """
    db = get_db()
    db.processed_articles.delete_one({'url': url})
