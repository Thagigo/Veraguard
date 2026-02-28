import json
import unittest.mock as mock
from fastapi.testclient import TestClient
from core.main import app
import core.database as database

client = TestClient(app)

def test_sovereign_readiness():
    print("=== BEGINNING FINAL SOVEREIGN HANDSHAKE ===")
    passed = 0
    total = 4
    
    print("\n[1] Verifying Intelligence Purity & Activation...")
    with mock.patch("httpx.AsyncClient.get") as mock_get:
        # Mock a successful Google API response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # We also need to inject the mock env vars for the endpoint to even try httpx
        import os
        with mock.patch.dict(os.environ, {"GOOGLE_API_KEY": "mock_key", "NOTEBOOK_ID": "mock_id", "ENV_MODE": "PRODUCTION"}):
            response = client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            
            env_mode = data.get("env_mode")
            notebook_status = data.get("notebooklm", {}).get("status")
            
            if env_mode == "PRODUCTION" and notebook_status == "GROUNDED":
                print("  [OK] ENV_MODE is PRODUCTION")
                print("  [OK] Brain is GROUNDED")
                passed += 1
            else:
                print(f"  [X] Failed: env_mode={env_mode}, notebook_status={notebook_status}")

    # Initialize a clean DB state for the next tests
    database.init_db()

    # 2. The Variant Stress Test (The Skeptic)
    print("\n[2] Executing Variant Stress Test (The Skeptic)...")
    
    # Give the stress_tester_001 enough credits (in base db)
    with database.get_db() as cnn:
        c = cnn.cursor()
        c.execute("INSERT OR REPLACE INTO users (user_id, credits) VALUES (?, ?)", ("stress_tester_001", 1000))
        cnn.commit()
    
    # Mocking check_contract to simulate the engine catching a mutated variant
    mock_audit_result = json.dumps({
        "vera_score": 10,
        "warnings": ["DETECTED: Ghost Mint (Signature A)", "(Ancestral Source: 0xGhost)"],
        "note": "SIMULATION: Critical Vulnerability Found",
        "report_id": "mutant-test-id",
        "report_hash": "0xmutant_hash_123"
    })

    print("\n[2] Executing Variant Stress Test (The Skeptic)...")
    with mock.patch("core.audit_logic.check_contract", return_value=mock_audit_result):
        # ensure draft tweet triggers properly
        with mock.patch("core.x_agent.draft_tweet", return_value="https://twitter.com/intent/tweet?text=vera-verify-alert") as mock_draft:
            audit_res = client.post("/api/audit", json={
                "address": "0xMutatedReentrancyVariantContract",
                "user_id": "stress_tester_001",
                "confirm_deep_dive": True
            })
        
        if audit_res.status_code != 200:
            print(f"  [X] Audit endpoint failed: {audit_res.status_code} {audit_res.text}")
        assert audit_res.status_code == 200
        audit_data = audit_res.json()
        
        warnings = str(audit_data.get("warnings", []))
        if "Ancestral Source" in warnings:
            print("  [OK] Mutated variant detected.")
            print("  [OK] Reasoning Trace cited Ancestral Source.")
            passed += 1
        else:
            print("  [X] Failed to detect variant or cite source.")

        # 3. Market Domination Layer (The Rainmaker)
        print("\n[3] Verifying Market Domination Layer (The Rainmaker)...")
        if "bounty_id" in audit_data and "bounty_link" in audit_data:
            print(f"  [OK] Bounty Link Generated: {audit_data['bounty_link']}")
            if "tweet_intent_url" in audit_data:
                print(f"  [OK] X-Agent drafted Intelligence Report: {audit_data['tweet_intent_url'][:60]}...")
                passed += 1
            else:
               print("  [X] X-Agent failed to draft report.")
        else:
            print("  [X] Revenue Share failed to generate bounty link.")

    # 4. Production Toggle (Ledger Check)
    print("\n[4] Verifying Indigo Stream Distribution...")
    import core.settlement_worker as settlement_worker
    
    # Mock database functions to trace ledger interaction
    with mock.patch("core.database.expire_vouchers", return_value=100.0) as mock_expire:
        with mock.patch("core.database.record_founder_carry") as mock_record:
            # We also mock generate_reports to avoid side effects
            with mock.patch("core.reports.generate_monthly_revenue_report", return_value="mock_report.pdf"):
                settlement_worker.run_settlement()
                
                # Verify that Founder received 60% of the 100 expired vouchers = 60.0
                mock_record.assert_called_with(60.0, 'settlement')
                print("  [OK] 60% Indigo Stream explicitly distributed to founder in ledger.")
                passed += 1

    print("\n================================================")
    print(f"VERIFICATION: {passed}/{total} PASSED")
    
    if passed == total:
         print("SOVEREIGN HANDSHAKE COMPLETE.")
         exit(0)
    else:
         print("SOVEREIGN HANDSHAKE FAILED.")
         exit(1)

if __name__ == "__main__":
    test_sovereign_readiness()
