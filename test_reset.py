
import requests
import json

def test_reset():
    url = "http://localhost:8000/api/debug/reset"
    payload = {"user_id": "test_verifier"}
    headers = {"Content-Type": "application/json"}
    
    print(f"Resetting credits for {payload['user_id']}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:", response.json())
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_reset()
