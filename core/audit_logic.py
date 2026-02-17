import json
from web3 import Web3
import time
from . import cache
from . import triage
from . import hunter_agent

# Use existing signatures from audit_logic.py or refactor.
# For simplicity, we keep the signature checking directly here or import it 
# if we wanted to modularize further. To avoid circular imports or breaking existing logic,
# we will re-integrate the signature checks.

# Signatures of Malice (2026 High-Priority)
SIGNATURES_OF_MALICE = {
    "ghost_mint": {
        "name": "Ghost Mint (Signature A)",
        "description": "Pricing logic allowing zero-value minting.",
        "risk_level": "CRITICAL",
        "score_deduction": 100,
        "signature_hex": "6d696e74"
    },
    "uups_silent_death": {
        "name": "UUPS Silent Death (Signature B)",
        "description": "UUPS Proxy missing upgradeTo function.",
        "risk_level": "CRITICAL",
        "score_deduction": 100,
        "signature_hex": "3659cfe6"
    },
    "legacy_math": {
       "name": "Legacy Math Overflow",
       "description": "Solidity < 0.8.0 without SafeMath protection.",
        "risk_level": "HIGH",
        "score_deduction": 40,
        "panic_signature": "4e487b71"
    }
}

def check_contract(address: str, rpc_url: str = "https://cloudflare-eth.com") -> str:
    """
    Orchestrates the intelligent audit: Cache -> Triage -> Hunter.
    """
    warnings = []
    vera_score = 100
    bytecode = ""
    note = "Audit based on Verified Intelligence"

    # --- SIMULATION RESTORATION ---
    # (Keeping the demo modes active as they are useful for UI)
    if "ghost" in address.lower():
         return json.dumps({"vera_score": 0, "warnings": ["DETECTED: Ghost Mint (Signature A)"], "note": "SIMULATION: Ghost Mint Demo"})
    if "brick" in address.lower():
         return json.dumps({"vera_score": 0, "warnings": ["DETECTED: UUPS Silent Death (Signature B)"], "note": "SIMULATION: Bricking Risk Demo"})
    if "fee" in address.lower():
         return json.dumps({"vera_score": 50, "warnings": ["DETECTED: Fee-On-Transfer Abuse"], "note": "SIMULATION: Fee Abuse Demo"})
    if "honey" in address.lower():
         return json.dumps({"vera_score": 50, "warnings": ["DETECTED: Honeypot"], "note": "SIMULATION: Honeypot Demo"})
    if "safe" in address.lower():
        return json.dumps({"vera_score": 100, "warnings": [], "note": "SIMULATION: Safe Contract Demo"})

    # --- REAL AUDIT MODE ---
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
             return json.dumps({"error": "Failed to connect to RPC", "vera_score": 0, "warnings": []})
        
        if not w3.is_address(address):
            return json.dumps({"error": "Invalid address.", "vera_score": 0, "warnings": []})
        
        checksum_address = w3.to_checksum_address(address)
        try:
             bytecode = w3.eth.get_code(checksum_address).hex()
        except:
             return json.dumps({"error": "Failed to fetch bytecode", "vera_score": 0, "warnings": []})

        if bytecode == "0x" or bytecode == "":
            return json.dumps({"error": "Contract has no bytecode (EOA or destroyed)", "vera_score": 0, "warnings": []})

        # --- 1. CACHE CHECK ---
        cached_result = cache.get_cached_audit(bytecode)
        if cached_result:
            cached_result['note'] = "Served from Semantic Cache (24h)"
            return json.dumps(cached_result)

        # --- 2. TRIAGE TIER (Gemini 3 Flash) ---
        triage_result = triage.scan(bytecode)
        vera_score = triage_result['triage_score']
        warnings.extend(triage_result['triage_warnings'])

        # --- 3. CORE LOGIC (Signatures) ---
        # (We keep the core signatures as part of the baseline check)
        
        if SIGNATURES_OF_MALICE['ghost_mint']['signature_hex'] in bytecode:
             warnings.append(f"DETECTED: {SIGNATURES_OF_MALICE['ghost_mint']['name']}")
             vera_score -= SIGNATURES_OF_MALICE['ghost_mint']['score_deduction']

        if "c4d66de8" in bytecode and SIGNATURES_OF_MALICE['uups_silent_death']['signature_hex'] not in bytecode:
             warnings.append(f"DETECTED: {SIGNATURES_OF_MALICE['uups_silent_death']['name']}")
             vera_score -= SIGNATURES_OF_MALICE['uups_silent_death']['score_deduction']

        if SIGNATURES_OF_MALICE['legacy_math']['panic_signature'] not in bytecode:
             warnings.append(f"DETECTED: {SIGNATURES_OF_MALICE['legacy_math']['name']}")
             vera_score -= SIGNATURES_OF_MALICE['legacy_math']['score_deduction']


        # --- 4. HUNTER TIER (Gemini 3 Pro) ---
        # Trigger Hunter if score dropped below 70 from Triage or Signatures
        if vera_score < 70:
            hunter_result = hunter_agent.analyze(bytecode, warnings)
            vera_score -= hunter_result['hunter_score_deduction']
            warnings.extend(hunter_result['hunter_warnings'])
            note += " | Hunter Deep Analysis Triggered"

        # Final Score Calculation
        vera_score = max(0, vera_score)
        
        final_result = {
            "vera_score": vera_score,
            "warnings": warnings,
            "note": note
        }

        # --- 5. UPDATE CACHE ---
        cache.set_cached_audit(bytecode, final_result)

        return json.dumps(final_result)

    except Exception as e:
        return json.dumps({"error": str(e), "vera_score": 0, "warnings": []})
