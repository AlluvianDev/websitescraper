import sqlite3
import json
import ollama
import os
import time

os.nice(19)

def backfill():
    conn = sqlite3.connect('iyte_data.db')
    cursor = conn.cursor()
    
    while True:
        cursor.execute("SELECT id, content FROM pages WHERE summary IS NULL LIMIT 1")
        row = cursor.fetchone()
        
        if not row:
            print("All rows have been summarized!")
            break
            
        row_id, content = row
        print(f"Processing ID: {row_id}...")
        
        try:
            prompt = f"Summarize this university webpage in one short sentence and provide 3 keywords. Format as JSON: {content[:2000]}"
            response = ollama.generate(model="llama3.2:1b", prompt=prompt, format="json")
            data = json.loads(response['response'])
            
            cursor.execute(
                "UPDATE pages SET summary = ?, keywords = ? WHERE id = ?",
                (data.get('summary'), json.dumps(data.get('keywords')), row_id)
            )
            conn.commit()
            
        except Exception as e:
            print(f"Error on ID {row_id}: {e}")
            time.sleep(5)
            
        time.sleep(1)

    conn.close()

if __name__ == "__main__":
    backfill()