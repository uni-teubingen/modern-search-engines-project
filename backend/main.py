from crawler import crawl
import db
import indexing
from app import app

#test
import sqlite3
from db import DB_PATH


if __name__ == "__main__":
    #db.drop_all_tables()
    db.init_db()
    #crawl()
    #db.insert_varied_dummy_documents(2000)
    # init_db()
    #indexing.compute_and_store_tfidf()
    #db.print_tfs_entries()
    # init_db()

    # token print test
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT term FROM tfs ORDER BY term")
        terms = cursor.fetchall()
        print("\n🌸 Alle gespeicherten Tokens im Index:")
        for term in terms:
            print(f" • {term[0]}")

    app.run(host="0.0.0.0", port=5050)
