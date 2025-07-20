import sqlite3
import os

SEED_URLS = [
    "https://uni-tuebingen.de/en/international/study-in-tuebingen/"
    "https://www.tripadvisor.com/Restaurants-g198539-Tubingen_Baden_Wurttemberg.html"
    "https://www.happycow.net/europe/germany/tubingen/"
    "https://www.studying-in-germany.org/tubingen/"
    "https://www.germany.travel/en/cities-culture/tuebingen.html",
    "https://www.expatrio.com/about-germany/eberhard-karls-universitat-tubingen",
    "https://en.wikipedia.org/wiki/Tübingen",
    "https://historicgermany.travel/historic-germany/tubingen/",
    "https://www.mygermanyvacation.com/best-things-to-do-and-see-in-tubingen-germany/",
    "https://visit-tubingen.co.uk/",
    "http://britannica.com/place/Tubingen-Germany",
    #"https://uni-tuebingen.de/en"

]
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "search.db")

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.db_path)

    def init(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY,
                    url TEXT UNIQUE,
                    title TEXT,
                    content TEXT,
                    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    done INTEGER DEFAULT 0
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
            print("[✅] Datenbank initialisiert:", self.db_path)

    def drop_all(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            for table in ["pages", "tfs"]:
                cursor.execute(f"DROP TABLE IF EXISTS {table};")
                print(f"Tabelle '{table}' gelöscht.")
            print("Alle Tabellen erfolgreich gelöscht.")

class PageTable:
    def __init__(self, db: Database):
        self.db = db

    def get_all_ids(self):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM pages")
            return [row[0] for row in cursor.fetchall()]

    def get_content(self, doc_id):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM pages WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_all(self):
        with self.db.connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, content FROM pages")
            return cursor.fetchall()

    def get_metadata(self, doc_id):
        with self.db.connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT title, url FROM pages WHERE id = ?", (doc_id,))
            return cursor.fetchone()
        x   
    def print_all(self):
        with self.db.connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pages")
            rows = cursor.fetchall()
            if not rows:
                print("⚠️  Keine Einträge in der 'pages'-Tabelle gefunden.")
                return
            for row in rows:
                print(f"[id={row['id']}] URL={row['url']} | Titel={row['title']}")
                print(f"Inhalt: {row['content'][:200]}...\nZeitpunkt: {row['crawled_at']}")
                print("-" * 50)

class TfTable:
    def __init__(self, db: Database):
        self.db = db

    def reset(self):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tfs")
            conn.commit()

    def insert(self, doc_id, term, tf, idf, tfidf):
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tfs (doc_id, term, tf, idf, tfidf)
                VALUES (?, ?, ?, ?, ?)
            """, (doc_id, term, tf, idf, tfidf))
            conn.commit()

    def print_entries(self, limit=500):
        with self.db.connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tfs ORDER BY doc_id, term LIMIT ?", (limit,))
            rows = cursor.fetchall()
            if not rows:
                print("⚠️  Keine Einträge in der 'tfs'-Tabelle gefunden.")
                return
            for row in rows:
                print(f"[doc_id={row['doc_id']}] term='{row['term']}' | tf={row['tf']:.4f} | idf={row['idf']:.4f} | tfidf={row['tfidf']:.4f}")
