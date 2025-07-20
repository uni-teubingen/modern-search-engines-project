from tokenization import tokenize
import sqlite3
import db
from collections import Counter, defaultdict
from readability import Document
from bs4 import BeautifulSoup
import math
import time

def compute_and_store_tfidf():
    start = time.time()
    documents = db.get_all_documents()
    total_docs = len(documents)
    print(f"📄 Indexing {total_docs} documents...")

    term_doc_freq = defaultdict(int)
    doc_tokens = {}

    for doc in documents:
        tokens = tokenize(doc["content"])
        doc_tokens[doc["id"]] = tokens
        for term in set(tokens):
            term_doc_freq[term] += 1

    idf_values = {term: math.log(total_docs / df) for term, df in term_doc_freq.items()}

    db.reset_tfs_table()
    batch = []
    for doc_id, tokens in doc_tokens.items():
        tf = Counter(tokens)
        total = len(tokens)
        for term, count in tf.items():
            tf_val = count / total
            idf_val = idf_values.get(term, 0.0)
            tfidf = tf_val * idf_val
            batch.append((doc_id, term, tf_val, idf_val, tfidf))

    with sqlite3.connect(db.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO tfs (doc_id, term, tf, idf, tfidf)
            VALUES (?, ?, ?, ?, ?)
        """, batch)
        conn.commit()

    print(f"✅ Index erstellt in {time.time() - start:.2f} sec")


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
            content = db.get_document_content(row["doc_id"])
            snippet = extract_snippet_from_html(content, query)
            results.append({
                "doc_id": row["doc_id"],
                "title": meta["title"] if meta else "",
                "url": meta["url"] if meta else "",
                "score": row["score"],
                "snippet": snippet
            })

        return results
    
def generate_snippet(text: str, query: str, window: int = 40, max_chars: int = 250) -> str:
    """
    Generiert ein Snippet aus dem Dokumenttext auf Basis der Suchanfrage.
    Bevorzugt keyword-relevante Ausschnitte, fallback: erste Sätze.
    """
    if not text or not query:
        return ""

    words = text.split()
    query_terms = query.lower().split()

    for i, word in enumerate(words):
        if any(q in word.lower() for q in query_terms):
            start = max(0, i - window // 2)
            end = min(len(words), i + window // 2)
            snippet = " ".join(words[start:end])
            return snippet.strip()[:max_chars] + "..."

def extract_snippet_from_html(html: str, query: str, max_chars=250):
    try:
        doc = Document(html)
        main_html = doc.summary()
        text = BeautifulSoup(main_html, 'html.parser').get_text(separator=' ', strip=True)
    except Exception:
        text = BeautifulSoup(html, 'html.parser').get_text(separator=' ', strip=True)

    return generate_snippet(text, query, max_chars=max_chars)

