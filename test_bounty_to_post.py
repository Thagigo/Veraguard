from fastapi.testclient import TestClient
from core.main import app
import unittest.mock as mock

client = TestClient(app)

def test_bounty_to_post_loop():
    print("=== RUNNING BOUNTY-TO-POST VERIFICATION LOOP ===")
    
    # We will simulate an audit on a contract we know will trigger a CRITICAL warning.
    # We mock 'check_contract' to return a known payload, simulating a Deep Dive bust.
    
    mock_audit_result = '''{
        "vera_score": 10,
        "warnings": ["DETECTED: Ghost Mint (Signature A)", "HIGH: Unverified Contract"],
        "note": "SIMULATION: Critical Vulnerability Found",
        "report_id": "simulated-test-id",
        "report_hash": "0x12345abcdef"
    }'''
    
    with mock.patch("core.audit_logic.check_contract", return_value=mock_audit_result):
        # 1. Audit Phase
        print("[1] Simulating Audit Request...")
        response = client.post("/api/audit", json={
            "address": "0xDeceptiveGhostMintContract",
            "user_id": "test_hunter_001",
            "confirm_deep_dive": True
        })
        
        assert response.status_code == 200, f"Audit failed: {response.text}"
        data = response.json()
        
        # 2. Revenue Share Phase (Bounty Link)
        print("[2] Verifying The Rainmaker (Bounty Link)...")
        assert "bounty_id" in data, "Failed: No Bounty ID generated."
        assert "bounty_link" in data, "Failed: No Bounty Link generated."
        print(f"    -> Bounty Link Gen: {data['bounty_link']}")
        
        # 3. Public Signal Phase (X-Agent Tweet)
        print("[3] Verifying X-Agent (Public Signal)...")
        assert "tweet_intent_url" in data, "Failed: No Tweet Intent generated despite 100% Grounded Match."
        print(f"    -> Tweet Intent: {data['tweet_intent_url']}")
        
    print("================================================")
    print("VERIFICATION: SUCCESS")

if __name__ == "__main__":
    test_bounty_to_post_loop()
