import sqlite3
import datetime
import time
import os
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
        
        # [NEW] FIFO Credit Ledger
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                amount_remaining REAL,
                source_type TEXT,
                created_at REAL
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_txs (
                tx_hash TEXT PRIMARY KEY,
                user_id TEXT,
                timestamp REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id TEXT PRIMARY KEY,
                expiry REAL,
                tier TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_daily_counts (
                user_id TEXT,
                day_timestamp REAL,
                scan_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, day_timestamp)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_reports (
                report_id TEXT PRIMARY KEY,
                report_hash TEXT,
                address TEXT,
                data TEXT,
                vera_score REAL,
                timestamp REAL,
                finder_id TEXT,
                is_first_finder INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                code TEXT PRIMARY KEY,
                owner_id TEXT,
                owner_ip_hash TEXT,
                owner_ua_hash TEXT,
                uses INTEGER DEFAULT 0,
                earned_credits INTEGER DEFAULT 0,
                is_flagged INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referral_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id TEXT,
                referee_id TEXT,
                timestamp REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referral_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                ip_hash TEXT,
                timestamp REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
                day_timestamp REAL PRIMARY KEY,
                volume_eth REAL DEFAULT 0,
                tx_count INTEGER DEFAULT 0
            )
        """)
        # [NEW] Founder Ledger (Settlements & Carry)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS founder_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                source TEXT, 
                timestamp REAL
            )
        """)

        # [NEW] Sheriff Rankings (Frontier)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sheriff_rankings (
                user_id TEXT PRIMARY KEY,
                total_verifications INTEGER DEFAULT 0,
                correct_verifications INTEGER DEFAULT 0,
                accumulated_yield REAL DEFAULT 0.0,
                last_active REAL
            )
        """)

        # [NEW] Synapse Migration (Neural Bridge)
        try:
             cursor.execute("ALTER TABLE audit_reports ADD COLUMN synapse_synced INTEGER DEFAULT 0")
        except:
             pass # Already exists

        # [NEW] Initial Suspicion — History of Suspicion (auto-scan persistence)
        try:
             cursor.execute("ALTER TABLE audit_reports ADD COLUMN initial_suspicion REAL DEFAULT NULL")
        except:
             pass
        try:
             cursor.execute("ALTER TABLE audit_reports ADD COLUMN initial_source TEXT DEFAULT NULL")
        except:
             pass
        try:
             cursor.execute("ALTER TABLE audit_reports ADD COLUMN initial_detected_at REAL DEFAULT NULL")
        except:
             pass

        # [NEW] Royalty Settlement (Sheriff's Revenue)
        try:
             cursor.execute("ALTER TABLE audit_reports ADD COLUMN royalty_claimed_eth REAL DEFAULT 0.0")
        except:
             pass

        # [NEW] Migration: Convert legacy credits to 'purchase' ledger entries
        # Check if users have credits but no ledger entries
        cursor.execute("SELECT user_id, credits FROM users WHERE credits > 0")
        users_with_credits = cursor.fetchall()
        
        for u in users_with_credits:
            uid, creds = u
            # Check ledger
            cursor.execute("SELECT 1 FROM credit_ledger WHERE user_id=?", (uid,))
            if not cursor.fetchone():
                print(f"Migrating {creds} credits for {uid} to Ledger (Purchase)")
                cursor.execute("INSERT INTO credit_ledger (user_id, amount_remaining, source_type, created_at) VALUES (?, ?, 'purchase', ?)", 
                               (uid, float(creds), time.time()))

        # [NEW] Treasury & Evolution Stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasury_stats (
                id INTEGER PRIMARY KEY,
                total_volume_eth REAL DEFAULT 0,
                chest_balance_eth REAL DEFAULT 0,
                war_chest_eth REAL DEFAULT 0,
                last_updated REAL
            )
        """)

        # Migration: Add neurons_active
        try:
             cursor.execute("ALTER TABLE treasury_stats ADD COLUMN neurons_active INTEGER DEFAULT 0")
        except:
             pass 
             
        # Migration: Add last_notebooklm_sync
        try:
             cursor.execute("ALTER TABLE treasury_stats ADD COLUMN last_notebooklm_sync REAL DEFAULT 0")
        except:
             pass 

        # Migration: Add contracts seen and scout leads
        try:
             cursor.execute("ALTER TABLE treasury_stats ADD COLUMN total_contracts_seen INTEGER DEFAULT 0")
        except:
             pass
        try:
             cursor.execute("ALTER TABLE treasury_stats ADD COLUMN scout_leads_generated INTEGER DEFAULT 0")
        except:
             pass

        # Ensure row 1 exists (now that columns are definitely there or it fails gracefully)
        try:
            cursor.execute("INSERT OR IGNORE INTO treasury_stats (id, total_volume_eth, chest_balance_eth, war_chest_eth, neurons_active, last_notebooklm_sync) VALUES (1, 0, 0, 0, 0, 0)")
        except:
            # Fallback if some columns are still missing for some reason
            cursor.execute("INSERT OR IGNORE INTO treasury_stats (id) VALUES (1)")

        conn.commit()

