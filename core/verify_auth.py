import hmac
import hashlib
import json
import time
import requests
import os
from urllib.parse import quote

# Configuration (Match .env)
BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
ADMIN_ID = 123456789
BASE_URL = "http://localhost:8000/api/brain/status"

def generate_init_data(user_id, token_to_sign_with=BOT_TOKEN):
    """
    Generates a valid Telegram WebApp initData string with HMAC signature.
    """
    user_json = json.dumps({"id": user_id, "first_name": "TestUser", "username": "tester"})
    auth_date = str(int(time.time()))
    
    # Data to sign
    data_dict = {
        "auth_date": auth_date,
        "query_id": "AAG...",
        "user": user_json
    }
    
    # Sort A-Z
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    
    # Sign
    secret_key = hmac.new(b"WebAppData", token_to_sign_with.encode(), hashlib.sha256).digest()
    signature = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    # Construct final query string
    # Note: Requests handles encoding, but we construct the raw header string here
    # "query_id=...&user=...&auth_date=...&hash=..."
    # URL encoded values? Telegram sends them URL encoded usually. 
    # But parse_qsl decodes them. 
    
    init_data = f"auth_date={auth_date}&query_id=AAG...&user={user_json}&hash={signature}"
    return init_data

def test_request(name, init_data, expected_status):
    print(f"\n--- TEST: {name} ---")
    try:
        headers = {}
        if init_data:
            headers["X-Telegram-Init-Data"] = init_data
            
        res = requests.get(BASE_URL, headers=headers)
        print(f"Status: {res.status_code} (Expected: {expected_status})")
        
        if res.status_code == 200:
            print(f"Response: {res.json().get('status')} - Admin: {res.json().get('admin_user')}")
        else:
            print(f"Error: {res.json().get('detail')}")
            
        if res.status_code == expected_status:
            print("✅ PASS")
        else:
            print("❌ FAIL")
            
    except Exception as e:
        print(f"Exception: {e}")

def run_tests():
    print("🔐 VERIFYING ADMIN GATEWAY HARDENING...")
    
    # 1. Valid Admin (Should Pass)
    valid_data = generate_init_data(ADMIN_ID)
    test_request("Authorized Admin", valid_data, 200)
    
    # 2. Valid Signature, Wrong User (Should Fail - ID Lock)
    wrong_user_data = generate_init_data(999999999)
    test_request("Unauthorized User (Valid Sig)", wrong_user_data, 403) # Auth fails ID check, creates generic 403? Or 500 if raise ValueError? 
    # My auth.py catches Exception and raises 403.
    
    # 3. Invalid Signature (Should Fail - Crypto Check)
    # We use a different bot token to sign
    fake_token_data = generate_init_data(ADMIN_ID, token_to_sign_with="fake-token")
    test_request("Spoofed Signature", fake_token_data, 403)
    
    # 4. No Header (Should Fail)
    test_request("No Auth Header", None, 401)
    
    # 5. Brute Force Check (Lockout)
    print("\n--- TEST: Brute Force Shield (Spamming...) ---")
    for i in range(6):
        test_request(f"Spam Attempt {i+1}", None, 401 if i < 5 else 429)

if __name__ == "__main__":
    run_tests()
