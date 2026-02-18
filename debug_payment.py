import requests
import json

url = "http://localhost:8000/api/pay"
headers = {"Content-Type": "application/json"}
data = {
    "tx_hash": "test_tx_debug_002", 
    "user_id": "test_user", 
    "credits": 10, 
    "is_subscription": False, 
    "referral_code": None
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
