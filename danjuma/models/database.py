import sqlite3
from datetime import datetime
import os

# Get DB path from environment variable or use default
DB_PATH = os.environ.get('DATABASE_URL', 'sqlite:///danjuma.db').replace('sqlite:///', '')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table 1: registered_emails
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registered_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')

    # Table 2: scan_history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registered_email TEXT NOT NULL,
            sender_email TEXT NOT NULL,
            file_name TEXT NOT NULL,
            verdict TEXT NOT NULL,
            malicious_count INTEGER DEFAULT 0,
            suspicious_count INTEGER DEFAULT 0,
            virustotal_link TEXT,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
