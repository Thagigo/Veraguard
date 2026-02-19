import requests
import json
import os

url = "http://localhost:8000/api/audit"
payload = {
    "address": "0xDeepDiveTest",
    "user_id": "test_certificate_user",
    "confirm_deep_dive": True
}

try:
    print("Sending Audit Request...")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Audit Success.")
        if "certificate" in data:
            print("Certificate Field Found:")
            print(json.dumps(data["certificate"], indent=2))
        else:
            print("Certificate Field MISSING.")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Failed: {e}")
