import sqlite3
import math
import time
from collections import Counter, defaultdict
from dto.result_dto import ResultDto
from tokenization import tokenize
from readability import Document
from bs4 import BeautifulSoup
import db


class TFIDFIndexer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db = db.Database(self.db_path)
        self.pages = db.PageTable(self.db)
        self.db = db.TfTable(self.db)

    def compute_and_store(self):
        
        start = time.time()
        documents = self.pages.get_all()
        print(f"📄 Indexing {len(documents)} documents...")

        doc_tokens, term_doc_freq = self._tokenize_documents(documents)
        idf_values = self._compute_idf(term_doc_freq, len(documents))
        batch = self._build_tfidf_batch(doc_tokens, idf_values)

        self.db.reset()
        self._store_batch(batch)

        print(f"✅ Index erstellt in {time.time() - start:.2f} sec")

    def _tokenize_documents(self, documents):
        doc_tokens = {}
        term_doc_freq = defaultdict(int)

        for doc in documents:
            tokens = tokenize(doc["content"])
            doc_tokens[doc["id"]] = tokens
            for term in set(tokens):
                term_doc_freq[term] += 1

        return doc_tokens, term_doc_freq

    def _compute_idf(self, term_doc_freq, total_docs):
        return {
            term: math.log(total_docs / df)
            for term, df in term_doc_freq.items()
        }

    def _build_tfidf_batch(self, doc_tokens, idf_values):
        batch = []
        for doc_id, tokens in doc_tokens.items():
            tf = Counter(tokens)
            total = len(tokens)
            for term, count in tf.items():
                tf_val = count / total
                idf_val = idf_values.get(term, 0.0)
                tfidf = tf_val * idf_val
                batch.append((doc_id, term, tf_val, idf_val, tfidf))
        return batch

    def _store_batch(self, batch):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO tfs (doc_id, term, tf, idf, tfidf)
                VALUES (?, ?, ?, ?, ?)
            """, batch)
            conn.commit()


class SearchEngine:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db = db.Database(self.db_path)
        self.pages = db.PageTable(self.db)

    def search(self, query, top_k=100):
        terms = tokenize(query)
        if not terms:
            return []

        scored_docs,palmer_score = self._get_ranked_documents(terms, top_k)
        return self._build_results(scored_docs, query,palmer_score)

    def _get_ranked_documents(self, terms, top_k):
        placeholders = ",".join(["?"] * len(terms))
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT doc_id, SUM(tfidf) AS score
                FROM tfs
                WHERE term IN ({placeholders})
                GROUP BY doc_id
                ORDER BY score DESC
                LIMIT ?
            """, (*terms, top_k))

            rows = cursor.fetchall()

            contains_boris_palmer = False

            # Dokumentinhalte holen und prüfen
            for row in rows:
                content = self.pages.get_content(row["doc_id"])
                if content and "boris palmer" in content.lower():
                    contains_boris_palmer = True
                    break

            return rows, contains_boris_palmer


    def _build_results(self, ranked_docs, query,palmer_score):
        results = []
        for row in ranked_docs:
            doc_id = row["doc_id"]
            meta = self.pages.get_metadata(doc_id)
            content = self.pages.get_content(doc_id)
            snippet = self._extract_snippet_from_html(content, query)
            result_dto = ResultDto(meta["title"] if meta else "",meta["url"] if meta else "",palmer_score,snippet)
            results.append(result_dto)
        return results

    def _extract_snippet_from_html(self, html: str, query: str, max_chars=250):
        try:
            doc = Document(html)
            main_html = doc.summary()
            text = BeautifulSoup(main_html, 'html.parser').get_text(separator=' ', strip=True)
        except Exception:
            text = BeautifulSoup(html, 'html.parser').get_text(separator=' ', strip=True)
        return self._generate_snippet(text, query, max_chars=max_chars)

    def _generate_snippet(self, text: str, query: str, window: int = 40, max_chars: int = 250) -> str:
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

        return text[:max_chars] + "..."  # fallback
