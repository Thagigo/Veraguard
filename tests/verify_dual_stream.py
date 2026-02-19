import requests
import json
import os
import time

BASE_URL = "http://localhost:8000"
USER_ID = "test_verifier"
ADDRESS = "0xsafe000000000000000000000000000000000000"

def print_step(msg):
    print(f"\n[STEP] {msg}")

def verify():
    # 1. Reset User
    print_step("Resetting User State...")
    requests.post(f"{BASE_URL}/api/debug/wipeout", json={"user_id": USER_ID})

    # 2. Add Voucher Credits (Subscription)
    print_step("Adding Voucher Credits (Subscription Mock)...")
    # Using /api/pay with is_subscription=True -> Adds 50 credits as 'voucher'
    res = requests.post(f"{BASE_URL}/api/pay", json={
        "tx_hash": "0x_sub_tx",
        "user_id": USER_ID,
        "credits": 0,
        "is_subscription": True
    })
    print(f"Sub Response: {res.json()}")

    # 3. Add Purchased Credits (Bundle)
    print_step("Adding Purchased Credits (Bundle Mock)...")
    # Adds 10 credits as 'purchase'
    res = requests.post(f"{BASE_URL}/api/pay", json={
        "tx_hash": "0x_bundle_tx",
        "user_id": USER_ID,
        "credits": 10,
        "is_subscription": False
    })
    print(f"Bundle Response: {res.json()}")

    # 4. Perform Audit (Should consume Voucher first - FIFO? No, wait.)
    # FIFO depends on timestamp.
    # Sub added first -> Voucher first.
    # So this audit should use VOUCHER.
    print_step("Performing Audit 1 (Expect VOUCHER)...")
    res = requests.post(f"{BASE_URL}/api/audit", json={
        "address": ADDRESS,
        "user_id": USER_ID,
        "bypass_deep_dive": False, # Deep Dive -> Cost 2 or 3
        "confirm_deep_dive": True
    })
    data = res.json()
    print(f"Audit 1 Source: {data.get('credit_source')}")
    print(f"Audit 1 Cost: {data.get('cost_deducted')}")
    
    if data.get('credit_source') != 'voucher':
        print("FAILED: Expected 'voucher', got", data.get('credit_source'))
    else:
        print("PASSED: Source is Voucher")

    # 5. Check Certificate
    print_step("Checking Certificate 1...")
    report_id = data.get('report_id')
    cert_path = os.path.join("NotebookLM", "The_Vault", f"Certificate_{report_id}.json")
    if os.path.exists(cert_path):
        with open(cert_path, 'r') as f:
            cert = json.load(f)
            notice = cert.get('forensic_notice', '')
            print(f"Forensic Notice: {notice}")
            if "Vera-Pass Voucher" in notice:
                print("PASSED: Certificate mentions Voucher")
            else:
                print("FAILED: Certificate text mismatch")
    else:
        print(f"FAILED: Certificate not found at {cert_path}")

    # 6. Consume all Vouchers to switch to Purchase? 
    # Voucher balance = 50. Purchase = 10.
    # That takes too long.
    # Let's Wipe and add Purchase FIRST, then Voucher.
    
    print_step("Resetting for Reverse Test...")
    requests.post(f"{BASE_URL}/api/debug/wipeout", json={"user_id": USER_ID})

    print_step("Adding Purchase First...")
    requests.post(f"{BASE_URL}/api/pay", json={
        "tx_hash": "0x_bundle_tx_2",
        "user_id": USER_ID,
        "credits": 5, # Small amount
        "is_subscription": False
    })
    # Wait a bit to ensure timestamp diff
    time.sleep(1.1)

    print_step("Adding Voucher Second...")
    requests.post(f"{BASE_URL}/api/pay", json={
        "tx_hash": "0x_sub_tx_2",
        "user_id": USER_ID,
        "credits": 50,
        "is_subscription": True
    })

    print_step("Performing Audit 2 (Expect PURCHASE)...")
    res = requests.post(f"{BASE_URL}/api/audit", json={
        "address": "0xsafe222222222222222222222222222222222222",
        "user_id": USER_ID,
        "confirm_deep_dive": True
    })
    data = res.json()
    print(f"Audit 2 Source: {data.get('credit_source')}")
    
    if data.get('credit_source') != 'purchase':
        print("FAILED: Expected 'purchase', got", data.get('credit_source'))
    else:
        print("PASSED: Source is Purchase")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"Verification Error: {e}")
