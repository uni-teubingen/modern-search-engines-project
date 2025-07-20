import crawler
import db 
import indexing
import os
from app import app
if __name__ == "__main__":
    NOTHING = 0
    CRAWLING = 1
    INDEXING = 2
    RANKING = 3
    BACKEND = 4
    index = indexing.TFIDFIndexer(db.DB_PATH)
    database = db.Database(db.DB_PATH)
    status = db.StatusTable(database)
    if not os.path.isfile(db.DB_PATH):
        print("ℹ️  Datenbank nicht gefunden. Initialisiere Datenbank...")
        database.init()
        status.set_status(NOTHING)
    current_status = status.get_status()
    while current_status != BACKEND:
        if(current_status == NOTHING):
            print("ℹ️  Datenbank initialisieren...")
            database.drop_all()
            database.init()
            status.set_status(CRAWLING)
        elif (current_status == CRAWLING):
            print("ℹ️  Datenbank ist bereits initialisiert. Continue mit dem Crawlen...")
            crawler = crawler.Crawler()
            crawler.start()
            status.set_status(INDEXING)
        elif (current_status == INDEXING):
            print("ℹ️  Datenbank ist bereits initialisiert und Crawling ist abgeschlossen. Continue mit dem Indexieren...")
            index.compute_and_store()
            status.set_status(BACKEND)
        else:
            print("⚠️ Unbekannter Status in der Datenbank. Bitte überprüfen Sie die Datenbank.")
            exit(1)
        current_status = status.get_status()
    print("✅ Backend gestartet.")
    app.run(host="0.0.0.0", port=5050)
