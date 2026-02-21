"""
Brain-Feedback Interface: The Learning Loop.
Monitors The Vault for emerging patterns -> Updates Sovereign_FAQ.md -> Generates Heuristics.
"""
import os
import json
import time
import datetime
import requests
from collections import Counter

# Configuration
VAULT_PATH = os.path.join("NotebookLM", "The_Vault")
FAQ_PATH = "Sovereign_FAQ.md"
HEURISTIC_PATH = "HEURISTIC_UPDATE.txt"

def analyze_patterns():
    if not os.path.exists(VAULT_PATH):
        return {}

    exploit_vectors = []
    
    # scan for Neuron Packets
    for filename in os.listdir(VAULT_PATH):
        if filename.startswith("Neuron_Packet_") and filename.endswith(".json"):
            try:
                with open(os.path.join(VAULT_PATH, filename), "r", encoding="utf-8") as f:
                    packet = json.load(f)
                    vector = packet.get("exploit_vector")
                    if vector:
                        exploit_vectors.append(vector)
            except:
                continue
                
    return Counter(exploit_vectors)

def update_faq(vector, count):
    if not os.path.exists(FAQ_PATH):
        print(f"[BRAIN] Error: {FAQ_PATH} not found.")
        return

    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    if vector in content:
        return # Already documented

    print(f"[BRAIN] Emerging Threat Detected: {vector} (Seen {count} times). Updating FAQ...")
    
    # Generate new entry (Template)
    new_entry = f"""
## Q: What is the '{vector}' vulnerability?
**A:** The Autonomous CNS has detected a rising trend in **{vector}**. 
This exploit typically involves manipulating contract state to bypass validation. 
*Heuristic Update has been deployed to the Audit Engine.*
"""
    
    with open(FAQ_PATH, "a", encoding="utf-8") as f:
        f.write("\n" + new_entry)
        
    # Generate Heuristic Update
    with open(HEURISTIC_PATH, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().isoformat()
        f.write(f"[{timestamp}] HEURISTIC_ADD: {vector} | WEIGHT: 0.95 | SOURCE: CNS_AUTO_LEARN\n")

def run_loop():
    print("[BRAIN] Monitor Active. Analyzing Synaptic Patterns every 4 hours...")
    
    # Import scout to inject Zero-Credit filters
    from core.scout import scout
    
    while True:
        try:
            patterns = analyze_patterns()
            
            # If any vector seen > 0 times (for testing, usually higher), update FAQ
            for vector, count in patterns.items():
                if count >= 1: 
                    update_faq(vector, count)
                    
                    # Auto-inject into Scout's Zero-Credit Filter list
                    zero_credit_filters = scout.heuristics.get("zero_credit_filters", [])
                    if vector.lower() not in [f.lower() for f in zero_credit_filters]:
                        zero_credit_filters.append(vector)
                        scout.heuristics["zero_credit_filters"] = zero_credit_filters
                        print(f"[BRAIN] Injected '{vector}' into Scout Zero-Credit Filters.")
                        
                        try:
                            requests.post("http://127.0.0.1:8000/api/internal/live_event", json={"event_type": "intelligence_update", "data": {"heuristic": vector}})
                        except Exception as e:
                            print(f"[BRAIN] Failed to broadcast intelligence update: {e}")
            
            # Sleep for 4 hours (14400 seconds)
            time.sleep(14400) 
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[BRAIN] Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_loop()
