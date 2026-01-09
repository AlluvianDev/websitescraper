import os
import time
import sqlite3
import requests
import sys
import urllib3
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PageParser:
    def parse(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        
        for script in soup(["script", "style", "noscript"]):
            script.extract()
            
        text_content = soup.get_text(separator='\n', strip=True)
        title = soup.title.string if soup.title else base_url
        
        links = []
        for tag in soup.find_all('a', href=True):
            full_url = urljoin(base_url, tag['href'])
            links.append(full_url)
            
        return title, text_content, links

class DatabaseManager:
    def __init__(self, db_name="iyte_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                content TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                source_url TEXT,
                target_url TEXT,
                FOREIGN KEY(source_url) REFERENCES pages(url)
            )
        ''')
        self.conn.commit()

    def save_page(self, url, title, content, found_links):
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO pages (url, title, content) VALUES (?, ?, ?)",
                (url, title, content)
            )
            
            link_data = [(url, link) for link in found_links]
            if link_data:
                self.cursor.executemany(
                    "INSERT INTO links (source_url, target_url) VALUES (?, ?)",
                    link_data
                )
            
            self.conn.commit()
        except Exception as e:
            print(f"Database error: {e}", file=sys.stderr)

    def close(self):
        self.conn.close()

class Crawler:
    def __init__(self, start_url, max_pages=100000):
        self.queue = deque([])  # Start empty, we will fill it from DB
        self.seen = set()
        self.max_pages = max_pages
        self.parser = PageParser()
        self.db = DatabaseManager()
        self.page_count = 0
        
        print("--- RESUMING CRAWL ---", flush=True)

        # 1. Load pages we have already finished (The "Done" list)
        print("Loading visited pages...", flush=True)
        self.db.cursor.execute("SELECT url FROM pages")
        visited_urls = [row[0] for row in self.db.cursor.fetchall()]
        self.page_count = len(visited_urls)
        
        # Add them to 'seen' so we don't crawl them again
        for url in visited_urls:
            self.seen.add(url)
        print(f"Loaded {self.page_count} finished pages.", flush=True)

        # 2. Find links we saw but haven't crawled yet (The "To Do" list)
        print("Rebuilding queue from pending links (this might take a moment)...", flush=True)
        # This SQL finds links that appear in 'links' table but NOT in 'pages' table
        self.db.cursor.execute("""
            SELECT DISTINCT target_url 
            FROM links 
            WHERE target_url NOT IN (SELECT url FROM pages)
        """)
        
        pending_links = [row[0] for row in self.db.cursor.fetchall()]
        
        count_added = 0
        for link in pending_links:
            # Only add valid IYTE links that we haven't 'seen' yet
            if "iyte.edu.tr" in urlparse(link).netloc and link not in self.seen:
                self.queue.append(link)
                self.seen.add(link) # Mark as seen so we don't queue it twice
                count_added += 1

        print(f"Resurrection complete! Added {count_added} pages to the queue.", flush=True)
        
        # If queue is empty (e.g., first run), start with the start_url
        if not self.queue and self.page_count == 0:
            self.queue.append(start_url)
            self.seen.add(start_url)

        # --------------------------------------

        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })

    def is_valid_link(self, url):
        try:
            parsed = urlparse(url)
            return "iyte.edu.tr" in parsed.netloc and url not in self.seen
        except:
            return False

    def run(self):
        print(f"Starting crawl at {time.strftime('%X')}", flush=True)
        
        while self.queue and self.page_count < self.max_pages:
            current_url = self.queue.popleft()
            
            try:
                print(f"[{self.page_count + 1}] Processing: {current_url}", flush=True)
                
                response = self.session.get(current_url, timeout=15, verify=False)
                
                if response.status_code != 200:
                    print(f"   Skipping {current_url} (Status: {response.status_code})", flush=True)
                    continue

                if "text/html" not in response.headers.get("Content-Type", ""):
                    continue

                title, text, links = self.parser.parse(response.content, current_url)
                self.db.save_page(current_url, title, text, links)
                self.page_count += 1
                
                new_links_count = 0
                for link in links:
                    if self.is_valid_link(link):
                        self.seen.add(link)
                        self.queue.append(link)
                        new_links_count += 1
                
                print(f"   Found {new_links_count} new links", flush=True)
                time.sleep(0.5)

            except Exception as e:
                print(f"   Failed to process {current_url}: {e}", file=sys.stderr, flush=True)
                
        self.db.close()
        print("Crawl completed.", flush=True)

if __name__ == "__main__":
    start_url = "https://iyte.edu.tr/"
    bot = Crawler(start_url)
    bot.run()