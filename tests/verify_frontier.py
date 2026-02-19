
import sys
import os
import sqlite3
import time
import random

# Add core to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../core')))

import database
import frontier_logic

def verify_frontier():
    print("🤠 Verifying Sheriff's Frontier Logic...")
    
    # 1. Setup Test Data
    sheriffs = ["sheriff_alice", "sheriff_bob", "sheriff_charlie"]
    user_id = "test_user_123"
    
    # Clear previous rankings for test purity (optional, but good for cleanliness)
    with database.get_db() as conn:
        conn.execute("DELETE FROM sheriff_rankings WHERE user_id LIKE 'sheriff_%'")
        conn.commit()

    print(f"✅ Cleared old test rankings.")

    # 2. Simulate Audits
    # Alice: 5 correct, 0 incorrect (100% Vera, High Yield)
    for _ in range(5):
        frontier_logic.update_sheriff_ranking("sheriff_alice", is_correct=True, yield_amount=10.0)
    
    # Bob: 3 correct, 2 incorrect (60% Vera, Medium Yield)
    for _ in range(3):
        frontier_logic.update_sheriff_ranking("sheriff_bob", is_correct=True, yield_amount=5.0)
    for _ in range(2):
        frontier_logic.update_sheriff_ranking("sheriff_bob", is_correct=False, yield_amount=0.0)

    # Charlie: 1 correct, 0 incorrect (100% Vera, Low Yield)
    frontier_logic.update_sheriff_ranking("sheriff_charlie", is_correct=True, yield_amount=2.0)

    print("✅ Simulated audits for Alice, Bob, and Charlie.")

    # 3. Verify Leaderboard
    top_sheriffs = frontier_logic.get_top_sheriffs(limit=10)
    print("\n🏆 Leaderboard:")
    for i, s in enumerate(top_sheriffs):
        print(f"{i+1}. {s['user_id']} | Vera: {s['veracity_rate']:.1f}% | Yield: {s['yield']} | Multiplier: {'✅' if s['multiplier_active'] else '❌'}")

    # Check Rankings
    # Alice should be #1 (100% Vera, High Yield)
    # Charlie might be #2 (100% Vera, Low Yield) OR Bob might be depending on logic
    # Logic: Sort by Veracity DESC, then Yield DESC
    
    if top_sheriffs[0]['user_id'] == 'sheriff_alice':
        print("✅ Alice is #1 (Correct)")
    else:
        print(f"❌ Unexpected #1: {top_sheriffs[0]['user_id']}")

    # Check Multiplier Eligibility (Must have > 5 total verifications? No, logic says min_verifications=5)
    # Alice has 5 total. Bob has 5 total. Charlie has 1.
    # Alice: 5 verifications. 100% Vera. -> Eligible?
    # Logic: if total >= 5 and vera_rate >= 95.
    
    alice_data = next(s for s in top_sheriffs if s['user_id'] == 'sheriff_alice')
    if alice_data['multiplier_active']:
        print("✅ Alice has Multiplier (Correct)")
    else:
        print("❌ Alice MISSING Multiplier (Expected True)")

    bob_data = next(s for s in top_sheriffs if s['user_id'] == 'sheriff_bob')
    if not bob_data['multiplier_active']:
        print("✅ Bob has NO Multiplier (Correct - Low Vera)")
    else:
        print("❌ Bob HAS Multiplier (Expected False)")


    # 4. Trigger Mock Bounty (Vulnerable Audit)
    print("\n💰 Triggering Mock Bounty...")
    with database.get_db() as conn:
        # Insert a 'Bust' record manually into audit_reports
        conn.execute("""
            INSERT INTO audit_reports (report_id, report_hash, address, data, timestamp, vera_score, finder_id, is_first_finder)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"bust_{int(time.time())}", 
            "mock_hash",
            "0xVULNERABLE_CONTRACT", 
            "{}", 
            time.time(),
            20, # Low Vera Score
            "scout_dave",
            1
        ))
        conn.commit()

    # 5. Verify Bounty Feed
    recent_bounties = frontier_logic.get_recent_bounties(limit=5)
    print("\n📜 Recent Bounties:")
    for b in recent_bounties:
        print(f"- {b['target']} found by {b['scout_alias']} (Payout: {b['payout_eth']} ETH)")

    found = any(b['target'] == "0xVULNERABLE_CONTRACT" for b in recent_bounties)
    if found:
        print("✅ Mock Bounty found in Feed.")
    else:
        print("❌ Mock Bounty NOT found in Feed.")

if __name__ == "__main__":
    verify_frontier()
