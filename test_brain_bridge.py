import os
import sys
import time
import datetime
import random
from dotenv import load_dotenv

# Ensure we can import from core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import database as db
from core.synapse_worker import VAULT_PATH, DIGEST_FILENAME

def test_brain_bridge():
    load_dotenv()
    db.init_db()
    
    print("\n=== E2E BRAIN BRIDGE TEST ===\n")
    
    # 1. Trigger a synthetic "Bust"
    test_address = f"0xTEST_{random.getrandbits(32):08x}"
    test_report_id = f"TEST_REPORT_{int(time.time())}"
    
    print(f"[1/4] Triggering synthetic Bust for {test_address}...")
    
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO audit_reports (report_id, report_hash, address, data, vera_score, timestamp, synapse_synced)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            test_report_id,
            "TEST_HASH_123",
            test_address,
            '{"exploit_vector": "Neural Bridge Verification", "notes": "This is a test to verify the connection between VeraGuard and NotebookLM."}',
            10, # BUST score (< 50)
            datetime.datetime.now().isoformat(),
            0 # Not synced yet
        ))
        conn.commit()
    
    print(f"      OK: Synthetic report created (ID: {test_report_id})")
    
    # 2. Wait for Synapse Worker
    print(f"[2/4] Waiting for synapse_worker to process (polling every 5s)...")
    max_wait = 20
    start_time = time.time()
    packet_path = None
    
    while time.time() - start_time < max_wait:
        # Check if synced in DB
        with db.get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT synapse_synced FROM audit_reports WHERE report_id=?", (test_report_id,))
            if c.fetchone()[0] == 1:
                # Find the packet
                for f in os.listdir(VAULT_PATH):
                    if test_report_id[-6:] in f:
                        packet_path = os.path.join(VAULT_PATH, f)
                        break
                break
        time.sleep(2)
    
    if packet_path:
        print(f"      SUCCESS: Neuron Packet generated at {packet_path}")
    else:
        print(f"      FAIL: Synapse worker did not process the report within {max_wait}s.")
        print("      (Make sure python -m core.synapse_worker is running!)")
        return

    # 3. Verify Local Digest
    print(f"[3/4] Checking local Brain_Digest.md...")
    digest_path = os.path.join("NotebookLM", DIGEST_FILENAME)
    if os.path.exists(digest_path):
        with open(digest_path, "r", encoding="utf-8") as f:
            content = f.read()
            if test_address in content:
                print(f"      SUCCESS: {test_address} exists in local digest.")
            else:
                print(f"      FAIL: {test_address} not found in local digest content.")
    else:
        print(f"      FAIL: {digest_path} not found.")

    # 4. Success Instructions
    print(f"\n[4/4] NEXT STEPS (Manual Verification):")
    print(f"  1. Go to Google Drive and check 'The_Vault' folder.")
    print(f"  2. Verify 'Brain_Digest.md' was updated just now.")
    print(f"  3. Open NotebookLM.")
    print(f"  4. Re-upload Brain_Digest.md from Drive.")
    print(f"  5. Ask the AI: 'Explain the exploit found at {test_address}'.")
    print(f"\n✅ If the AI accurately explains the 'Neural Bridge Verification' test, your Brain is CONNECTED.")

if __name__ == "__main__":
    test_brain_bridge()
