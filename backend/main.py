import crawler
import db
import indexing

from app import app
if __name__ == "__main__":
    database =db.Database(db.DB_PATH)
    # database.drop_all()
    # database.init()
    has_pages,has_tfs=database.has_entries()
    if(not has_pages):
        crawl = crawler.Crawler()
        crawl.start()
        index = indexing.TFIDFIndexer(db.DB_PATH)
        index.compute_and_store()
        app.run(host="0.0.0.0", port=5050)
    elif(not has_tfs):
        index = indexing.TFIDFIndexer(db.DB_PATH)
        index.compute_and_store()
        app.run(host="0.0.0.0", port=5050)
    else:
        app.run(host="0.0.0.0", port=5050)