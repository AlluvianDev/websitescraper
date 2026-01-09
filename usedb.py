import sqlite3
import sys
import time

def search_db(keyword):
    conn = sqlite3.connect('iyte_data.db')
    cursor = conn.cursor()

    print(f"Searching for: '{keyword}'...")
    start_time = time.time()

    query = """
        SELECT url, title 
        FROM pages 
        WHERE content LIKE ? OR title LIKE ? 
        LIMIT 100
    """
    
    wildcard_keyword = f"%{keyword}%"
    cursor.execute(query, (wildcard_keyword, wildcard_keyword))
    results = cursor.fetchall()
    
    end_time = time.time()
    duration = (end_time - start_time) * 1000

    print(f"\nFound {len(results)} results in {duration:.2f} ms:\n")

    for i, (url, title) in enumerate(results, 1):
        # --- FIX STARTS HERE ---
        # If title is None (missing), use the URL as the title
        if title is None:
            title = url
        # --- FIX ENDS HERE ---

        clean_title = title.replace('\n', ' ').strip()
        print(f"{i}. {clean_title}")
        print(f"   {url}")
        print("-" * 40)

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 search_engine.py <search_term>")
        sys.exit(1)

    search_term = " ".join(sys.argv[1:])
    search_db(search_term)