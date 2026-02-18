
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_audit_flow():
    print("\n--- Testing Audit Flow (to populate Shame Wall) ---")
    # 1. Reset credits for test user
    requests.post(f"{BASE_URL}/api/debug/reset", json={"user_id": "sheriff_tester"})
    
    # 2. Buy credits (mock db insert or just rely on free tier if implemented, 
    # but let's cheat and add credits via DB helper if we could, but we can't via API easily without payment.
    # Actually, we can use the debug reset, then maybe just rely on free tier? 
    # Or strict payment?
    # Let's just use the 'user_test' which might have credits or we can just try audit and see.
    
    payload = {
        "address": "0xScamContract_" + str(time.time())[-4:],
        "user_id": "sheriff_tester",
        "confirm_deep_dive": True,
        "bypass_deep_dive": False
    }
    
    # We need credits. core/database.py has db_add_credits but no API.
    # We will assume the audit might fail with 402 if no credits.
    # However, for this test, let's just hit the read-only endpoints first to see if they crash.
    pass

def test_endpoints():
    print("\n--- Testing Sheriff's Frontier Endpoints ---")
    
    # Shame Wall
    try:
        res = requests.get(f"{BASE_URL}/api/shame-wall")
        print(f"GET /shame-wall: {res.status_code}")
        if res.status_code == 200:
            print(f"Data: {len(res.json())} items")
            print(json.dumps(res.json()[:1], indent=2))
    except Exception as e:
        print(f"Shame Wall Error: {e}")

    # Leaderboard
    try:
        res = requests.get(f"{BASE_URL}/api/leaderboard")
        print(f"GET /leaderboard: {res.status_code}")
        if res.status_code == 200:
            print(f"Data: {len(res.json())} items")
            print(json.dumps(res.json()[:1], indent=2))
    except Exception as e:
        print(f"Leaderboard Error: {e}")

if __name__ == "__main__":
    test_endpoints()
