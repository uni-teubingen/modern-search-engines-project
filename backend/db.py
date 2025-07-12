import sqlite3
import os

DB_PATH = "data/search.db"

SEED_URLS = [
    "https://www.tuebingen.de/",
    "https://www.tuebingen.de/tourismus",
    "https://www.tourismus-tuebingen.de/",
    "https://www.tuebingen-info.de/gastronomie",
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
    conn.commit()
    conn.close()
