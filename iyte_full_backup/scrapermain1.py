import os
import time
import sqlite3
import requests
import sys
import urllib3
import json
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ollama

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AIProcessor:
    def __init__(self, model="llama3.2:1b"):
        self.model = model

    def summarize_and_tag(self, text):
        try:
            prompt = f"Summarize this university webpage in one short sentence and provide 3 keywords. Format as JSON: {text[:2000]}"
            response = ollama.generate(model=self.model, prompt=prompt, format="json")
            return json.loads(response['response'])
        except Exception:
            return {"summary": "N/A", "keywords": []}

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
                summary TEXT,
                keywords TEXT,
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

    def save_page(self, url, title, content, summary, keywords, found_links):
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO pages (url, title, content, summary, keywords) VALUES (?, ?, ?, ?, ?)",
                (url, title, content, summary, json.dumps(keywords))
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
        os.nice(15)
        self.queue = deque([])
        self.seen = set()
        self.dead_domains = set()
        self.max_pages = max_pages
        self.parser = PageParser()
        self.db = DatabaseManager()
        self.ai = AIProcessor()
        self.page_count = 0
        
        self.db.cursor.execute("SELECT url FROM pages")
        visited_urls = [row[0] for row in self.db.cursor.fetchall()]
        self.page_count = len(visited_urls)
        
        for url in visited_urls:
            self.seen.add(url)

        self.db.cursor.execute("""
            SELECT DISTINCT target_url 
            FROM links 
            WHERE target_url NOT IN (SELECT url FROM pages)
        """)
        
        pending_links = [row[0] for row in self.db.cursor.fetchall()]
        
        for link in pending_links:
            if "iyte.edu.tr" in urlparse(link).netloc and link not in self.seen:
                self.queue.append(link)
                self.seen.add(link)

        if not self.queue and self.page_count == 0:
            self.queue.append(start_url)
            self.seen.add(start_url)

        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=1)
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
            
            if parsed.netloc in self.dead_domains:
                return False
                
            blacklisted_ext = ('.pdf', '.jpg', '.png', '.zip', '.docx', '.xlsx', '.pptx', '.mp4')
            if any(url.lower().endswith(ext) for ext in blacklisted_ext):
                return False
                
            return "iyte.edu.tr" in parsed.netloc and url not in self.seen
        except:
            return False

    def run(self):
        while self.queue and self.page_count < self.max_pages:
            current_url = self.queue.popleft()
            
            try:
                response = self.session.get(current_url, timeout=10, verify=False)
                
                if response.status_code != 200:
                    continue

                if "text/html" not in response.headers.get("Content-Type", ""):
                    continue

                title, text, links = self.parser.parse(response.content, current_url)
                
                ai_data = self.ai.summarize_and_tag(text)
                
                summary_text = ai_data.get('summary', 'N/A')
                keywords_list = ai_data.get('keywords', [])
                
                self.db.save_page(current_url, title, text, summary_text, keywords_list, links)
                self.page_count += 1
                
                for link in links:
                    if self.is_valid_link(link):
                        self.seen.add(link)
                        self.queue.append(link)
                
                time.sleep(2)

            except requests.exceptions.ConnectionError as e:
                print(f"Dead domain blocked: {current_url}", file=sys.stderr)
                domain = urlparse(current_url).netloc
                self.dead_domains.add(domain)
                
            except Exception as e:
                print(f"Error processing {current_url}: {e}", file=sys.stderr)
                
        self.db.close()

if __name__ == "__main__":
    start_url = "https://iyte.edu.tr/"
    bot = Crawler(start_url)
    bot.run()