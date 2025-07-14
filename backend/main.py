from crawler import crawl
import db
from indexing import compute_and_store_tfidf
from app import app
if __name__ == "__main__":
    db.init_db()
    # crawl()
    # init_db()
    # compute_and_store_tfidf()
    # print_tfs_entries()
    # init_db()

    # app.run(host="0.0.0.0", port=5050)
