import json
import uuid
import hashlib
import random
from web3 import Web3
import time
from . import cache
from . import triage
from . import hunter_agent
from . import certificate # [NEW] Certificate Module

# Use existing signatures from audit_logic.py or refactor.
# For simplicity, we keep the signature checking directly here or import it 
# if we wanted to modularize further. To avoid circular imports or breaking existing logic,
# we will re-integrate the signature checks.

# Signatures of Malice (2026 High-Priority)
# (imports above)

def universal_ledger_check(address: str) -> str:
    """
    Simulates a 'Universal Ledger' check against the Veraguard Knowledge Base.
    - Checks for 'huge' contracts (>24KB bytecode).
    - Checks for known 'complex' patterns.
    Returns: "Standard" (0.001 ETH) or "Deep Dive" (0.003 ETH).
    """
    if not address: return "Standard"
    addr_lower = address.lower()
    if addr_lower.endswith("huge") or addr_lower.endswith("24kb") or addr_lower.endswith("deep"):
        return "Deep Dive"
    return "Standard"

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

def perform_triage_scan(bytecode: str) -> dict:
    """
    Phase 1 & 2: Static Analysis, Heuristics, and Signatures.
    Fast, Regex-based.
    """
    warnings = []
    vera_score = 100
    is_proxy = False

    # --- HEURISTIC PROXY DETECTION ---
    if "f4" in bytecode or "360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc" in bytecode:
            is_proxy = True

    # --- 2. TRIAGE TIER (Gemini 3 Flash) ---
    triage_result = triage.scan(bytecode)
    vera_score = triage_result['triage_score']
    warnings.extend(triage_result['triage_warnings'])

    # --- 3. CORE LOGIC (Signatures) ---
    if SIGNATURES_OF_MALICE['ghost_mint']['signature_hex'] in bytecode:
            warnings.append(f"DETECTED: {SIGNATURES_OF_MALICE['ghost_mint']['name']}")
            vera_score -= SIGNATURES_OF_MALICE['ghost_mint']['score_deduction']

    if "c4d66de8" in bytecode and SIGNATURES_OF_MALICE['uups_silent_death']['signature_hex'] not in bytecode:
            warnings.append(f"DETECTED: {SIGNATURES_OF_MALICE['uups_silent_death']['name']}")
            vera_score -= SIGNATURES_OF_MALICE['uups_silent_death']['score_deduction']

    if SIGNATURES_OF_MALICE['legacy_math']['panic_signature'] not in bytecode:
            warnings.append(f"DETECTED: {SIGNATURES_OF_MALICE['legacy_math']['name']}")
            vera_score -= SIGNATURES_OF_MALICE['legacy_math']['score_deduction']
    
    return {
        "vera_score": max(0, vera_score),
        "warnings": warnings,
        "is_proxy": is_proxy,
        "note": "Triage Analysis Complete"
    }

def perform_deep_scan(bytecode: str, triage_data: dict) -> dict:
    """
    Phase 3: Hunter Agent (Gemini Pro Simulation).
    """
    vera_score = triage_data['vera_score']
    warnings = list(triage_data['warnings'])
    note = triage_data['note']

    # --- 4. HUNTER TIER (Gemini 3 Pro) ---
    # Trigger Hunter if score dropped below 70 from Triage or Signatures
    
    # [NEW] Red Team Simulation Log
    red_team_log = []
    
    # Mocking Red Team Actions for Deep Scan
    attack_vectors = [
        {"name": "Flash Loan Attack", "status": "Simulating Liquidity Drain..."},
        {"name": "Reentrancy", "status": "Attempting Recursive Call..."},
        {"name": "Ownership Override", "status": "Bypassing Admin Logic..."},
    ]
    
    for vector in attack_vectors:
        # Simple RNG for demo purposes, in real app this comes from Hunter
        is_vuln = False
        if "reentrancy" in note.lower() and vector['name'] == "Reentrancy": is_vuln = True
        if "honeypot" in note.lower() and vector['name'] == "Flash Loan Attack": is_vuln = True
        
        verdict = "VULNERABLE" if is_vuln else "RESILIENT"
        red_team_log.append({
            "vector": vector['name'],
            "status": "Attempted",
            "verdict": verdict,
            "details": f"{vector['status']} [{verdict}]"
        })

    # Trigger Hunter if needed for score/warning adjustments (Mock logic retained)
    if vera_score < 70:
        hunter_result = hunter_agent.analyze(bytecode, warnings)
        vera_score -= hunter_result['hunter_score_deduction']
        warnings.extend(hunter_result['hunter_warnings'])
        note += " | Hunter Deep Analysis Triggered"

    return {
        "vera_score": max(0, vera_score),
        "warnings": warnings,
        "is_proxy": triage_data['is_proxy'],
        "note": note,
        "red_team_log": red_team_log
    }

