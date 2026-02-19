import requests
import json
import time
import os
import sys

# Ensure we can import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core import database, settlement_worker

USER_ID = "test_settlement_user"

def print_step(msg):
    print(f"\n[STEP] {msg}")

def verify():
    # 0. Initialize DB
    print_step("Initializing DB...")
    database.init_db()

    # 1. Reset User
    print_step("Resetting User State...")
    database.wipeout_user(USER_ID)

    # 2. Add Old Vouchers (Backdate creation time)
    print_step("Adding Old Vouchers...")
    # Manually insert to control timestamp
    old_ts = time.time() - (60 * 86400) # 60 days ago
    with database.get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (user_id, credits) VALUES (?, 100)", (USER_ID,))
        c.execute("INSERT INTO credit_ledger (user_id, amount_remaining, source_type, created_at) VALUES (?, 100, 'voucher', ?)", (USER_ID, old_ts))
        conn.commit()

    print(f"User Credits: {database.get_credits(USER_ID)}")

    # 3. Run Settlement
    print_step("Running Settlement Worker...")
    settlement_worker.run_settlement()

    # 4. Verify Expiration
    print_step("Verifying Expiration...")
    creds = database.get_credits(USER_ID)
    print(f"User Credits after Settlement: {creds}")
    
    if creds == 0:
        print("PASSED: Credits expired.")
    else:
        print(f"FAILED: Credits remaining: {creds}")

    # 5. Verify Founder Ledger
    print_step("Verifying Founder Ledger...")
    stats = database.get_revenue_stats_24h()
    print(f"Revenue Stats: {stats}")
    
    # Expected Carry: 100 * 0.40 = 40.0
    if stats['founder_carry'] >= 40.0:
        print("PASSED: Founder Carry recorded.")
    else:
        print(f"FAILED: Founder Carry missing or incorrect: {stats['founder_carry']}")

if __name__ == "__main__":
    verify()
