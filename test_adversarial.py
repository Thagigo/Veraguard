import json
import unittest.mock as mock
import binascii
from core.audit_logic import check_contract

def to_hex(ascii_str):
    return binascii.hexlify(ascii_str.encode('utf-8')).decode('utf-8')

# The Skeptic's Fake-Out Deceptions
DECEPTIVE_CONTRACTS = [
    {
        "name": "Ghost Mint via SafeMath",
        # Includes ASCII "SafeMath" and "require" as hex strings to fake-out simple analysis,
        # but also includes the actual Hex signature for ghost_mint: "6d696e74"
        "bytecode": to_hex("require(msg.sender == owner) SafeMath.add()") + "6d696e74" + to_hex("fake_bytecode"),
        "expected_flag": "ghost_mint"
    },
    {
        "name": "Hidden Proxy with ER20 Interface",
        # Includes ASCII "totalSupply()" but contains the UUPS Silent Death indicator 'c4d66de8' (initialize without upgradeTo)
        "bytecode": to_hex("totalSupply() balanceOf()") + "c4d66de8" + to_hex("fake_bytecode"),
        "expected_flag": "uups_silent_death"
    },
    {
        "name": "EIP-1967 Proxy Hidden in Withdraw",
        # Includes safe withdraw logic but contains EIP-1967 fallback hex
        "bytecode": to_hex("withdraw() emit Transfer()") + "360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc" + to_hex("fake_bytecode"),
        "expected_flag": "is_proxy"
    },
    {
        "name": "Rug Pull via delegatecall inside nonReentrant",
        # Includes nonReentrant ascii but contains classic 'f4' delegatecall sequence
        "bytecode": to_hex("nonReentrant() burn() collectFee()") + "6080604052f4" + to_hex("fake_bytecode"),
        "expected_flag": "is_proxy"
    },
    {
        "name": "Missing SafeMath Panic",
        # Lacks the 4e487b71 signature (panic), triggering Legacy Math Overflow
        "bytecode": to_hex("ReentrancyGuard SafeERC20") + "00000000",
        "expected_flag": "legacy_math"
    }
]

def run_fake_out_tests():
    import core.database
    core.database.init_db()
    
    passed = 0
    total = len(DECEPTIVE_CONTRACTS)
    
    print("=== RUNNING SKEPTIC FAKE-OUT TESTS ===")
    for idx, contract in enumerate(DECEPTIVE_CONTRACTS):
        print(f"[{idx+1}/{total}] Testing: {contract['name']}...")
        with mock.patch("core.audit_logic.Web3") as MockWeb3:
            try:
                # Mocking the returned bytecode and Web3 behavior
                instance = MockWeb3.return_value
                instance.is_connected.return_value = True
                
                # We return bytes that when hexlified will become the contract['bytecode'] string
                instance.eth.get_code.return_value = bytes.fromhex(contract["bytecode"])
                
                # Run Check
                result_json = check_contract("0x1234567890123456789012345678901234567890", credit_source="test_runner")
                result = json.loads(result_json)
                
                if result["vera_score"] <= 60 and len(result["warnings"]) > 0:
                    print(f"   [PASS] Flagged successfully. Score: {result['vera_score']}")
                    passed += 1
                else:
                    print(f"   [FAIL] Evaded detection! Score: {result['vera_score']}. Warnings: {result['warnings']}")
            except Exception as e:
                print(f"   [ERROR] Exception during test: {str(e)}")
                
    print("======================================")
    print(f"RESULTS: {passed}/{total} Passed")
    
    if passed == total:
        print("SKEPTIC HARDENING: COMPLETE")
        exit(0)
    else:
        print("SKEPTIC HARDENING: FAILED")
        exit(1)

if __name__ == "__main__":
    run_fake_out_tests()
