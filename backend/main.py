from crawler import crawl
import db
import indexing
import time
from app import app
if __name__ == "__main__":
    start_time = time.time()
    db.drop_all_tables()
    db.init_db()
    crawl()
    indexing.compute_and_store_tfidf()
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"⏱️ Gesamtdauer: {elapsed:.2f} Sekunden")
    print("✅ Backend gestartet.")
    app.run(host="0.0.0.0", port=5050)