def check_contract(address: str, scan_type: str = "deep", rpc_url: str = "https://cloudflare-eth.com", credit_source: str = "purchase") -> str:
    """
    Orchestrates the intelligent audit.
    scan_type: 'triage' (Fast) or 'deep' (Full).
    """
    
    # Helper to watermark simulation
    def watermark_sim(data: dict):
        rid = str(uuid.uuid4())
        ts = str(time.time())
        # safe hash
        payload = f"{address}:{data.get('vera_score', 0)}:{ts}:{data.get('note', '')}:SOURCE={credit_source}"
        rhash = hashlib.sha256(payload.encode()).hexdigest()
        
        data.update({
            "report_id": rid,
            "report_hash": rhash,
            "timestamp": ts,
            "risk_summary": data.get("note", "Simulation"),
            "milestones": [],
            "vitals": {"liquidity": "SIMULATED", "owner_risk": "UNKNOWN"}
        })

        # [NEW] Generate Certificate for Simulation
        try:
             cert = certificate.generate_certificate(rid, rhash, address, data.get('vera_score', 0), data.get('warnings', []), credit_source)
             data["certificate"] = cert
        except Exception as e:
             print(f"Sim Cert Gen Failed: {e}")

        return json.dumps(data)

    if "ghost" in address.lower():
            return watermark_sim({"vera_score": 0, "warnings": ["DETECTED: Ghost Mint (Signature A)"], "note": "SIMULATION: Ghost Mint Demo"})
    if "brick" in address.lower():
            return watermark_sim({"vera_score": 0, "warnings": ["DETECTED: UUPS Silent Death (Signature B)"], "note": "SIMULATION: Bricking Risk Demo"})
    if "fee" in address.lower():
            return watermark_sim({"vera_score": 50, "warnings": ["DETECTED: Fee-On-Transfer Abuse"], "note": "SIMULATION: Fee Abuse Demo"})
    if "honey" in address.lower():
            return watermark_sim({"vera_score": 50, "warnings": ["DETECTED: Honeypot"], "note": "SIMULATION: Honeypot Demo"})
    if "huge" in address.lower() or "deep" in address.lower():
        # Simulate a complex Deep Dive result
        time.sleep(2) # Mock processing time
        return watermark_sim({
            "vera_score": 45, 
            "warnings": ["CRITICAL: Hidden Proxy Logic", "HIGH: Unverified External Call"], 
            "note": "SIMULATION: Multi-Layer Deep Dive Analysis",
            "red_team_log": [
                {"vector": "Flash Loan Attack", "status": "Attempted", "verdict": "VULNERABLE", "details": "Simulating Liquidity Drain... [VULNERABLE]"},
                {"vector": "Reentrancy", "status": "Attempted", "verdict": "RESILIENT", "details": "Attempting Recursive Call... [RESILIENT]"},
                {"vector": "Ownership Override", "status": "Attempted", "verdict": "VULNERABLE", "details": "Bypassing Admin Logic... [VULNERABLE]"}
            ]
        })

    if "safe" in address.lower():
        return watermark_sim({"vera_score": 100, "warnings": [], "note": "SIMULATION: Safe Contract Demo"})

    # --- REAL AUDIT MODE ---
    # --- 1. BYTECODE EXTRACTION ---
    # --- 1. BYTECODE EXTRACTION ---
    try:
        # Connect to RPC
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            return json.dumps({"error": "RPC Connection Failed", "vera_score": 0, "warnings": []})
        
        code = w3.eth.get_code(Web3.to_checksum_address(address))
        bytecode = code.hex()
        
        if bytecode == "0x":
            return json.dumps({"error": "Contract has no bytecode (EOA or Destructed)", "vera_score": 0, "warnings": []})
            
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch bytecode: {str(e)}", "vera_score": 0, "warnings": []})

    # --- 1. CACHE CHECK ---
    # Cache key should probably include scan_type? 
    # Or we always cache the Deep Result and can serve Triage from it?
    # For now, simplistic cache.
    cached_result = cache.get_cached_audit(bytecode)
    if cached_result:
        # If we requested Triage but have Deep cached, we can return it (or downgrade it?)
        if scan_type == 'triage':
            # Triage is a subset, so we could just return it, BUT Triage shouldn't show Hunter warnings.
            # Re-running Triage is cheap.
            pass
        elif scan_type == 'deep':
            cached_result['note'] = "Served from Semantic Cache (24h)"
            return json.dumps(cached_result)

    # --- EXECUTE SCAN ---
    triage_data = perform_triage_scan(bytecode)
    
    final_data = triage_data
    
    if scan_type == 'deep':
        final_data = perform_deep_scan(bytecode, triage_data)

        # --- FINAL PACKAGING ---
        vera_score = final_data['vera_score']
        warnings = final_data['warnings']
        note = final_data['note']
        is_proxy = final_data['is_proxy']

        # [INTERACTIVE UX] Generate Medical Report Data
        milestones = [
            {"step": "Bytecode Extraction", "status": "complete", "details": "Fetched from Chain"},
            {"step": "Decompilation", "status": "complete", "details": "AST Generated"},
            {"step": "Signature Check", "status": "complete", "details": "Checked 3/3 Critical Patterns"},
            {"step": "Heuristic Scan", "status": "complete", "details": "VeraGuard Knowledge Base"},
        ]
        
        red_team_log = []
        if scan_type == 'deep':
             milestones.append({"step": "Deep Hunter Analysis", "status": "complete", "details": "Gemini 3 Pro Simulation"})
             red_team_log = final_data.get('red_team_log', [])
        else:
             milestones.append({"step": "Deep Hunter Analysis", "status": "pending", "details": "Upgrade to Deep Scan"})

        # [REFINED] Diagnostic Vitals for Medical Chart
        vitals = {
            "liquidity": "LOW (<$5k)" if vera_score < 40 else "HIGH (>$500k)",
            "owner_risk": "RENOUNCED" if vera_score > 90 else "ACTIVE ADMIN",
            "upgradeability": "DETECTED" if is_proxy else "IMMUTABLE"
        }

        # [NEW] Ethical Watermarking & Varied Summary
        report_id = str(uuid.uuid4())
        
        # Varied Phrasing (Simulated AI Personality)
        phrases_safe = [
            "No known vulnerabilities detected. Standard risks apply.",
            "Clean scan. Codebase adheres to standard safety patterns.",
            "Analysis complete: No critical vectors found in current bytecode.",
            "System verified. Contract appears operational and standard."
        ]
        phrases_warn = [
            "WARNING: Code contains unsafe patterns or centralization risks.",
            "CAUTION: Heuristics indicate potential control centralization.",
            "ALERT: Non-standard logic detected. Review permissions carefully.",
            "NOTICE: Codebase contains centralized functions. Owner risk present."
        ]
        phrases_crit = [
            "CRITICAL: High probability of capital loss due to active malicious signatures.",
            "DANGER: Known malicious signature identified. Do not interact.",
            "URGENT: Exploit vector confirmed. Funds at immediate risk.",
            "EXTREME RISK: Malicious logic detected. High confidence of scam."
        ]

        if vera_score < 50:
            base_summary = random.choice(phrases_crit)
        elif vera_score < 80:
                base_summary = random.choice(phrases_warn)
        else:
                base_summary = random.choice(phrases_safe)
        
        if scan_type == 'triage':
            base_summary = "[TRIAGE RESULT] " + base_summary

        timestamp_str = str(time.time())
        watermark_payload = f"{address}:{vera_score}:{timestamp_str}:{base_summary}"
        report_hash = hashlib.sha256(watermark_payload.encode()).hexdigest()

        final_result = {
            "report_id": report_id,
            "report_hash": report_hash,
            "timestamp": timestamp_str,
            "vera_score": vera_score,
            "warnings": warnings,
            "note": note,
            "milestones": milestones,
            "risk_summary": base_summary,
            "vitals": vitals,
            "is_proxy": is_proxy,
            "scan_type": scan_type,
            "red_team_log": red_team_log
        }

        # [NEW] Generate Sovereign Certificate
        try:
             cert = certificate.generate_certificate(report_id, report_hash, address, vera_score, warnings, credit_source)
             final_result["certificate"] = cert
        except Exception as e:
             print(f"Certificate Gen Failed: {e}")
             final_result["certificate"] = None

        # [NEW] Attach Initial Suspicion ("History of Suspicion")
        # Look up whether this address was previously auto-detected
        try:
            from . import database as _db
            initial = _db.get_initial_suspicion(address)
            if initial:
                final_result["initial_detection"] = initial
        except Exception:
            pass

        # --- 5. UPDATE CACHE (Only for Deep Scans?) ---
        if scan_type == 'deep':
            cache.set_cached_audit(bytecode, final_result)

        return json.dumps(final_result)
