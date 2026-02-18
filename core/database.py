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
                amount_usd REAL, 
                timestamp DATETIME
            )
        """)
        
        # New tables for Rate Limiting & Double-Spend
        cursor.execute('''CREATE TABLE IF NOT EXISTS processed_txs
                 (tx_hash TEXT PRIMARY KEY, user_id TEXT, timestamp REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS scan_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, timestamp REAL)''')
        
        # [NEW] Hybrid Revenue & Referrals
        cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                 (user_id TEXT PRIMARY KEY, expiry REAL, tier TEXT DEFAULT 'standard')''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS referrals
                 (code TEXT PRIMARY KEY, owner_id TEXT, owner_ip_hash TEXT, owner_ua_hash TEXT, uses INTEGER DEFAULT 0, earned_credits INTEGER DEFAULT 0)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS referral_claims
                 (referrer_id TEXT, referee_id TEXT, timestamp REAL, PRIMARY KEY (referrer_id, referee_id))''')

        # [NEW] Ethical Watermarking & Anti-Spam
        cursor.execute('''CREATE TABLE IF NOT EXISTS audit_reports
                 (report_id TEXT PRIMARY KEY, report_hash TEXT, address TEXT, data TEXT, timestamp REAL)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS referral_events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, ip_hash TEXT, timestamp REAL)''')
          
        # Update Referrals with flagging
        try:
            cursor.execute("ALTER TABLE referrals ADD COLUMN is_flagged BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Migrations (idempotent)
        try:
            cursor.execute("ALTER TABLE verified_txs ADD COLUMN amount_usd REAL")
        except sqlite3.OperationalError:
            pass # Column likely exists
        
        try:
            cursor.execute("ALTER TABLE referrals ADD COLUMN owner_ua_hash TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE audit_reports ADD COLUMN vera_score INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE audit_reports ADD COLUMN finder_id TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE audit_reports ADD COLUMN is_first_finder INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

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

def reset_credits(user_id: str):
    """
    DEBUG ONLY: Resets user credits to 0.
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET credits = 0 WHERE user_id=?", (user_id,))
        conn.commit()

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

def record_tx(tx_hash: str, user_id: str, amount_eth: float, amount_usd: float = 0.0):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO verified_txs (tx_hash, user_id, amount_eth, amount_usd, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (tx_hash, user_id, amount_eth, amount_usd, datetime.datetime.now()))
        conn.commit()

