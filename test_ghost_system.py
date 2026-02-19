import os
import json
import time
import shutil
from unittest.mock import MagicMock
from core import database as db
from core import ghost_worker

# Setup Test Environment
TEST_USER = "ghost_tester"
TEST_REPORT_ID = "report_ghost_001"
TEST_ADDR = "0xGhostContract"

def setup():
    print("--- Setting up Test Environment ---")
    if os.path.exists("NotebookLM_Inbox"):
        shutil.rmtree("NotebookLM_Inbox")
    if os.path.exists("NotebookLM_Synced"):
        shutil.rmtree("NotebookLM_Synced")
    
    os.makedirs("NotebookLM_Inbox")
    
    # Create a dummy certificate
    with open(f"NotebookLM_Inbox/Certificate_{TEST_REPORT_ID}.json", "w") as f:
        f.write('{"test": "certificate"}')

    # Reset DB state for test
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM audit_reports WHERE report_id=?", (TEST_REPORT_ID,))
        c.execute("DELETE FROM otp_codes WHERE user_id=?", (TEST_USER,))
        conn.commit()

def test_otp_flow():
    print("\n--- Testing OTP Flow ---")
    code = db.create_otp(TEST_USER)
    print(f"Generated OTP: {code}")
    
    # Verify in DB
    with db.get_db() as conn:
        row = conn.execute("SELECT code FROM otp_codes WHERE user_id=?", (TEST_USER,)).fetchone()
        if row and row[0] == code:
            print("✅ OTP Saved to DB")
        else:
            print("❌ OTP Save Failed")
            return

    # Verify Linking (Mock)
    success, msg = db.verify_and_link_telegram(code, "12345_TG")
    if success:
        print("✅ Telegram Linked Successfully")
    else:
        print(f"❌ Link Failed: {msg}")

    # Check User Config
    with db.get_db() as conn:
        row = conn.execute("SELECT telegram_id FROM users WHERE user_id=?", (TEST_USER,)).fetchone()
        if row and row[0] == "12345_TG":
            print("✅ User Telegram ID Updated")
        else:
             print("❌ User Telegram ID Mismatch")

def test_ghost_worker_flow():
    print("\n--- Testing Ghost Worker Flow ---")
    
    # 1. Insert Vulnerable Report
    data = json.dumps({"risk_summary": "Critical Exploit"})
    # Save directly to bypass audit logic
    with db.get_db() as conn:
        conn.execute("INSERT INTO audit_reports (report_id, report_hash, address, data, timestamp, vera_score, finder_id, is_public_alert_sent, is_drive_synced) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)",
                     (TEST_REPORT_ID, "hash123", TEST_ADDR, data, time.time(), 20, TEST_USER))
        conn.commit()
    
    # 2. Mock Network Calls
    ghost_worker.send_telegram_alert = MagicMock(return_value=True)
    
    # 3. Run Worker Logic (One Pass)
    print("Running Ghost Logic (Single Pass)...")
    
    # Alerts
    pending_alerts = db.get_pending_public_alerts()
    print(f"Pending Alerts Found: {len(pending_alerts)}")
    
    for r in pending_alerts:
        msg = ghost_worker.format_alert_message(r)
        if ghost_worker.send_telegram_alert(msg):
             db.mark_alert_sent(r[0])
             print("Alert Marked Sent.")

    # Syncs
    pending_syncs = db.get_pending_syncs()
    print(f"Pending Syncs Found: {len(pending_syncs)}")
    
    for r in pending_syncs:
        if ghost_worker.sync_to_notebook_lm(r):
            db.mark_synced(r[0])
            print("Sync Marked Complete.")

    # 4. Assertions
    with db.get_db() as conn:
        row = conn.execute("SELECT is_public_alert_sent, is_drive_synced FROM audit_reports WHERE report_id=?", (TEST_REPORT_ID,)).fetchone()
        alert_sent = row[0]
        drive_synced = row[1]
    
    if alert_sent:
        print("✅ Alert Sent Flag Set")
    else:
        print("❌ Alert Sent Flag Missing")
        
    if drive_synced:
        print("✅ Drive Synced Flag Set")
    else:
        print("❌ Drive Synced Flag Missing")
        
    if os.path.exists(f"NotebookLM_Synced/Certificate_{TEST_REPORT_ID}.json"):
        print("✅ Certificate File Moved to Synced Folder")
    else:
        print("❌ Certificate File Not Found in Synced Folder")

if __name__ == "__main__":
    setup()
    test_otp_flow()
    test_ghost_worker_flow()
