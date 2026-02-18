import sqlite3
import datetime
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
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def add_credit(user_id: str, amount: int = 1):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, credits) 
            VALUES (?, ?) 
            ON CONFLICT(user_id) DO UPDATE SET credits = credits + ?
        """, (user_id, amount, amount))
        conn.commit()

def get_credits(user_id: str) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row[0] if row else 0

def use_credit(user_id: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        current = get_credits(user_id)
        if current > 0:
            cursor.execute("UPDATE users SET credits = credits - 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            return True
        return False

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
