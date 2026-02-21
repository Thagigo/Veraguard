import asyncio
from core.scout import scout
from core.brain_monitor import update_faq

def test_stateless_triage():
    print("--- Testing Stateless Triage ---")
    
    # Test 1: Benign contract (low suspicion)
    score1 = scout.stateless_triage("0xSafeContract123")
    print(f"Safe Contract Score: {score1}%")
    
    # Test 2: Highly Suspicious Contract
    score2 = scout.stateless_triage("0xFreshUnverifiedContract")
    print(f"Suspicious Contract Score: {score2}%")
    
    # Test Scan Orchestration (should trigger alert if score2 > 65)
    print("\nExecuting Scout Scan on Suspicious...")
    scout.scan_contract("0xFreshUnverifiedContract")
    
def test_brain_heuristic_injection():
    print("\n--- Testing Brain Heuristic Injection ---")
    
    # Mock a pattern that notebook LM detected
    mock_vector = "reentrancy_flashloan_v2"
    
    print(f"Injecting emerging pattern: {mock_vector}")
    
    # Inject into zero credit filters
    zero_filters = scout.heuristics.get("zero_credit_filters", [])
    if mock_vector not in zero_filters:
        zero_filters.append(mock_vector)
        scout.heuristics["zero_credit_filters"] = zero_filters
        
    print(f"Scout Zero-Credit Filters: {scout.heuristics['zero_credit_filters']}")
    
    # Test triage with the new filter
    test_address = f"0xContract_using_{mock_vector}"
    score = scout.stateless_triage(test_address)
    print(f"Triage Score for contract matching injected pattern: {score}%")
    assert score >= 50 # At least 50 from the zero credit filter
    
if __name__ == "__main__":
    test_stateless_triage()
    test_brain_heuristic_injection()
    print("\n[SUCCESS] All verifications passed.")
