from crawler import crawl
from db import init_db
from indexing import compute_and_store_tfidf
from app import app
if __name__ == "__main__":
    # init_db()
    # crawl()
    # compute_and_store_tfidf()
    app.run(host="0.0.0.0", port=5050)
