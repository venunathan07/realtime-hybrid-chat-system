"""
Run this ONCE to add the new columns to your existing chat.db
Run with: python migrate.py
"""

import sqlite3
import os

DB_PATH = "chat.db"  # adjust path if needed

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ {DB_PATH} not found. Make sure you run this from your project root.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Add email to users table
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        print("✅ Added 'email' column to users")
    except sqlite3.OperationalError as e:
        print(f"ℹ️  users.email: {e}")

    # Add timestamp to messages table
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN timestamp DATETIME")
        print("✅ Added 'timestamp' column to messages")
    except sqlite3.OperationalError as e:
        print(f"ℹ️  messages.timestamp: {e}")

    conn.commit()
    conn.close()
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate()