import sqlite3
import datetime
import time
from contextlib import contextmanager

DB_PATH = "credits.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                credits INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verified_txs (
                tx_hash TEXT PRIMARY KEY,
                user_id TEXT,
                amount_eth REAL,
                timestamp DATETIME
            )
        """)
        # New tables for Rate Limiting & Double-Spend
        cursor.execute('''CREATE TABLE IF NOT EXISTS processed_txs
                 (tx_hash TEXT PRIMARY KEY, user_id TEXT, timestamp REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS scan_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, timestamp REAL)''')
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def db_add_credits(user_id: str, amount: int, tx_hash: str = None):
    with get_db() as conn:
        c = conn.cursor()
        
        # Double-Spend Check
        if tx_hash:
            c.execute("SELECT tx_hash FROM processed_txs WHERE tx_hash=?", (tx_hash,))
            if c.fetchone():
                raise ValueError("Double-Spend Detected: Transaction already processed.")
            
            c.execute("INSERT INTO processed_txs (tx_hash, user_id, timestamp) VALUES (?, ?, ?)", 
                      (tx_hash, user_id, time.time()))

        c.execute("INSERT OR IGNORE INTO users (user_id, credits) VALUES (?, 0)", (user_id,))
        c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, user_id))
        conn.commit()

def get_credits(user_id: str) -> int:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        return row[0] if row else 0

def use_credit(user_id: str) -> bool:
    current = get_credits(user_id)
    if current > 0:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET credits = credits - 1 WHERE user_id=?", (user_id,))
            conn.commit()
            return True
    return False

def check_rate_limit(user_id: str, limit: int = 3, window_seconds: int = 86400) -> bool:
    """Returns True if user is within rate limit (Free Tier)."""
    with get_db() as conn:
        c = conn.cursor()
        cutoff = time.time() - window_seconds
        c.execute("SELECT COUNT(*) FROM scan_logs WHERE user_id=? AND timestamp > ?", (user_id, cutoff))
        count = c.fetchone()[0]
        return count < limit

def log_scan_attempt(user_id: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO scan_logs (user_id, timestamp) VALUES (?, ?)", (user_id, time.time()))
        conn.commit()

def record_tx(tx_hash: str, user_id: str, amount: float):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO verified_txs (tx_hash, user_id, amount_eth, timestamp)
            VALUES (?, ?, ?, ?)
        """, (tx_hash, user_id, amount, datetime.datetime.now()))
        conn.commit()

def tx_exists(tx_hash: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT 1 FROM verified_txs WHERE tx_hash = ?", (tx_hash,)).fetchone()
        return row is not None

def tx_exists(tx_hash: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT 1 FROM verified_txs WHERE tx_hash = ?", (tx_hash,)).fetchone()
        return row is not None
