import sqlite3
from datetime import datetime
import json
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
            is_active BOOLEAN DEFAULT 0
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

    # Table 3: oauth_tokens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oauth_tokens (
            email TEXT PRIMARY KEY,
            token_data TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()

def save_oauth_token(email, token_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT OR REPLACE INTO oauth_tokens (email, token_data, updated_at)
           VALUES (?, ?, CURRENT_TIMESTAMP)''',
        (email, token_data)
    )
    conn.commit()
    conn.close()


def get_oauth_token(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT token_data FROM oauth_tokens WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    return row['token_data'] if row else None