# --- SETTLEMENT & REVENUE HELPERS ---
def record_founder_carry(amount: float, source: str):
    """
    Records revenue into the Founder's private ledger.
    Source: 'settlement' (Expired Vouchers) or 'fee' (Purchase Carry).
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO founder_ledger (amount, source, timestamp) VALUES (?, ?, ?)", (amount, source, time.time()))
        conn.commit()

def expire_vouchers(cutoff_timestamp: float) -> float:
    """
    Expires all 'voucher' credits created before cutoff_timestamp.
    Returns the total remaining amount that was expired.
    """
    with get_db() as conn:
        c = conn.cursor()
        
        # 1. Find vouchers to expire
        c.execute("SELECT id, user_id, amount_remaining FROM credit_ledger WHERE source_type='voucher' AND created_at < ? AND amount_remaining > 0", (cutoff_timestamp,))
        rows = c.fetchall()
        
        if not rows:
            return 0.0
            
        total_expired = 0.0
        user_deductions = {} # user_id -> amount
        ledger_ids = []

        for r in rows:
            lid, uid, amt = r
            total_expired += amt
            user_deductions[uid] = user_deductions.get(uid, 0.0) + amt
            ledger_ids.append(lid)
            
        # 2. Update Users
        for uid, amt in user_deductions.items():
            c.execute("UPDATE users SET credits = credits - ? WHERE user_id=?", (amt, uid))
            
        # 3. Update Ledger (Expire them)
        # Use executemany or just a IN clause
        # SQLite limit on variables might be an issue for huge sets, but for now fine.
        if ledger_ids:
            placeholders = ','.join(['?'] * len(ledger_ids))
            c.execute(f"UPDATE credit_ledger SET amount_remaining = 0 WHERE id IN ({placeholders})", ledger_ids)
            
        conn.commit()
            
        return total_expired

def get_revenue_stats_24h():
    """
    Returns Founder Carry and Protocol Growth for last 24h.
    """
    cutoff = time.time() - 86400
    with get_db() as conn:
        c = conn.cursor()
        
        # Founder Carry (Last 24h)
        c.execute("SELECT SUM(amount) FROM founder_ledger WHERE timestamp > ?", (cutoff,))
        row = c.fetchone()
        carry_24h = row[0] if row and row[0] else 0.0
        
        # Protocol Growth (New Users? Volume?)
        # Let's say Volume ETH in last 24h
        c.execute("SELECT SUM(amount_eth) FROM verified_txs WHERE timestamp > ?", (cutoff,))
        row = c.fetchone()
        volume_24h = row[0] if row and row[0] else 0.0
        
        return {"founder_carry": carry_24h, "protocol_growth_eth": volume_24h}

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def db_add_credits(user_id: str, amount: int, tx_hash: str = None, source_type: str = 'purchase'):
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
        
        # [NEW] Add to Ledger
        c.execute("INSERT INTO credit_ledger (user_id, amount_remaining, source_type, created_at) VALUES (?, ?, ?, ?)",
                  (user_id, float(amount), source_type, time.time()))
        
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
        c.execute("DELETE FROM credit_ledger WHERE user_id=?", (user_id,)) # Clear ledger too
        conn.commit()

def wipeout_user(user_id: str):
    """
    DEBUG ONLY: Deletes ALL data for a user to simulate a fresh start.
    """
    with get_db() as conn:
        c = conn.cursor()
        # 1. Reset Credits
        c.execute("UPDATE users SET credits = 0 WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM credit_ledger WHERE user_id=?", (user_id,))
        
        # 2. Delete History & State
        c.execute("DELETE FROM verified_txs WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM processed_txs WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM scan_logs WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM subscriptions WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM scan_daily_counts WHERE user_id=?", (user_id,))
        
        # 3. Delete Audit Reports found by user
        c.execute("DELETE FROM audit_reports WHERE finder_id=?", (user_id,))
        
        # 4. Delete Referrals owned by user
        c.execute("DELETE FROM referrals WHERE owner_id=?", (user_id,))
        c.execute("DELETE FROM referral_claims WHERE referrer_id=? OR referee_id=?", (user_id, user_id))
        
        conn.commit()

def deduct_credits_fifo(user_id: str, amount: int) -> str:
    """
    Deducts credits using First-In-First-Out logic.
    Returns the 'primary_source' (the source of the majority of credits used).
    """
    with get_db() as conn:
        c = conn.cursor()
        
        # Check Total
        c.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if not row or row[0] < amount:
            raise ValueError("Insufficient funds")

        remaining_to_deduct = float(amount)
        sources_used = {} # type -> amount
        
        # Fetch active ledger entries ordered by time
        c.execute("SELECT id, amount_remaining, source_type FROM credit_ledger WHERE user_id=? AND amount_remaining > 0 ORDER BY created_at ASC", (user_id,))
        entries = c.fetchall()
        
        for entry in entries:
            eid, amt, src = entry
            
            deduct = min(amt, remaining_to_deduct)
            
            # Update Entry
            new_amt = amt - deduct
            c.execute("UPDATE credit_ledger SET amount_remaining = ? WHERE id=?", (new_amt, eid))
            
            # Track Source
            sources_used[src] = sources_used.get(src, 0) + deduct
            
            remaining_to_deduct -= deduct
            if remaining_to_deduct <= 0:
                break
        
        if remaining_to_deduct > 0:
             # Should not happen via the check above, but purely defensive
             pass

        # Update Aggregate
        c.execute("UPDATE users SET credits = credits - ? WHERE user_id=?", (amount, user_id))
        conn.commit()
        
        # Determine Primary Source
        if not sources_used:
            return "purchase" # Default fallback
            
        return max(sources_used, key=sources_used.get)

def use_credit(user_id: str) -> bool:
    # Deprecated/Wrapper for legacy calls
    try:
        deduct_credits_fifo(user_id, 1)
        return True
    except:
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
        """, (tx_hash, user_id, amount_eth, amount_usd, time.time()))
        conn.commit()

