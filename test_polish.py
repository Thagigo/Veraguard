import requests
import time
import uuid

BASE_URL = "http://localhost:8000"

def generate_user():
    return f"user_{uuid.uuid4().hex[:8]}"

def generate_ghost_address():
    return f"0x{uuid.uuid4().hex[:8]}ghost{uuid.uuid4().hex[:8]}"

def test_polish():
    print("--- Testing Final Polish Logic ---")
    
    # 1. Setup Users
    user_member = generate_user()
    user_normie = generate_user()
    
    # Fund & Subscribe "Member"
    print(f"Creating Member: {user_member}")
    requests.post(f"{BASE_URL}/api/pay", json={"tx_hash": f"tx_{uuid.uuid4().hex}", "user_id": user_member, "credits": 50, "is_subscription": True})
    
    # Fund "Normie" (Standard Credits)
    print(f"Creating Normie: {user_normie}")
    requests.post(f"{BASE_URL}/api/pay", json={"tx_hash": f"tx_{uuid.uuid4().hex}", "user_id": user_normie, "credits": 10, "is_subscription": False})

    # 2. Trigger First Finds
    addr_member_find = generate_ghost_address()
    addr_normie_find = generate_ghost_address()
    
    print(f"\nMember ({user_member}) finding {addr_member_find}...")
    requests.post(f"{BASE_URL}/api/audit", json={"address": addr_member_find, "user_id": user_member, "confirm_deep_dive": False, "bypass_deep_dive": True})
    
    print(f"Normie ({user_normie}) finding {addr_normie_find}...")
    requests.post(f"{BASE_URL}/api/audit", json={"address": addr_normie_find, "user_id": user_normie, "confirm_deep_dive": False, "bypass_deep_dive": True})
    
    # 3. Check Leaderboard
    print("\nChecking Leaderboard for Scores...")
    time.sleep(1)
    lb = requests.get(f"{BASE_URL}/api/leaderboard").json()
    
    entry_m = next((x for x in lb if x['user_id'].startswith(user_member[:4])), None)
    entry_n = next((x for x in lb if x['user_id'].startswith(user_normie[:4])), None)
    
    # Expected: 
    # Member: 50 * 1.5 = 75 points. (Plus maybe credits? 50 credits = 50 pts. Total 125 * 1.5? Or is score logic: Rep + FirstFinds?
    # Logic: Sheriff Score = (Credits + (FirstFinds * 50)) * Multiplier
    # Member has 50 credits (from sub) + 1 First Find (50). Total Base = 100. Multiplier 1.5 => 150.
    # Normie has 10 credits + 1 First Find (50). Total Base = 60. Multiplier 1.0 => 60.
    
    if entry_m:
        print(f"Member Entry: {entry_m}")
        if entry_m['sheriff_score'] >= 150:
            print("✅ Member Multiplier Active (Score >= 150)")
        else:
            print(f"❌ Member Score Too Low: {entry_m['sheriff_score']}")
            
        if entry_m.get('is_member'):
             print("✅ Member Flag Present")
        else:
             print("❌ Member Flag Missing")
             
    if entry_n:
        print(f"Normie Entry: {entry_n}")
        if entry_n['sheriff_score'] == 60:
             print("✅ Normie Score Correct (60)")
        else:
             print(f"❌ Normie Score Mismatch: {entry_n['sheriff_score']} (Expected 60)")

    # 4. Check Wall of Shame for Founder Badge
    print("\nChecking Wall of Shame...")
    ws = requests.get(f"{BASE_URL}/api/shame-wall").json()
    
    # Check if our finds are there and have finder_display
    found_m = next((x for x in ws if x['address'] == addr_member_find), None)
    if found_m:
        print(f"Found Member's Bust: {found_m}")
        if 'finder_display' in found_m and found_m['finder_display'] != "Unknown":
            print("✅ Founder Badge Data Present")
        else:
            print("❌ Founder Badge Data Missing")
    else:
        print("❌ Member's Bust Not on Wall")

if __name__ == "__main__":
    test_polish()
