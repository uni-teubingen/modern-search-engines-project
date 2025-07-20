import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import tldextract
import sqlite3
import time
import threading
from queue import Queue
from db import DB_PATH, SEED_URLS

ALLOWED_DOMAIN = "tuebingen"
MAX_PAGES = 4000
USER_AGENT = "TüBingCrawler/1.0"
WORKER_THREADS = 10  # Anzahl paralleler Crawler
REQUEST_DELAY = 0.5  # Sekunden zwischen Requests

# Shared Resources
robot_parsers = {}  # Hier definieren wir robot_parsers auf Modulebene
url_lock = threading.Lock()
seen_urls = set()
english_urls = set()
german_urls = set()
frontier = Queue()
crawled_count = 0

def is_404_page(soup):
    """Prüft ob Seite eine 404 Fehlerseite ist"""
    if soup.title and "404" in soup.title.text.lower():
        return True
    if soup.find(text=lambda t: "not found" in t.lower()):
        return True
    return False

def normalize_url(url):
    """Normalisiert URLs und entfernt unnötige Parameter"""
    parsed = urlparse(url)
    # Entferne Query-Parameter und Fragmente
    clean_url = parsed._replace(query="", fragment="").geturl()
    # Entferne doppelte Schrägstriche
    clean_url = clean_url.replace("//", "/") if "://" not in clean_url else clean_url
    return clean_url.rstrip('/')

def is_allowed_by_robots(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    
    with url_lock:  # Thread-sicherer Zugriff
        if domain not in robot_parsers:
            rp = RobotFileParser()
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            
            try:
                response = requests.get(
                    robots_url,
                    headers={'User-Agent': USER_AGENT},
                    timeout=3
                )
                if response.ok:
                    rp.parse(response.text.splitlines())
                else:
                    rp = None
            except Exception:
                rp = None
            
            robot_parsers[domain] = rp
        
        parser = robot_parsers[domain]
        return parser.can_fetch(USER_AGENT, url) if parser else True

def is_english(text):
    """Verbesserte Spracherkennung"""
    english_words = {"the", "and", "is", "of", "in", "to", "with", "that", 
                    "as", "for", "on", "was", "are", "by", "this", "from"}
    words = text.lower().split()
    if len(words) < 20:  # Zu kurze Texte nicht bewerten
        return False
    matches = sum(1 for word in words if word in english_words)
    return matches / len(words) > 0.08  # 8% englische Wörter

def already_crawled(url):
    """Prüft ob URL bereits gecrawlt wurde (thread-safe)"""
    with url_lock:
        return url in seen_urls or url in german_urls

def save_page(url, title, content):
    """Speichert Seite in DB (thread-safe)"""
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

def process_url(url):
    """Verarbeitet eine einzelne URL"""
    global crawled_count
    
    normalized_url = normalize_url(url)
    
    # Skip bereits gesehene URLs
    if already_crawled(normalized_url):
        return
    
    # Skip deutsche URLs
    if "/de/" in normalized_url.lower():
        with url_lock:
            german_urls.add(normalized_url)
        return
    
    # Prüfe robots.txt
    if not is_allowed_by_robots(normalized_url):
        with url_lock:
            seen_urls.add(normalized_url)
        return
    
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(normalized_url, headers=headers, timeout=10)
        
        # Prüfe Statuscode
        if response.status_code != 200:
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Prüfe 404 Seite
        if is_404_page(soup):
            return
            
        text = soup.get_text(separator=' ', strip=True)
        
        # Sprache prüfen
        if not is_english(text):
            with url_lock:
                german_urls.add(normalized_url)
            return
            
        # Englische Seite verarbeiten
        title = soup.title.string.strip() if soup.title else ""
        content = text.strip()
        
        save_page(normalized_url, title, content)
        
        with url_lock:
            seen_urls.add(normalized_url)
            english_urls.add(normalized_url)
            crawled_count += 1
            #print(f"[{crawled_count}/{MAX_PAGES}] Crawled: {normalized_url}")
        
        # Neue Links extrahieren
        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Skip mailto-Links
            if href.startswith(("mailto:", "tel:", "javascript:", "ftp:", "file:")):
                continue
            absolute_url = urljoin(normalized_url, href)
            clean_url = normalize_url(absolute_url)
            
            # Nur erlaubte Domains hinzufügen
            domain = tldextract.extract(clean_url).domain
            if domain and ALLOWED_DOMAIN in domain.lower():
                if not already_crawled(clean_url):
                    frontier.put(clean_url)
                    
    except Exception as e:
        print(f"[Error] {normalized_url}: {str(e)[:100]}")
    finally:
        time.sleep(REQUEST_DELAY)

def worker():
    """Worker-Thread für paralleles Crawling"""
    while True:
        if crawled_count >= MAX_PAGES:
            break
        url = frontier.get()
        try:
            process_url(url)
        finally:
            frontier.task_done()

def crawl():
    """Startet das Crawling mit mehreren Workern"""
    #init_db()
    start_time = time.time()
    
    # Seed URLs zur Warteschlange hinzufügen
    for url in SEED_URLS:
        frontier.put(normalize_url(url))
    # Worker-Threads starten
    threads = []
    for _ in range(WORKER_THREADS):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)
    try:
        # Hauptschleife für Fortschrittskontrolle
        while True:
            time.sleep(1)
            
            # Abbruchbedingungen prüfen
            if crawled_count >= MAX_PAGES:
                print(f"MAX_PAGES ({MAX_PAGES}) erreicht")
                break
    except KeyboardInterrupt:
        print("\n🛑 Manueller Abbruch durch Nutzer")
    finally:
        for t in threads:
            t.join(timeout=2)
        print(f"✅ Crawling abgeschlossen.")
        end_time = time.time()
        elapsed = start_time - end_time
        print(f"⏱️ Crawling abgeschlossen in {elapsed:.2f} Sekunden")