def tx_exists(tx_hash: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT 1 FROM verified_txs WHERE tx_hash = ?", (tx_hash,)).fetchone()
        return row is not None

def get_lifetime_spend_eth(user_id: str) -> float:
    """Returns total ETH spent by user."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT SUM(amount_eth) FROM verified_txs WHERE user_id=?", (user_id,))
        result = c.fetchone()[0]
        return result if result else 0.0

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
            
            # [NEW] Ledger Entry (Treat Referral as Voucher/Grant)
            c.execute("INSERT INTO credit_ledger (user_id, amount_remaining, source_type, created_at) VALUES (?, ?, 'voucher', ?)",
                      (referrer_id, float(reward), time.time()))
            
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
        try:
            c.execute("INSERT INTO audit_reports (report_id, report_hash, address, data, timestamp, vera_score, finder_id, is_first_finder) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (report_id, report_hash, address, data, time.time(), vera_score, user_id, is_first))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Silently skip duplicates

def save_initial_suspicion(address: str, score: float, source: str = "chain") -> bool:
    """
    Save the FIRST automatic suspicion score for an address (chain_listener / userbot).
    Only saves on first detection — subsequent calls for the same address are ignored.
    Returns True if this was the first detection, False if already recorded.
    """
    with get_db() as conn:
        c = conn.cursor()
        # Check if any report already has an initial_suspicion for this address
        c.execute(
            "SELECT 1 FROM audit_reports WHERE address=? AND initial_suspicion IS NOT NULL LIMIT 1",
            (address,),
        )
        if c.fetchone():
            return False  # Already recorded — don't overwrite first detection

        # Upsert: insert or update existing row for this address
        # Find existing row (any) to update, or create a sentinel row
        c.execute(
            "SELECT report_id FROM audit_reports WHERE address=? ORDER BY timestamp ASC LIMIT 1",
            (address,),
        )
        existing = c.fetchone()

        if existing:
            c.execute(
                "UPDATE audit_reports "
                "SET initial_suspicion=?, initial_source=?, initial_detected_at=? "
                "WHERE report_id=?",
                (score, source, time.time(), existing[0]),
            )
        else:
            # No prior report — insert a sentinel row so the info is persisted
            import uuid
            c.execute(
                "INSERT INTO audit_reports "
                "(report_id, report_hash, address, data, timestamp, vera_score, "
                " initial_suspicion, initial_source, initial_detected_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()), "", address, "{}",
                    time.time(), 0,
                    score, source, time.time(),
                ),
            )
        conn.commit()
        return True


def get_initial_suspicion(address: str) -> dict | None:
    """
    Returns the earliest recorded auto-scan suspicion for an address, or None.
    Shape: { score, source, detected_at }
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT initial_suspicion, initial_source, initial_detected_at "
            "FROM audit_reports "
            "WHERE address=? AND initial_suspicion IS NOT NULL "
            "ORDER BY initial_detected_at ASC LIMIT 1",
            (address,),
        )
        row = c.fetchone()
        if not row or row[0] is None:
            return None
        return {
            "score":       row[0],
            "source":      row[1] or "auto",
            "detected_at": row[2],
        }


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

