"""
Live-Synapse Worker: The Autonomous CNS.
Triggers on every Audit_Verdict (Bust) -> Generates Neuron_Packet -> Syncs to Brain (NotebookLM).
"""
import time
import json
import os
import shutil
import datetime
from . import database as db

# Configuration
VAULT_PATH = os.path.join("NotebookLM", "The_Vault")
DRIVE_SYNC_ENABLED = False # Set to True if Google Drive API credentials present

def generate_neuron_packet(report):
    # report = (report_id, report_hash, address, data, vera_score)
    r_id, r_hash, address, data_json, score = report
    
    try:
        data = json.loads(data_json)
        risk_summary = data.get("risk_summary", "Unknown Vulnerability")
    except:
        data = {}
        risk_summary = "Parse Error"

    timestamp = datetime.datetime.now().isoformat()
    synapse_id = f"neu_{int(time.time())}_{r_id[-6:]}"

    packet = {
        "synapse_id": synapse_id,
        "timestamp": timestamp,
        "verdict": "BUST_CONFIRMED",
        "vera_score": score,
        "target_contract": address,
        "sheriff_notes": f"Automated flagging of {risk_summary}.",
        "exploit_vector": risk_summary,
        "technical_context": {
            "report_hash": r_hash,
            "raw_data_snippet": str(data)[:500] # Truncated for token optimization
        },
        "instruction_to_brain": "Analyze this exploit pattern. Update Heuristics/FAQ if novel."
    }
    return packet

def push_to_brain(packet):
    filename = f"Neuron_Packet_{packet['synapse_id']}.json"
    
    # 1. Local Persistence (The Vault)
    if not os.path.exists(VAULT_PATH):
        os.makedirs(VAULT_PATH, exist_ok=True)
        
    local_path = os.path.join(VAULT_PATH, filename)
    with open(local_path, "w") as f:
        json.dump(packet, f, indent=2)
        
    print(f"[SYNAPSE] Neuron Fired: {filename} -> {VAULT_PATH}")

    # 2. Google Drive Sync (Placeholder/Future)
    if DRIVE_SYNC_ENABLED:
        # TODO: Implement pydrive or google-api-python-client here
        pass
    
    return True

def run_loop():
    print("[SYNAPSE] Neural Bridge Active. Listening for Audit Verdicts...")
    while True:
        try:
            pending = db.get_pending_synapse_syncs()
            for r in pending:
                packet = generate_neuron_packet(r)
                if push_to_brain(packet):
                    db.mark_synapse_synced(r[0])
            
            time.sleep(5) # Fast poll for "Live" feel
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[SYNAPSE] Critical Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_loop()
