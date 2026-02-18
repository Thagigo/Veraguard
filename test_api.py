
import requests
import json

def test_audit():
    url = "http://localhost:8000/api/audit"
    payload = {
        "address": "0xSafeContractForWatermarkTest",
        "user_id": "test_verifier",
        "confirm_deep_dive": False,
        "bypass_deep_dive": True 
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2))
            
            if 'report_id' in data and 'report_hash' in data:
                print("SUCCESS: Report ID and Hash present.")
            else:
                print("FAILURE: Missing watermarking fields.")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_audit()