def get_user_audit_history(user_id: str, limit: int = 5):
    """
    Returns last {limit} unique addresses scanned by the user.
    """
    with get_db() as conn:
        c = conn.cursor()
        # Get unique addresses, taking the most recent one for each
        query = """
            SELECT address, vera_score, MAX(timestamp) as last_scan, data
            FROM audit_reports
            WHERE finder_id = ?
            GROUP BY address
            ORDER BY last_scan DESC
            LIMIT ?
        """
        c.execute(query, (user_id, limit))
        rows = c.fetchall()

        results = []
        import json
        for r in rows:
            try:
                details = json.loads(r[3])
                is_proxy = details.get("is_proxy", False)
                
                # [Optimization] Return full display data for instant "View Report"
                warnings = details.get("warnings", [])
                milestones = details.get("milestones", [])
                vitals = details.get("vitals", None)
                risk_summary = details.get("risk_summary") 
                
                # [NEW] Premium Data Persistence
                red_team_log = details.get("red_team_log", [])
                report_hash = details.get("report_hash")
                logic_dna_seq = details.get("logic_dna_seq")
                cost_deducted = details.get("cost_deducted", 3) # [FIX] Default to 3 if missing
            except:
                scam_type = None
                is_proxy = False
                warnings = []
                milestones = []
                vitals = None
                risk_summary = None
                red_team_log = []
                report_hash = None
                logic_dna_seq = None
                cost_deducted = 3

            results.append({
                "address": r[0],
                "score": r[1],
                "timestamp": r[2],
                "scam_type": risk_summary,
                "is_proxy": is_proxy,
                "warnings": warnings,
                "milestones": milestones,
                "vitals": vitals,
                "risk_summary": risk_summary,
                "red_team_log": red_team_log, # [NEW]
                "report_hash": report_hash,   # [NEW]
                "logic_dna_seq": logic_dna_seq, # [NEW]
                "cost": cost_deducted # [NEW]
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

    return True


# --- HISTORY AGGREGATION ---
def get_user_history(user_id: str):
    """
    Aggregates:
    - Verified Txs (Purchases)
    - Audit Reports (Scans)
    - Referral Claims (Rewards)
    """
    history = []
    
    with get_db() as conn:
        c = conn.cursor()
        
        # 1. Purchases
        c.execute("SELECT tx_hash, amount_eth, amount_usd, timestamp FROM verified_txs WHERE user_id=?", (user_id,))
        for r in c.fetchall():
            history.append({
                "type": "purchase",
                "id": r[0], # tx_hash
                "amount_eth": r[1],
                "amount_usd": r[2],
                "timestamp": r[3],
                "description": "Credit Purchase"
            })
            
        # 2. Scans (Audits)
        # using report_id as id
        c.execute("SELECT report_id, address, vera_score, timestamp FROM audit_reports WHERE finder_id=?", (user_id,))
        for r in c.fetchall():
            history.append({
                "type": "audit",
                "id": r[0],
                "address": r[1],
                "score": r[2],
                "timestamp": r[3],
                "description": "Contract Scan"
            })
            
        # 3. Referral Rewards
        c.execute("SELECT referee_id, timestamp FROM referral_claims WHERE referrer_id=?", (user_id,))
        for r in c.fetchall():
             history.append({
                "type": "reward",
                "id": f"rew_{r[1]}_{r[0]}", 
                "referee": r[0],
                "timestamp": r[1],
                "description": "Referral Reward"
            })
            
    # Sort by timestamp DESC
    def parse_ts(ts):
        try:
            if isinstance(ts, (int, float)):
                return float(ts)
            # Handle string timestamps (datetime.now() stringified)
            # SQLite stores datetime as "YYYY-MM-DD HH:MM:SS.mmmmmm"
            import dateutil.parser
            dt = dateutil.parser.parse(str(ts))
            return dt.timestamp()
        except:
            return 0.0

    history.sort(key=lambda x: parse_ts(x['timestamp']), reverse=True)
    return history


# --- TREASURY & PRIZE HELPERS ---
def log_daily_volume(amount_eth: float):
    # normalize to midnight
    midnight = int(time.time() / 86400) * 86400
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO daily_metrics (day_timestamp, volume_eth, tx_count) VALUES (?, 0, 0)", (midnight,))
        c.execute("UPDATE daily_metrics SET volume_eth = volume_eth + ?, tx_count = tx_count + 1 WHERE day_timestamp=?", (amount_eth, midnight))
        
        # Update Global Treasury
        c.execute("UPDATE treasury_stats SET total_volume_eth = total_volume_eth + ?, chest_balance_eth = chest_balance_eth + ?, last_updated=?", (amount_eth, amount_eth, time.time()))
        conn.commit()

def get_treasury_stats():
    with get_db() as conn:
        c = conn.cursor()
        row = c.execute("SELECT total_volume_eth, chest_balance_eth, war_chest_eth FROM treasury_stats WHERE id=1").fetchone()
        return {"total_volume": row[0], "chest_balance": row[1], "war_chest": row[2]} if row else None

def get_daily_volumes(days: int = 30):
    with get_db() as conn:
        c = conn.cursor()
        cutoff = time.time() - (days * 86400)
        c.execute("SELECT day_timestamp, volume_eth FROM daily_metrics WHERE day_timestamp > ? ORDER BY day_timestamp DESC", (cutoff,))
        return [{"date": r[0], "volume": r[1]} for r in c.fetchall()]

def record_payout_round(round_id: str, merkle_root: str, total_payout: float, winners_count: int, metadata: dict):
    import json
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO payout_rounds (round_id, merkle_root, total_payout_eth, winners_count, metadata_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (round_id, merkle_root, total_payout, winners_count, json.dumps(metadata), time.time()))
        
        # Deduct from Chest
        c.execute("UPDATE treasury_stats SET chest_balance_eth = chest_balance_eth - ? WHERE id=1", (total_payout,))
        conn.commit()


# --- ANTI-FRAGILE HELPERS ---
def increment_daily_scan_count(user_id: str):
    midnight = int(time.time() / 86400) * 86400
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO scan_daily_counts (user_id, day_timestamp, scan_count) VALUES (?, ?, 0)", (user_id, midnight))
        c.execute("UPDATE scan_daily_counts SET scan_count = scan_count + 1 WHERE user_id=? AND day_timestamp=?", (user_id, midnight))
        conn.commit()

def get_daily_scan_count(user_id: str):
    midnight = int(time.time() / 86400) * 86400
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT scan_count FROM scan_daily_counts WHERE user_id=? AND day_timestamp=?", (user_id, midnight))
        row = c.fetchone()
        return row[0] if row else 0

def get_first_finder(address: str):
    """Returns user_id of the first finder for this address, if any."""
    with get_db() as conn:
        c = conn.cursor()
        # Find the earliest report for this address with vera_score < 50
        c.execute("SELECT finder_id FROM audit_reports WHERE address=? AND is_first_finder=1 ORDER BY timestamp ASC LIMIT 1", (address,))
        row = c.fetchone()
        return row[0] if row else None

def record_royalty_claim(report_id_or_address: str, finder_id: str, amount_eth: float):
    # We update the original report or user credits?
    # Actually simplest is to just give credits to the finder and log it.
    # We don't have a 'royalty_events' table, but we can update the 'audit_report' of the finder.
    with get_db() as conn:
        c = conn.cursor()
        # Award credits/ETH to finder
        c.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount_eth * 1000, finder_id)) # 1 ETH = 1000 Credits? Or just store ETH?
        
        # We need to track how much was claimed.
        # Find the original report by this finder for this address
        # logic: update audit_reports set royalty_claimed_eth += amount where address=? and finder_id=?
        c.execute("UPDATE audit_reports SET royalty_claimed_eth = royalty_claimed_eth + ? WHERE address=? AND finder_id=?", (amount_eth, report_id_or_address, finder_id))
        conn.commit()


