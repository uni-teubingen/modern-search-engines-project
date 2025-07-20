""" 2. Query Processing 
Process a textual query and return the 100 most relevant documents from your index. Please incorporate **at least one retrieval model innovation** that goes beyond BM25 or TF-IDF. Please allow for queries to be entered either individually in an interactive user interface (see also #3 below), or via a batch file containing multiple queries at once. The batch file (see `queries.txt` for an example) will be formatted to have one query per line, listing the query number, and query text as tab-separated entries. An example of the batch file for the first two queries looks like this:

```
1   tübingen attractions
2   food and drinks
```
"""

import sqlite3
import math
from collections import defaultdict
import db

# Helperfunctions
def cosine(v1, v2):
    denom = math.sqrt(sum(x*x for x in v1.values())) * math.sqrt(sum(x*x for x in v2.values()))
    if denom == 0: return 0.0
    return sum(v1.get(k, 0) * v2.get(k, 0) for k in set(v1) | set(v2)) / denom

def mean_variance_score(vec):
    values = list(vec.values())
    if not values: return 0.0
    mean = sum(values) / len(values)
    var = sum((v - mean)**2 for v in values) / len(values)
    return mean - var

def load_tfidf_data(terms, conn):
    tfidf_data = defaultdict(dict)
    placeholders = ",".join("?" for _ in terms)
    cur = conn.cursor()
    cur.execute(f"SELECT doc_id, term, tfidf FROM tfs WHERE term IN ({placeholders})", terms)
    for doc_id, term, tfidf in cur.fetchall():
        tfidf_data[doc_id][term] = tfidf
    return tfidf_data

def load_idf_values(terms, conn):
    placeholders = ",".join("?" for _ in terms)
    cur = conn.cursor()
    cur.execute(f"SELECT term, idf FROM tfs WHERE term IN ({placeholders}) GROUP BY term", terms)
    return dict(cur.fetchall())

def compute_query_vector(terms, idf):
    n = len(terms)
    return {t: (1/n) * idf.get(t, 0) for t in terms}

def rank_documents(tfidf_data, query_vec, k, λ, α):
    selected = []
    scores = {}

    for _ in range(min(k, len(tfidf_data))):
        best_doc = None
        best_score = -float("inf")
        for doc, vec in tfidf_data.items():
            if doc in selected:
                continue
            sim_q = cosine(vec, query_vec)
            sim_d = max((cosine(vec, tfidf_data[d]) for d in selected), default=0)
            mv = mean_variance_score(vec)
            score = λ * sim_q - (1 - λ) * sim_d + α * mv
            if score > best_score:
                best_score = score
                best_doc = doc
        if best_doc is None:
            break
        selected.append(best_doc)
        scores[best_doc] = best_score

    return selected, scores

#Retrieve documents relevnt to a query. You need (at least) two parameters:
	#query: The user's search query
	#index: The location of the local index storing the discovered documents.
def retrieve(terms, index_path=db.DB_PATH, k=100, lambda_=0.5, alpha=0.5):
    if not terms:
        return [], False

    with sqlite3.connect(index_path) as conn:
        conn.row_factory = sqlite3.Row

        tfidf_data = load_tfidf_data(terms, conn)
        idf = load_idf_values(terms, conn)

        query_vec = compute_query_vector(terms, idf)
        selected_docs, scores = rank_documents(tfidf_data, query_vec, k, lambda_, alpha)

        if not selected_docs:
            return [], False

        placeholders = ",".join("?" for _ in selected_docs)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT DISTINCT doc_id FROM tfs
            WHERE doc_id IN ({placeholders})
        """, selected_docs)

        all_rows = cursor.fetchall()
        rows_by_doc = {row["doc_id"]: row for row in all_rows}

        ranked_rows = []
        for doc_id in selected_docs:
            if doc_id in rows_by_doc:
                ranked_rows.append(rows_by_doc[doc_id])

        contains_boris_palmer = False
        page_table = db.PageTable(db.Database(index_path))
        for row in ranked_rows:
            content = page_table.get_content(row["doc_id"])
            if content and "boris palmer" in content.lower():
                contains_boris_palmer = True
                break

    return ranked_rows, contains_boris_palmer