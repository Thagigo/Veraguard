import time
import requests
import sys

def simulate_evolution():
    print("--- 🧠 INITIALIZING AUTONOMOUS BRAIN EVOLUTION (REMOTE) ---")
    
    base_url = "http://localhost:8000"
    
    # Simulating a stream of new contracts on Base
    mock_contracts = [
        "0xSafeProject_LowLiquidity",
        "0xHighValue_Scam_Token",
        "0xStandard_Defi_Protocol",
        "0xMassive_Rug_Pull_Attempt"
    ]

    for address in mock_contracts:
        print(f"\n[SCANNING] {address}...")
        try:
            res = requests.post(f"{base_url}/api/admin/scan", json={"address": address})
            print(f"Server Response: {res.status_code}")
        except Exception as e:
            print(f"Connection Failed: {e}")
            
        time.sleep(1.5) # Formatting delay

    print("\n--- 🔄 EVOLUTION CYCLE COMPLETE ---")
    print(f"Check Protocol Dashboard for live feed.")

if __name__ == "__main__":
    simulate_evolution()