# --- TELEGRAM & GHOST AGENT HELPERS ---
def create_otp(user_id: str):
    import secrets
    import time
    code = secrets.token_hex(3).upper() # 6 chars
    expiry = time.time() + 300 # 5 mins
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO otp_codes (code, user_id, expiry) VALUES (?, ?, ?)", (code, user_id, expiry))
        conn.commit()
    return code

def verify_and_link_telegram(otp_code: str, telegram_id: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, expiry FROM otp_codes WHERE code=?", (otp_code,))
        row = c.fetchone()
        
        if not row:
            return False, "Invalid Code"
        
        user_id, expiry = row
        if time.time() > expiry:
            return False, "Code Expired"
            
        # Link
        c.execute("UPDATE users SET telegram_id=? WHERE user_id=?", (telegram_id, user_id))
        # Cleanup
        c.execute("DELETE FROM otp_codes WHERE code=?", (otp_code,))
        conn.commit()
        return True, user_id

def get_telegram_user(telegram_id: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, credits FROM users WHERE telegram_id=?", (telegram_id,))
        row = c.fetchone()
        return row if row else None

def get_pending_public_alerts():
    with get_db() as conn:
        c = conn.cursor()
        # Find reports with Score < 50 that haven't been alerted
        c.execute("SELECT report_id, address, vera_score, data FROM audit_reports WHERE vera_score < 50 AND is_public_alert_sent=0")
        return c.fetchall()

def mark_alert_sent(report_id: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE audit_reports SET is_public_alert_sent=1 WHERE report_id=?", (report_id,))
        conn.commit()

def get_pending_syncs():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT report_id, report_hash, address, data FROM audit_reports WHERE is_drive_synced=0")
        return c.fetchall()

def mark_synced(report_id: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE audit_reports SET is_drive_synced=1 WHERE report_id=?", (report_id,))
        conn.commit()


def get_executive_stats():
    """
    Returns high-level metrics for the Founder Dashboard.
    """
    with get_db() as conn:
        c = conn.cursor()
        
        # 1. Total Carry
        # (Check if table exists first? It should.)
        try:
            c.execute("SELECT SUM(amount) FROM founder_ledger")
            row = c.fetchone()
            total_carry = row[0] if row and row[0] else 0.0
        except:
            total_carry = 0.0
        
        # 2. Active Voucher Liability (Workforce Liquidity Pool Base)
        c.execute("SELECT SUM(amount_remaining) FROM credit_ledger WHERE source_type='voucher'")
        row = c.fetchone()
        active_vouchers = row[0] if row and row[0] else 0.0

        # ── Intelligence Discovery Staging Count ──────────────────────────
        staged_sigs = 0
        staging_file = os.path.join("NotebookLM", "SIGNATURE_CANDIDATES.md")
        if os.path.exists(staging_file):
            try:
                with open(staging_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    staged_sigs = content.count("## [New Signature Candidate]")
            except:
                staged_sigs = 0
        
        # 3. Vault Balance, Neurons, and Efficiency
        try:
            c.execute("SELECT chest_balance_eth, neurons_active, total_contracts_seen, scout_leads_generated FROM treasury_stats WHERE id=1")
        except sqlite3.OperationalError:
            # Fallback if migration hasn't run yet in a concurrent scenario
            return {
                "total_carry_usd": total_carry,
                "active_vouchers_usd": active_vouchers,
                "vault_balance_eth": 0.0,
                "neurons_active": 0,
                "efficiency_rate": 0.0,
                "staged_signatures": staged_sigs
            }

        row = c.fetchone()
        vault_balance = row[0] if row and row[0] else 0.0
        neurons_active = row[1] if row and row[1] else 0
        seen = len(row) > 2 and row[2] and row[2] or 0
        leads = len(row) > 3 and row[3] and row[3] or 0
        
        return {
            "total_carry_usd": total_carry,
            "active_vouchers_usd": active_vouchers,
            "vault_balance_eth": vault_balance,
            "neurons_active": neurons_active,
            "efficiency_rate": (leads / seen * 100) if seen > 0 else 0.0,
            "staged_signatures": staged_sigs
        }

def increment_contracts_seen():
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute("UPDATE treasury_stats SET total_contracts_seen = total_contracts_seen + 1 WHERE id=1")
            conn.commit()
        except sqlite3.OperationalError:
            pass

def increment_scout_leads():
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute("UPDATE treasury_stats SET scout_leads_generated = scout_leads_generated + 1 WHERE id=1")
            conn.commit()
        except sqlite3.OperationalError:
            pass

# --- NEURAL BRIDGE (SYNAPSE) HELPER ---
def get_pending_synapse_syncs():
    """Returns reports that need to be pushed to the Neural Bridge (The Vault)."""
    with get_db() as conn:
        c = conn.cursor()
        # Only sync BUSTS (Score < 50) or high-value findings
        c.execute("SELECT report_id, report_hash, address, data, vera_score FROM audit_reports WHERE synapse_synced=0 AND vera_score < 50")
        return c.fetchall()

def mark_synapse_synced(report_id: str):
    # Logic: When a report is synced to Synapse, it's a new 'Neuron' in the brain.
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE audit_reports SET synapse_synced=1 WHERE report_id=?", (report_id,))
        conn.commit()

def increment_neurons_active():
    """Increments the global Neurons Active counter."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE treasury_stats SET neurons_active = neurons_active + 1, last_updated = ? WHERE id=1", (time.time(),))
        conn.commit()

def get_top_neurons_weekly(limit: int = 3):
    """Returns the top 3 newest exploit patterns from the last 7 days."""
    cutoff = time.time() - (7 * 86400)
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT address, vera_score, data, timestamp 
            FROM audit_reports 
            WHERE vera_score < 50 AND timestamp > ? 
            ORDER BY timestamp DESC LIMIT ?
        """, (cutoff, limit))
        rows = c.fetchall()
        
        results = []
        import json
        for r in rows:
            try:
                details = json.loads(r[2])
                exploit = details.get("risk_summary", "Unknown Exploit")
            except:
                exploit = "Unknown Exploit"
            
            results.append({
                "address": r[0],
                "score": r[1],
                "exploit": exploit,
                "timestamp": r[3]
            })
        return results

def get_brain_lag():
    """Returns the count of neurons synced to Drive but not yet in NotebookLM."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT last_notebooklm_sync FROM treasury_stats WHERE id=1")
        row = c.fetchone()
        last_sync = row[0] if row else 0
        
        c.execute("SELECT COUNT(*) FROM audit_reports WHERE synapse_synced=1 AND vera_score < 50 AND timestamp > ?", (last_sync,))
        return c.fetchone()[0]

def mark_brain_synced():
    """Sets the last known NotebookLM sync time to now."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE treasury_stats SET last_notebooklm_sync = ?, last_updated = ? WHERE id=1", (time.time(), time.time()))
        conn.commit()

