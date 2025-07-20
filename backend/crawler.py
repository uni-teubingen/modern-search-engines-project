import requests
import sqlite3
import threading
import time
from queue import Queue
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import tldextract
from bs4 import BeautifulSoup
from db import DB_PATH, SEED_URLS


class Crawler:
    def __init__(self, allowed_domains = {"tuebingen", "tubingen", "tübingen"}, max_pages=2000, threads=10, delay=0.5):
        self.allowed_domains = allowed_domains
        self.max_pages = max_pages
        self.user_agent = "TüBingCrawler/1.0"
        self.request_delay = delay
        self.worker_threads = threads

        # Shared state
        self.robot_parsers = {}
        self.url_lock = threading.Lock()
        self.seen_urls = set()
        self.english_urls = set()
        self.frontier = Queue()
        self.crawled_count = 0

    def _normalize_url(self, url):
        parsed = urlparse(url)
        clean_url = parsed._replace(query="", fragment="").geturl()
        clean_url = clean_url.replace("//", "/") if "://" not in clean_url else clean_url
        return clean_url.rstrip('/')
    
    def _normalize_url_without_http(self, url):
        parsed = urlparse(url)
        clean_url = parsed._replace(query="", fragment="").geturl()
        clean_url = clean_url.replace("//", "/") if "://" not in clean_url else clean_url
        return clean_url.rstrip('/')

    def _is_allowed_by_robots(self, url):
        parsed = urlparse(url)
        domain = parsed.netloc

        with self.url_lock:
            if domain not in self.robot_parsers:
                rp = RobotFileParser()
                robots_url = f"{parsed.scheme}://{domain}/robots.txt"
                try:
                    response = requests.get(robots_url, headers={'User-Agent': self.user_agent}, timeout=3)
                    if response.ok:
                        rp.parse(response.text.splitlines())
                    else:
                        rp = None
                except Exception:
                    rp = None
                self.robot_parsers[domain] = rp

            parser = self.robot_parsers[domain]
            return parser.can_fetch(self.user_agent, url) if parser else True

    def _is_english(self, text):
        english_words = {"the", "and", "is", "of", "in", "to", "with", "that",
                         "as", "for", "on", "was", "are", "by", "this", "from"}
        words = text.lower().split()
        if len(words) < 20:
            return False
        matches = sum(1 for word in words if word in english_words)
        return matches / len(words) > 0.05

    def _already_crawled(self, url):
        with self.url_lock:
            return url in self.seen_urls

    def _is_404_page(self, soup):
        if soup.title and "404" in soup.title.text.lower():
            return True
        if soup.find(text=lambda t: "not found" in t.lower()):
            return True
        return False

    def _save_page(self, url, title, content):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO pages (url, title, content) 
                    VALUES (?, ?, ?)
                """, (url, title, content))
                conn.commit()
        except sqlite3.Error as e:
            print(f"[DB Error] {url}: {e}")

    def _process_url(self, url):
        normalized_url = self._normalize_url(url)
        normalized_url_without_http = self._normalize_url_without_http(url)
        # Skip bereits gesehene URLs
        if self._already_crawled(normalized_url_without_http):
            return
        if "/de/" in normalized_url.lower():
            with self.url_lock:
                self.seen_urls.add(normalized_url_without_http)
            return

        if not self._is_allowed_by_robots(normalized_url):
            with self.url_lock:
                self.seen_urls.add(normalized_url_without_http)
            return

        try:
            response = requests.get(normalized_url, headers={'User-Agent': self.user_agent}, timeout=3)
            if response.status_code != 200:
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            if self._is_404_page(soup):
                return

            text = soup.get_text(separator=' ', strip=True)
            if not self._is_english(text):
                with self.url_lock:
                    self.seen_urls.add(normalized_url_without_http)
                return

            title = soup.title.string.strip() if soup.title else ""
            content = text.strip()
            self._save_page(normalized_url_without_http, title, content)

            with self.url_lock:
                self.seen_urls.add(normalized_url_without_http)
                self.english_urls.add(normalized_url_without_http)
                self.crawled_count += 1

            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith(("mailto:", "tel:", "javascript:", "ftp:", "file:")):
                    continue
                if href.endswith((".pdf", ".doc", ".xls", ".ppt")):
                    #print(f"[Ignored] {normalized_url} - unsupported file type: {href}")
                    continue
                absolute_url = urljoin(normalized_url, href)
                clean_url = self._normalize_url(absolute_url)
                domain = tldextract.extract(clean_url).domain
                if domain and any(allowed in domain.lower() for allowed in self.allowed_domains) and not self._already_crawled(clean_url):
                    self.frontier.put(clean_url)

        except Exception as e:
            print(f"[Error] {normalized_url}: {str(e)[:100]}")
            print("Mache weiter mit der nächsten URL...")
        finally:
            time.sleep(self.request_delay)

    def _worker(self):
        while True:
            if self.crawled_count >= self.max_pages:
                break
            url = self.frontier.get()
            try:
                self._process_url(url)
            finally:
                self.frontier.task_done()

    def start(self):
        print(f"✅ Crawler gestartet (max {self.max_pages} Seiten)...")
        start_time = time.time()

        for url in SEED_URLS:
            self.frontier.put(self._normalize_url(url))

        threads = []
        for _ in range(self.worker_threads):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            threads.append(t)

        try:
            while self.crawled_count < self.max_pages:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Crawler manuell gestoppt.")
        finally:
            for t in threads:
                t.join(timeout=2)
            print("✅ Crawling abgeschlossen.")
            print(f"⏱️ Laufzeit: {time.time() - start_time:.2f} Sekunden")
