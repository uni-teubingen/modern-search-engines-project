import sqlite3
import os
import random
DB_PATH = "backend/data/search.db"

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



stadt_themen = [
    "Tübingen", "Universität", "Neckar", "Altstadt", "Stocherkahn", "Schloss", "Botanischer Garten"
]

aktivitaeten = [
    "spazieren", "studieren", "essen", "feiern", "lesen", "shoppen", "sport machen"
]

stimmungen = [
    "wunderschön", "interessant", "entspannt", "lebendig", "historisch", "modern", "grün"
]

def insert_varied_dummy_documents(n=100):
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            content TEXT,
            crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    for i in range(n):
        stadt = random.choice(stadt_themen)
        aktion = random.choice(aktivitaeten)
        stimmung = random.choice(stimmungen)

        url = f"https://example.com/{i}"
        title = f"Besuch in {stadt}"
        content = f"{stadt} ist eine {stimmung} Stadt. Man kann dort {aktion}. Es lohnt sich, {stadt} zu besuchen!"

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO pages (url, title, content)
                VALUES (?, ?, ?)
            """, (url, title, content))
        except Exception as e:
            print(f"Fehler bei Insert für {url}: {e}")

    conn.commit()
    conn.close()
    print(f"{n} variable Dummy-Dokumente erfolgreich eingefügt.")



def print_all_pages():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM pages")
            rows = cursor.fetchall()

            if not rows:
                print("⚠️  Keine Einträge in der 'pages'-Tabelle gefunden.")
                return

            print(f"📄 {len(rows)} Einträge in 'pages':\n")

            for row in rows:
                print(f"[id={row['id']}]")
                print(f"  URL     : {row['url']}")
                print(f"  Titel   : {row['title']}")
                print(f"  Inhalt  : {row['content'][:200]}...")  # nur Ausschnitt für Übersicht
                print(f"  Zeitpunkt: {row['crawled_at']}")
                print("-" * 60)

    except sqlite3.Error as e:
        print("❌ Fehler beim Lesen der Datenbank:", e)