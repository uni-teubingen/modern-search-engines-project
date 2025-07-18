from crawler import crawl
import db
import indexing
from app import app
if __name__ == "__main__":
    db.drop_all_tables()
    db.init_db()
    crawl()
    #db.insert_varied_dummy_documents()
    # init_db()
    indexing.compute_and_store_tfidf()
    db.print_tfs_entries()
    # init_db()

    app.run(host="0.0.0.0", port=5050)
