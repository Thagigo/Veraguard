import sys
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from core.audit_engine import fetch_bytecode, verify_bytecode_signature, triage_address
import unittest.mock as mock

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

print()
print("==========================================")
print("  VeraGuard -- Bytecode Fingerprinting Test")
print("==========================================")
print()

# Test 1: USDC + phantom mint keyword -> spoof expected
print("Test 1: USDC + 'phantom mint' -> SPOOF EXPECTED")
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
r1 = triage_address(address=USDC, context_text="phantom mint scam check this", source="test")
if r1.get("spoof_detected") and r1.get("pattern_match") is None:
    print(f"  {PASS} spoof_detected=True, pattern_match=None")
    print(f"  Dashboard: 'False Positive Blocked: Bytecode mismatch for {USDC[:10]}...'")
    results.append(True)
else:
    print(f"  {FAIL} spoof={r1.get('spoof_detected')} match={r1.get('pattern_match')}")
    results.append(False)
print()

# Test 2: Zero address + phantom mint -> spoof (no bytecode)
print("Test 2: Zero address + 'phantom mint' -> SPOOF EXPECTED (no bytecode)")
ZERO = "0x0000000000000000000000000000000000000001"
r2 = triage_address(address=ZERO, context_text="phantom mint attack vector", source="test")
if r2.get("spoof_detected") and r2.get("pattern_match") is None:
    print(f"  {PASS} spoof_detected=True, pattern_match=None")
    results.append(True)
else:
    print(f"  {FAIL} spoof={r2.get('spoof_detected')} match={r2.get('pattern_match')}")
    results.append(False)
print()

# Test 3: Monkeypatched bytecode with known selector -> confirm
print("Test 3: Bytecode with '40c10f19' selector -> CONFIRM EXPECTED")
FAKE_ADDR = "0xDeAdBeEf1234567890AbCdEf1234567890AbCdEf"
FAKE_BC = "6080604052341561000f57600080fd" + "40c10f19" + "deadbeef"
with mock.patch("core.audit_engine.fetch_bytecode", return_value=FAKE_BC):
    confirmed = verify_bytecode_signature(FAKE_ADDR, "Phantom_Mint_Exploit_2026")
if confirmed:
    print(f"  {PASS} '40c10f19' correctly identified as Phantom Mint")
    results.append(True)
else:
    print(f"  {FAIL} Expected True but verify returned False")
    results.append(False)
print()

# Test 4: Live RPC fetch for USDC
print("Test 4: fetch_bytecode() returns non-empty for USDC (live Eth RPC)")
bc = fetch_bytecode(USDC)
if len(bc) > 10:
    print(f"  {PASS} Got {len(bc)//2} bytes from RPC")
    results.append(True)
else:
    print(f"  {FAIL} Empty bytecode -- check ETH_RPC_URL in .env")
    results.append(False)
print()

# Summary
passed = sum(results)
total = len(results)
print("==========================================")
if passed == total:
    print(f"  ALL {total}/{total} TESTS PASSED -- Bytecode Fingerprinting operational.")
else:
    print(f"  {passed}/{total} PASSED -- Review failures above.")
print("==========================================")
print()
sys.exit(0 if passed == total else 1)
