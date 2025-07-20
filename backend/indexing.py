from tokenization import tokenize
import sqlite3
import db
import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

all_tokens = {}
all_tokens_lock = threading.Lock()

def calculate_document_frequencies(all_tokens):
    df = {}
    for tokens in all_tokens.values():
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1
    return df

def calculate_tf(tokens):
    total_terms = len(tokens)
    tf_counter = Counter(tokens)

    tf_result = {}
    for term, count in tf_counter.items():
        tf_result[term] = count / total_terms 
    return tf_result

def calculate_idf(term_doc_freq, total_docs):
    idf_result = {}
    for term, df in term_doc_freq.items():
        idf_result[term] = math.log(total_docs / df)
    return idf_result

def tokenize_batch(documents_chunk):
    local_tokens = {}
    for doc in documents_chunk:
        doc_id = doc["id"]
        content = doc["content"]
        tokens = tokenize(content)
        local_tokens[doc_id] = tokens

    
    with all_tokens_lock:
        all_tokens.update(local_tokens)

def process_document(doc_id, tokens, idf_values):
    tf_values = calculate_tf(tokens)
    results = []
    for term, tf in tf_values.items():
        idf = idf_values.get(term, 0.0)
        tfidf = tf * idf
        results.append((doc_id, term, tf, idf, tfidf))
    return results

def compute_and_store_tfidf():
    start_time = time.time()
    global all_tokens
    all_tokens = {}

    documents = db.get_all_documents()
    total_docs = len(documents)
    NUM_WORKERS = 8
    chunk_size = (len(documents) + NUM_WORKERS - 1) // NUM_WORKERS
    chunks = [documents[i:i+chunk_size] for i in range(0, len(documents), chunk_size)]
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        executor.map(tokenize_batch, chunks)
    term_doc_freq = calculate_document_frequencies(all_tokens)
    idf_values = calculate_idf(term_doc_freq, total_docs)
    db.reset_tfs_table()
    results = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {
            executor.submit(process_document, doc_id, tokens, idf_values): doc_id
            for doc_id, tokens in all_tokens.items()
        }

        for future in as_completed(futures):
            results.extend(future.result())

    def insert_batch(batch):
        with sqlite3.connect(db.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO tfs (doc_id, term, tf, idf, tfidf)
                VALUES (?, ?, ?, ?, ?)
            """, batch)
            conn.commit()

    BATCH_SIZE = 10000
    batches = [results[i:i+BATCH_SIZE] for i in range(0, len(results), BATCH_SIZE)]

    for batch in batches:
        insert_batch(batch)

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"⏱️ TF-IDF Index erstellt in {elapsed:.2f} Sekunden.")


def search(query, top_k=100):
    terms = tokenize(query)
    term_placeholders = ",".join(["?"] * len(terms))

    with sqlite3.connect(db.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT doc_id, SUM(tfidf) AS score
            FROM tfs
            WHERE term IN ({term_placeholders})
            GROUP BY doc_id
            ORDER BY score DESC
            LIMIT ?
        """, (*terms, top_k))

        ranked_docs = cursor.fetchall()

        results = []
        for row in ranked_docs:
            meta = db.get_page_metadata(row["doc_id"])
            results.append({
                "doc_id": row["doc_id"],
                "title": meta["title"] if meta else "",
                "url": meta["url"] if meta else "",
                "score": row["score"]
            })

        return results
