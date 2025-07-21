import sqlite3
import math
import time
from collections import Counter, defaultdict
from dto.result_dto import ResultDto
from readability import Document
from bs4 import BeautifulSoup
import db
from ranking import Ranker
import re
import os

class TFIDFIndexer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db = db.Database(self.db_path)
        self.pages = db.PageTable(self.db)
        self.db = db.TfTable(self.db)
        self.helper = HelperFunction()
    
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
            tokens = self.helper.tokenize(doc["content"])
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
        self.helper = HelperFunction()
        self.ranker = Ranker()
        self.tf = db.TfTable(self.db)

    def search(self, query,performance_report = True):
        terms = self.helper.tokenize(query)
        if not terms:
            return []

        scored_docs,palmer_score = self._get_ranked_documents(terms)
        results = self._build_results(scored_docs, query,palmer_score,performance_report,terms)
        if(performance_report):
            self.helper.performance_report(results)
        return results

    def _get_ranked_documents(self, terms):
        ranked_docs, palmer_flag = self.ranker.retrieve(terms)
        return ranked_docs, palmer_flag

    def _build_results(self, ranked_docs, query, palmer_score, performance_report,query_terms):
        results = []

        if performance_report:
            all_scores = self.tf.get_all_total_scores(query_terms)
        else:
            all_scores = {}

        for row in ranked_docs:
            doc_id = row["doc_id"]
            meta = self.pages.get_metadata(doc_id)
            content = self.pages.get_content(doc_id)
            snippet = self._extract_snippet_from_html(content, query)

            score = all_scores.get(doc_id, 0.0) if performance_report else 0.0

            result_dto = ResultDto(
                doc_id=doc_id,
                title=meta["title"] if meta else "",
                url=meta["url"] if meta else "",
                palmer_score=palmer_score,
                snippet=snippet,
                score=score
            )
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



class HelperFunction():
    
    def tokenize(self,text):
        stopwords = set([
        "the", "and", "is", "of", "in", "to", "with", "that", "as", "for", "on",
        "was", "are", "by", "this", "from", "be", "or", "an", "it"
        ])
        tokens = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        return [t for t in tokens if t not in stopwords]
    
    def performance_report(self, result):

        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "performance")
        os.makedirs(output_dir, exist_ok=True)

        filename = "performance_results.txt"
        filepath = os.path.join(output_dir, filename)

        query_number = 1
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    try:
                        last_query_num = int(last_line.split("\t")[0])
                        query_number = last_query_num + 1
                    except (IndexError, ValueError):
                        pass

        with open(filepath, "a", encoding="utf-8") as f:
            for rank, dto in enumerate(result[:100], start=1):
                line = f"{query_number}\t{rank}\t{dto.url}\t{dto.score:.3f}\n"
                f.write(line)

