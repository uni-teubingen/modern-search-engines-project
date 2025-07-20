import crawler
import db
import indexing
import time
from app import app
if __name__ == "__main__":
    database =db.Database(db.DB_PATH)
    database.init()
    tables_exist=database.has_entries()
    if(tables_exist):
        app.run(host="0.0.0.0", port=5050)
    else:
        index = indexing.TFIDFIndexer(db.DB_PATH)
        crawl = crawler.Crawler()
        crawl.start()
        index.compute_and_store()
        app.run(host="0.0.0.0", port=5050)
   
