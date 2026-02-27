import sqlite3

# Connect to the file
conn = sqlite3.connect('iyte_data.db')
cursor = conn.cursor()

# Count the rows
cursor.execute("SELECT count(*) FROM pages")
total_pages = cursor.fetchone()[0]

print(f"Total Pages Scraped: {total_pages}")

conn.close()