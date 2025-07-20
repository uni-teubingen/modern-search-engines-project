import crawler
import db
import indexing
import time
from app import app
if __name__ == "__main__":
    # index = indexing.TFIDFIndexer(db.DB_PATH)
    database =db.Database(db.DB_PATH)
    # start_time = time.time()
    database.drop_all()
    database.init()
    crawler = crawler.Crawler()
    crawler.start()
    # index.compute_and_store()
    # end_time = time.time()
    # elapsed = end_time - start_time
    # print(f"⏱️ Gesamtdauer: {elapsed:.2f} Sekunden")
    # print("✅ Backend gestartet.")
    app.run(host="0.0.0.0", port=5050)
