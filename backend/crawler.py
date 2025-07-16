import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import tldextract
import sqlite3
import time
from db import DB_PATH, SEED_URLS, init_db

ALLOWED_DOMAIN = "tuebingen"
MAX_PAGES = 300
USER_AGENT = "TüBingCrawler/1.0"  # Eigenen User-Agent definieren

# Cache für robots.txt-Parser
robot_parsers = {}

# === Hilfsfunktion für robots.txt-Prüfung ===
def is_allowed_by_robots(url):
    parsed = urlparse(url)
    domain = parsed.netloc  # Domain extrahieren (z.B. "www.tuebingen.de")
    
    # Neue Domain: robots.txt initialisieren
    if domain not in robot_parsers:
        rp = RobotFileParser()
        rp.set_url(f"{parsed.scheme}://{domain}/robots.txt")
        try:
            rp.read()  # robots.txt herunterladen
        except Exception as e:
            print(f"⚠️ robots.txt Fehler für {domain}: {e}")
            rp = None  # Bei Fehler: Keine Einschränkungen annehmen
        robot_parsers[domain] = rp
    
    # Prüfung ob Crawling erlaubt ist
    parser = robot_parsers[domain]
    if parser is None:
        return True  # Keine robots.txt = alles erlaubt
    return parser.can_fetch(USER_AGENT, url)

# === Einfache Stopword-basierte Englisch-Erkennung ===
ENGLISH_WORDS = set([
    "the", "and", "is", "of", "in", "to", "with", "that", "as", "for",
    "on", "was", "are", "by", "this", "from", "or", "at", "be", "an",
    "it", "not", "we", "have", "has", "you", "can", "our", "about"
])

def is_english(text):
    words = text.lower().split()
    if len(words) == 0:
        return False
    match_count = sum(1 for w in words if w in ENGLISH_WORDS)
    return match_count / len(words) > 0.10  # mind. 10 % englische Wörter

def already_crawled(url, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM pages WHERE url = ?", (url,))
    return cursor.fetchone() is not None

def save_page(url, title, content, conn):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO pages (url, title, content) VALUES (?, ?, ?)
        """, (url, title, content))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"[⚠️] Seite bereits gespeichert: {url}")
        pass  # URL bereits gespeichert

def crawl():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    frontier = list(SEED_URLS)
    seen = set()

    while frontier and len(seen) < MAX_PAGES:
        url = frontier.pop(0)
        
        # robots.txt-Prüfung
        #if not is_allowed_by_robots(url):
        #    print(f"[🚫] Blockiert durch robots.txt: {url}")
        #    seen.add(url)
        #    continue
            
        if url in seen or already_crawled(url, conn):
            continue

        try:
            # Setze User-Agent für alle Requests
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
			# Links extrahieren
            for link_tag in soup.find_all("a", href=True):
                href = link_tag["href"]
                full_url = urljoin(url, href)
                domain = tldextract.extract(full_url).domain
                if domain and ALLOWED_DOMAIN in domain.lower():
                    if full_url not in seen:
                        frontier.append(full_url)

            # Sprache prüfen (per Wortvergleich)
            if not is_english(text):
                print(f"[–] Übersprungen (nicht Englisch): {url}")
                continue

            title = soup.title.string.strip() if soup.title else ""
            content = text.strip()

            print(f"[+] Gecrawlt ({len(seen)+1}/{MAX_PAGES}): {url}")
            save_page(url, title, content, conn)
            seen.add(url)

            

            time.sleep(1)  # höflich bleiben

        except Exception as e:
            print(f"[!] Fehler bei {url}: {e}")
            continue

    conn.close()
    print("✅ Crawling abgeschlossen.")
