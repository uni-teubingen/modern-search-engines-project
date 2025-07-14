import sqlite3
import os
import random
DB_PATH = "data/search.db"

SEED_URLS = [
    "https://www.germany.travel/en/cities-culture/tuebingen.html",
    "https://www.expatrio.com/about-germany/eberhard-karls-universitat-tubingen",
    "https://en.wikipedia.org/wiki/Tübingen",
    "https://historicgermany.travel/historic-germany/tubingen/",
    "https://uni-tuebingen.de/en"
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
            id INTEGER PRIMARY KEY,
            doc_id INTEGER,
            term TEXT,
            tf REAL,
            idf REAL,
            tfidf REAL,
            FOREIGN KEY (doc_id) REFERENCES pages(id)
        );
    """)
    print("[✅] Datenbank initialisiert:", DB_PATH)
    conn.commit()
    conn.close()

def get_all_documents():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, content FROM pages")
        return cursor.fetchall()

def get_page_metadata(doc_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT title, url FROM pages WHERE id = ?", (doc_id,))
        return cursor.fetchone()

def reset_tfs_table():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tfs")
        conn.commit()

def insert_tfidf(doc_id, term, tf, idf, tfidf):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tfs (doc_id, term, tf, idf, tfidf)
            VALUES (?, ?, ?, ?, ?)
        """, (doc_id, term, tf, idf, tfidf))
        conn.commit()


def print_tfs_entries():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tfs ORDER BY doc_id, term LIMIT 500")  # Begrenze Ausgabe bei Bedarf
    rows = cursor.fetchall()

    if not rows:
        print("⚠️  Keine Einträge in der 'tfs'-Tabelle gefunden.")
        return

    print(f"🔍 {len(rows)} Einträge in 'tfs':\n")
    for row in rows:
        print(f"[doc_id={row['doc_id']}] term='{row['term']}' | tf={row['tf']:.4f} | idf={row['idf']:.4f} | tfidf={row['tfidf']:.4f}")

    conn.close()


def drop_all_tables():
    if not os.path.exists(DB_PATH):
        print("Datenbank existiert nicht.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables_to_drop = ["pages", "tfs"]

    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")
            print(f"Tabelle '{table}' gelöscht.")
        except Exception as e:
            print(f"Fehler beim Löschen von '{table}': {e}")

    conn.commit()
    conn.close()
    print("Alle Tabellen erfolgreich gelöscht.")