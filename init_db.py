import sqlite3

conn = sqlite3.connect("chat.db")
cur = conn.cursor()

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER,
    user2_id INTEGER
)
""")

# Seed users (only if empty)
cur.execute("SELECT COUNT(*) FROM users")
count = cur.fetchone()[0]

if count == 0:
    cur.execute("INSERT INTO users (username) VALUES ('Alice')")
    cur.execute("INSERT INTO users (username) VALUES ('Bob')")
    cur.execute("INSERT INTO users (username) VALUES ('Charlie')")

conn.commit()
conn.close()

print("Database initialized successfully!")