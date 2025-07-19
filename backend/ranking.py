""" 2. Query Processing 
Process a textual query and return the 100 most relevant documents from your index. Please incorporate **at least one retrieval model innovation** that goes beyond BM25 or TF-IDF. Please allow for queries to be entered either individually in an interactive user interface (see also #3 below), or via a batch file containing multiple queries at once. The batch file (see `queries.txt` for an example) will be formatted to have one query per line, listing the query number, and query text as tab-separated entries. An example of the batch file for the first two queries looks like this:

```
1   tübingen attractions
2   food and drinks
```
"""

from tokenization import tokenize
import db
import sqlite3
import math
from collections import defaultdict

# Helperfunction for cosine similarity
def cosine(v1, v2):
    denom = math.sqrt(sum(x*x for x in v1.values())) * math.sqrt(sum(x*x for x in v2.values()))
    if denom == 0: return 0.0
    return sum(v1.get(k, 0) * v2.get(k, 0) for k in set(v1) | set(v2)) / denom

# Helperfunction for Mean Variance
def mean_variance_score(vec):
    values = list(vec.values())
    if not values: return 0.0
    mean = sum(values) / len(values)
    var = sum((v - mean)**2 for v in values) / len(values)
    return mean - var  # Portfolio Theory

# Helperfunction for loading TFIDF data
def load_tfidf_data(terms, conn):
    tfidf_data = defaultdict(dict)
    placeholders = ",".join("?" for _ in terms)
    cur = conn.cursor()
    cur.execute(f"SELECT doc_id, term, tfidf FROM tfs WHERE term IN ({placeholders})", terms)
    for doc, term, tfidf in cur.fetchall():
        tfidf_data[doc][term] = tfidf
    return tfidf_data

# Helperfunction for loading IDF values
def load_idf_values(terms, conn):
    placeholders = ",".join("?" for _ in terms)
    cur = conn.cursor()
    cur.execute(f"SELECT term, idf FROM tfs WHERE term IN ({placeholders}) GROUP BY term", terms)
    return dict(cur.fetchall())

# Helperfunction for computing vectors
def compute_query_vector(terms, idf):
    n = len(terms)
    return {t: (1/n) * idf.get(t, 0) for t in terms}

# Helperfunction for Ranking
def rank_documents(tfidf_data, query_vec, k, λ, α):
    selected, scores = [], {}

    for _ in range(min(k, len(tfidf_data))):
        best_doc, best_score = None, -1
        for doc in tfidf_data:
            if doc in selected: continue
            sim_q = cosine(tfidf_data[doc], query_vec)
            sim_d = max((cosine(tfidf_data[doc], tfidf_data[d]) for d in selected), default=0)
            mv = mean_variance_score(tfidf_data[doc])
            score = λ * sim_q - (1 - λ) * sim_d + α * mv
            if score > best_score:
                best_doc, best_score = doc, score

        if best_doc:
            selected.append(best_doc)
            scores[best_doc] = best_score
            title = db.get_page_metadata(best_doc)["title"] if db.get_page_metadata(best_doc) else "??"
            print(f"[Ranking] Doc {best_doc} ('{title}') Score: {best_score:.4f}")

    return selected, scores

#Retrieve documents relevnt to a query. You need (at least) two parameters:
	#query: The user's search query
	#index: The location of the local index storing the discovered documents.
def retrieve(query, index_path=db.DB_PATH, k=100, λ=0.5, α=0.5):
    print(f"[Ranking] Query: '{query}'")
    terms = list(tokenize(query).keys())
    if not terms: return []

    with sqlite3.connect(index_path) as conn:
        tfidf_data = load_tfidf_data(terms, conn)
        idf = load_idf_values(terms, conn)

    query_vec = compute_query_vector(terms, idf)
    selected, scores = rank_documents(tfidf_data, query_vec, k, λ, α)

    return [
        {
            "doc_id": doc,
            "title": meta["title"],
            "url": meta["url"],
            "score": scores[doc]
        }
        for doc in selected if (meta := db.get_page_metadata(doc))
    ]
