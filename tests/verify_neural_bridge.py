"""
Verify Neural Bridge (Autonomous CNS)
1. Simulate a 'Bust' (Audit Score < 50).
2. Trigger Synapse Worker -> Check for Neuron Packet.
3. Trigger Brain Monitor -> Check for FAQ Update.
"""
import sys
import os
import json
import time
import sqlite3

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import database as db
from core import synapse_worker
from core import brain_monitor

DB_PATH = "credits.db"
VAULT_PATH = os.path.join("NotebookLM", "The_Vault")
FAQ_PATH = "Sovereign_FAQ.md"

def setup_mock_bust():
    print("[TEST] Setting up Mock Bust...")
    report_id = f"test_bust_{int(time.time())}"
    address = "0xDEADBEEF_NEURAL_TEST"
    data = json.dumps({
        "risk_summary": "Recursive Reentrancy", 
        "vitals": {"complexity": "High"}
    })
    
    # Insert directly into DB
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Ensure user exists
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES ('tester')")
        # Insert Bust
        c.execute("""
            INSERT INTO audit_reports (report_id, report_hash, address, data, timestamp, vera_score, finder_id, synapse_synced)
            VALUES (?, 'hash123', ?, ?, ?, 20, 'tester', 0)
        """, (report_id, address, data, time.time()))
        conn.commit()
    return report_id

def verify_synapse():
    print("[TEST] Running Synapse Worker...")
    # 1. Check pending
    pending = db.get_pending_synapse_syncs()
    print(f"[TEST] Pending Syncs: {len(pending)}")
    
    found_target = False
    for r in pending:
        if "0xDEADBEEF" in r[2]:
            found_target = True
            packet = synapse_worker.generate_neuron_packet(r)
            synapse_worker.push_to_brain(packet)
            db.mark_synapse_synced(r[0])
            
    if not found_target:
        print("[FAIL] Mock Bust not found in pending syncs!")
        return False
        
    # Check Vault
    files = os.listdir(VAULT_PATH)
    packet_files = [f for f in files if "Neuron_Packet" in f]
    if not packet_files:
        print("[FAIL] No Neuron Packet found in Vault.")
        return False
        
    print(f"[PASS] Synapse generated {len(packet_files)} packets.")
    return True

def verify_brain():
    print("[TEST] Running Brain Monitor...")
    # Ensure FAQ exists
    if not os.path.exists(FAQ_PATH):
        with open(FAQ_PATH, "w", encoding="utf-8") as f:
            f.write("# Sovereign FAQ\n")
            
    # Force update logic
    patterns = brain_monitor.analyze_patterns()
    print(f"[TEST] Patterns Detected: {patterns}")
    
    if "Recursive Reentrancy" in patterns:
        brain_monitor.update_faq("Recursive Reentrancy", patterns["Recursive Reentrancy"])
    else:
        print("[FAIL] Brain did not detect 'Recursive Reentrancy'.")
        return False
        
    # Check FAQ content
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "Recursive Reentrancy" in content:
        print("[PASS] FAQ Updated with Emerging Threat.")
        return True
    else:
        print("[FAIL] FAQ content missing target string.")
        return False

if __name__ == "__main__":
    try:
        setup_mock_bust()
        if verify_synapse() and verify_brain():
            print("\n✅ NEURAL BRIDGE VERIFIED: LOOP CLOSED.")
        else:
            print("\n❌ VERIFICATION FAILED.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
