import sqlite3
import os

DB_PATH = "backend/data/search.db"

SEED_URLS = [
    "https://www.uni-tuebingen.de/en",
    "https://www.germany.travel/en/cities-culture/tuebingen.html",
    "https://www.expatrio.com/about-germany/eberhard-karls-universitat-tubingen",
    "https://en.wikipedia.org/wiki/Tübingen",
    "https://historicgermany.travel/historic-germany/tubingen/",
]

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            title TEXT,
            content TEXT,
            crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tfs (
            idxid INTEGER PRIMARY KEY,
        );
    """)
    print("[✅] Datenbank initialisiert:", DB_PATH)
    conn.commit()
    conn.close()