def tx_exists(tx_hash: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT 1 FROM verified_txs WHERE tx_hash = ?", (tx_hash,)).fetchone()
        return row is not None

def get_lifetime_spend(user_id: str) -> float:
    """Returns total USD spent by user."""
    with get_db() as conn:
        c = conn.cursor()
        # Sum amount_usd. If NULL (legacy), we ignore or could estimate.
        c.execute("SELECT SUM(amount_usd) FROM verified_txs WHERE user_id=?", (user_id,))
        result = c.fetchone()[0]
        return result if result else 0.0

# --- SUBSCRIPTION HELPERS ---
def get_subscription_status(user_id: str):
    """Returns expiry timestamp if active, else None."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT expiry FROM subscriptions WHERE user_id=? AND expiry > ?", (user_id, time.time()))
        row = c.fetchone()
        return row[0] if row else None

def activate_subscription(user_id: str, duration_days: int = 30):
    expiry = time.time() + (duration_days * 86400)
    with get_db() as conn:
        c = conn.cursor()
        # Upsert: Extend if exists? For simplicity, just set new expiry or max(old, new)
        c.execute("INSERT OR REPLACE INTO subscriptions (user_id, expiry, tier) VALUES (?, ?, 'vera_pass')", (user_id, expiry))
        conn.commit()

# --- REFERRAL HELPERS ---
def create_referral_code(user_id: str, ip_hash: str, ua_hash: str):
    import secrets
    code = "VERA-" + secrets.token_hex(3).upper()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO referrals (code, owner_id, owner_ip_hash, owner_ua_hash) VALUES (?, ?, ?, ?)", (code, user_id, ip_hash, ua_hash))
        conn.commit()
    return code

def get_referral_code(user_id: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT code FROM referrals WHERE owner_id=?", (user_id,))
        row = c.fetchone()
        return row[0] if row else None

def validate_referral(code: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT owner_id, owner_ip_hash, owner_ua_hash FROM referrals WHERE code=?", (code,))
        return c.fetchone()

def processing_referral_reward(referrer_id: str, referee_id: str, reward: int = 5):
    with get_db() as conn:
        c = conn.cursor()
        # Prevent double claiming
        try:
            c.execute("INSERT INTO referral_claims (referrer_id, referee_id, timestamp) VALUES (?, ?, ?)", (referrer_id, referee_id, time.time()))
            # Award credits
            c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (reward, referrer_id))
            c.execute("UPDATE referrals SET uses = uses + 1, earned_credits = earned_credits + ? WHERE owner_id=?", (reward, referrer_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

# --- AUDIT REPORT HELPERS ---
def save_audit_report(report_id: str, report_hash: str, address: str, data: str, vera_score: int, user_id: str = None):
    is_first = 0
    # Logic: If Score < 50 AND no previous report for this address has Score < 50, then it's a First Find.
    if vera_score < 50 and user_id:
         with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM audit_reports WHERE address=? AND vera_score < 50", (address,))
            if not c.fetchone():
                is_first = 1

    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO audit_reports (report_id, report_hash, address, data, timestamp, vera_score, finder_id, is_first_finder) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (report_id, report_hash, address, data, time.time(), vera_score, user_id, is_first))
        conn.commit()

def get_audit_report(report_id: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT data FROM audit_reports WHERE report_id=?", (report_id,))
        row = c.fetchone()
        return row[0] if row else None

def get_wall_of_shame(limit: int = 5):
    """
    Returns last {limit} reports where vera_score < 50.
    """
    with get_db() as conn:
        c = conn.cursor()
        # [UPDATED] Added finder_id to query
        c.execute("SELECT address, vera_score, timestamp, data, report_id, finder_id FROM audit_reports WHERE vera_score < 50 ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        
        results = []
        import json
        for r in rows:
            try:
                details = json.loads(r[3])
                scam_type = details.get("risk_summary", "Unknown Vulnerability")
            except:
                scam_type = "Unknown Vulnerability"
            
            # Shorten finder_id for UI
            finder_display = "Unknown"
            if r[5]:
                 f_id = str(r[5])
                 finder_display = f_id[:4] + "..." + f_id[-3:] if len(f_id) > 8 else f_id

            results.append({
                "address": r[0],
                "score": r[1],
                "timestamp": r[2],
                "scam_type": scam_type,
                "report_id": r[4],
                "finder_display": finder_display
            })
        return results

def get_leaderboard(limit: int = 10):
    """
    Rank users by Sheriff Score = ((Referral Credits) + (First Finds * 50)) * Multiplier.
    Multiplier = 1.5x if Active Subscriber.
    """
    with get_db() as conn:
        c = conn.cursor()
        
        # 1. Get Referral Stats
        c.execute("SELECT owner_id, earned_credits, uses FROM referrals")
        ref_rows = c.fetchall()
        
        # 2. Get First Finder Stats
        c.execute("SELECT finder_id, COUNT(*) FROM audit_reports WHERE is_first_finder=1 GROUP BY finder_id")
        find_rows = c.fetchall() # [(user_id, count), ...]
        
        # 3. Get Active Subscriptions (Members)
        import time
        c.execute("SELECT user_id FROM subscriptions WHERE expiry > ?", (time.time(),))
        member_rows = c.fetchall()
        members = set([m[0] for m in member_rows])

        # Map stats
        stats = {} # user_id -> { referrals: 0, credits: 0, first_finds: 0, is_member: False }
        
        for r in ref_rows:
            uid = r[0]
            if uid not in stats: stats[uid] = { "referrals": 0, "credits": 0, "first_finds": 0, "is_member": False }
            stats[uid]["credits"] = r[1]
            stats[uid]["referrals"] = r[2]

        for r in find_rows:
            uid = r[0]
            if uid: # filter None
                if uid not in stats: stats[uid] = { "referrals": 0, "credits": 0, "first_finds": 0, "is_member": False }
                stats[uid]["first_finds"] = r[1]
        
        # Apply Membership
        for uid in stats:
            if uid in members:
                stats[uid]["is_member"] = True

        # Calculate Scores & Sort
        leaderboard = []
        for uid, s in stats.items():
            base_score = s["credits"] + (s["first_finds"] * 50)
            multiplier = 1.5 if s["is_member"] else 1.0
            sheriff_score = int(base_score * multiplier)
            
            # Simple obfuscation
            display_name = str(uid)[:4] + "..." + str(uid)[-3:] if len(str(uid)) > 8 else str(uid)
            
            leaderboard.append({
                "user_id": display_name,
                "sheriff_score": sheriff_score,
                "first_finds": s["first_finds"],
                "referrals": s["referrals"],
                "is_member": s["is_member"]
            })
            
        # Sort by Sheriff Score DESC
        leaderboard.sort(key=lambda x: x["sheriff_score"], reverse=True)
        
        return leaderboard[:limit]

# --- ANTI-SPAM VELOCITY ---
def log_referral_click(code: str, ip_hash: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO referral_events (code, ip_hash, timestamp) VALUES (?, ?, ?)", (code, ip_hash, time.time()))
        conn.commit()

def check_referral_velocity(code: str, limit: int = 100, window_seconds: int = 86400) -> bool:
    """Returns True if referral code is SAFE (under limit), False if FLAGGED."""
    # 1. Check if already flagged
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT is_flagged FROM referrals WHERE code=?", (code,))
        row = c.fetchone()
        if row and row[0]: # If is_flagged is 1 (True)
            return False

    # 2. Check velocity (Unique IPs in window)
    cutoff = time.time() - window_seconds
    with get_db() as conn:
        c = conn.cursor()
        # Count unique IPs for this code in the last 24h
        c.execute("SELECT COUNT(DISTINCT ip_hash) FROM referral_events WHERE code=? AND timestamp > ?", (code, cutoff))
        count = c.fetchone()[0]
        
        if count > limit:
            # Auto-Flag
            c.execute("UPDATE referrals SET is_flagged=1 WHERE code=?", (code,))
            conn.commit()
            return False
            
    return True

