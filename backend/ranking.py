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

#Retrieve documents relevnt to a query. You need (at least) two parameters:
	#query: The user's search query
	#index: The location of the local index storing the discovered documents.
def cosine(vec1, vec2):
    dot = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in set(vec1) | set(vec2))
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    return dot / (norm1 * norm2 + 1e-9)

def mean_variance_score(vec):
    if not vec:
        return 0.0
    values = list(vec.values())
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return mean - variance  # Portfolio Theory

def retrieve(query, index_path=db.DB_PATH):
    print(f"[Ranking] Query: '{query}'")

    tokens = list(tokenize(query).keys())
    print(f"[Ranking] Tokenized Query: {tokens}")

    if not tokens:
        print("[Ranking] No tokens, empty list.")
        return []

    tfidf_data = defaultdict(dict)
    placeholders = ",".join(["?"] * len(tokens))

    with sqlite3.connect(index_path) as conn:
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT doc_id, term, tfidf
            FROM tfs
            WHERE term IN ({placeholders})
        """, tokens)
        for doc_id, term, tfidf in cursor.fetchall():
            tfidf_data[doc_id][term] = tfidf

        cursor.execute(f"""
            SELECT term, idf
            FROM tfs
            WHERE term IN ({placeholders})
            GROUP BY term
        """, tokens)
        idf_dict = {term: idf for term, idf in cursor.fetchall()}

    query_tf = {term: 1 / len(tokens) for term in tokens}
    query_vec = {term: query_tf[term] * idf_dict.get(term, 0) for term in tokens}

    lambda_param = 0.5  # 0 diversity <-> 1 relevance
    alpha_param = 0.5 # mean variance score
    selected = []
    selected_scores = {}
    candidates = list(tfidf_data.keys())

    for _ in range(min(100, len(candidates))):
        best_doc = None
        best_score = -1

        for doc_id in candidates:
            sim_query = cosine(tfidf_data[doc_id], query_vec)
            sim_selected = max(
                [cosine(tfidf_data[doc_id], tfidf_data[s]) for s in selected],
                default=0
            )
            mv_score = mean_variance_score(tfidf_data[doc_id])

            mmr_mv = (
                lambda_param * sim_query
                - (1 - lambda_param) * sim_selected
                + alpha_param * mv_score
            )

            if mmr_mv > best_score:
                best_score = mmr_mv
                best_doc = doc_id

        if best_doc:
            selected.append(best_doc)
            selected_scores[best_doc] = best_score
            candidates.remove(best_doc)
            meta = db.get_page_metadata(best_doc)
            title = meta["title"] if meta else "Unknown Title"
            print(f"[Ranking] Doc {best_doc} ('{title}') with Score {best_score:.4f}")

    results = []
    for doc_id in selected:
        meta = db.get_page_metadata(doc_id)
        if meta:
            results.append({
                "doc_id": doc_id,
                "title": meta["title"],
                "url": meta["url"],
                "score": selected_scores.get(doc_id, 0)
            })

    return results