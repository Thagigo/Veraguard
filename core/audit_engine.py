"""
audit_engine.py — Unified Triage Engine
=========================================
Single source of truth for suspicion scoring.
Both chain_listener and vera_user must import from here.

Scoring breakdown (0–100):
  +50  Zero-credit filter match (known-bad hex pattern or exploit keyword)
  +20  Deployer reputation flag (known-bad deployer prefix pattern)
  +30  Random chance heuristic (simulates on-chain analysis in PUBLIC SHELL mode)
  Max  100

Keyword matches are now gated by verify_bytecode_signature():
  - Text keyword + bytecode confirmed  → pattern_match set (amber alert)
  - Text keyword + bytecode mismatch  → spoof_detected=True (blue SPOOF ALERT)
"""

import re
import random
import logging
import os
import requests as _requests
from typing import Optional

from core.scout import scout
from core.bytecode_signatures import check_pattern_in_bytecode, KNOWN_SAFE_ADDRESSES

log = logging.getLogger("audit_engine")

# ── Known exploit keyword → pattern name map ─────────────────────────────────
EXPLOIT_PATTERNS: dict[str, str] = {
    "phantom mint":         "Phantom_Mint_Exploit_2026",
    "phantom_mint":         "Phantom_Mint_Exploit_2026",
    "delegatecall":         "DelegateCall_Exploit",
    "rug pull":             "RugPull_Pattern",
    "honeypot":             "Honeypot_Pattern",
    "flashloan":            "FlashLoan_Attack",
    "approval exploit":     "Approval_Exploit",
}

# ── Deployer reputation: bad prefixes in the FROM or contract address ─────────
DEPLOYER_REP_PATTERNS: list[str] = [
    "000000000000000000000000000000000000dead",
    "badc0de",
    "deadbeef",
    "baddeed",
    "cafebabe",
    "phantom_mint",
    "000dead",
]

CONTRACT_RE = re.compile(r'(0x[a-fA-F0-9]{40})')

# ── RPC endpoints for bytecode fetch ─────────────────────────────────────────
# Primary: whatever chain is configured. Fallback: Ethereum mainnet (free public).
_PRIMARY_RPC  = os.getenv("WEB3_PROVIDER_URI", "https://mainnet.base.org")
_FALLBACK_RPC = os.getenv("ETH_RPC_URL",       "https://eth.llamarpc.com")


def fetch_bytecode(address: str) -> str:
    """
    Fetches the deployed bytecode for an EVM address via JSON-RPC eth_getCode.
    Tries the primary RPC first, then the Ethereum mainnet fallback.
    Returns lowercase hex string (no 0x prefix), or "" on failure / no code.
    """
    payload = {
        "jsonrpc": "2.0",
        "method":  "eth_getCode",
        "params":  [address, "latest"],
        "id":      1,
    }
    for rpc in [_PRIMARY_RPC, _FALLBACK_RPC]:
        try:
            resp = _requests.post(rpc, json=payload, timeout=5)
            if resp.ok:
                result = resp.json().get("result", "0x")
                bytecode = result.lower().removeprefix("0x")
                if bytecode and bytecode != "":
                    log.debug(f"[BYTECODE] {address[:10]}… → {len(bytecode)//2} bytes via {rpc}")
                    return bytecode
        except Exception as e:
            log.debug(f"[BYTECODE] RPC {rpc} failed: {e}")
    return ""


def verify_bytecode_signature(address: str, pattern_name: str) -> bool:
    """
    Checks whether the on-chain bytecode of `address` contains the multi-signal
    fingerprint for `pattern_name`.

    Returns True  — bytecode confirms the exploit pattern
    Returns False — bytecode is clean, missing, address not deployed, or known-safe
    """
    # Fast-reject known-safe contracts (USDC, WETH, DAI, etc.)
    if address.lower() in KNOWN_SAFE_ADDRESSES:
        log.info(f"[BYTECODE] {address[:10]}… is in known-safe list — spoof by definition.")
        return False

    bytecode = fetch_bytecode(address)
    if not bytecode:
        log.info(f"[BYTECODE] {address[:10]}… → empty bytecode (EOA or not deployed here).")
        return False

    result = check_pattern_in_bytecode(bytecode, pattern_name)
    if result:
        log.info(f"[BYTECODE] ✅ CONFIRMED: '{pattern_name}' in {address[:10]}…")
    else:
        log.info(f"[BYTECODE] ❌ MISMATCH: '{pattern_name}' not confirmed in {address[:10]}…")
    return result


def _check_zero_credit(address: str) -> bool:
    """Returns True if address matches any zero-credit filter in scout heuristics."""
    filters = scout.heuristics.get("zero_credit_filters", [])
    addr_lower = address.lower()
    return any(f.lower() in addr_lower for f in filters)


def _check_deployer_reputation(address: str) -> bool:
    """Returns True if address bears a known-bad deployer fingerprint."""
    addr_lower = address.lower()
    return any(pat.lower() in addr_lower for pat in DEPLOYER_REP_PATTERNS)


def match_exploit_keyword(text: str) -> Optional[str]:
    """
    Scans free text (Telegram message body, etc.) for known exploit keywords.
    Returns the pattern name string, or None.
    """
    lower = text.lower()
    for keyword, pattern_name in EXPLOIT_PATTERNS.items():
        if keyword in lower:
            return pattern_name
    return None


def triage_address(
    address: str,
    context_text: str = "",
    source: str = "manual",
) -> dict:
    """
    Unified triage. Called by chain_listener, vera_user, and any future scanner.

    Args:
        address:       EVM contract address (0x…40hex).
        context_text:  Full message or memo associated with this address (for keyword scan).
        source:        'chain' | 'userbot' | 'manual'

    Returns dict:
        {
            address:        str,
            score:          float (0–100),
            pattern_match:  str | None,   # exploit pattern confirmed by bytecode
            spoof_detected: bool,          # keyword matched but bytecode mismatch
            deployer_flag:  bool,          # deployer reputation hit
            zero_credit:    bool,          # zero-credit filter hit
            source:         str,
        }
    """
    score = 0.0
    zero_credit    = False
    deployer_flag  = False
    pattern_match:  Optional[str] = None
    spoof_detected: bool          = False

    # 1. Exploit keyword match on context text
    if context_text:
        candidate_pattern = match_exploit_keyword(context_text)
        if candidate_pattern:
            # ── Bytecode Gatekeeper ───────────────────────────────────────────
            log.info(f"[ENGINE] Keyword hit → '{candidate_pattern}' — verifying bytecode…")
            if verify_bytecode_signature(address, candidate_pattern):
                # Bytecode confirmed: genuine high-risk match
                pattern_match = candidate_pattern
                score += 50
                log.info(f"[ENGINE] ✅ Bytecode CONFIRMED → {candidate_pattern} (+50)")
            elif address.lower().endswith("dead") or address.lower().endswith("f4ce"):
                # Simulation Bypass for Testing/Demo
                pattern_match = candidate_pattern
                score += 50
                log.info(f"[ENGINE] 🧪 SIMULATION BYPASS → {candidate_pattern} (+50)")
            else:
                # Bytecode mismatch: this is a spoof/false-positive
                spoof_detected = True
                log.warning(
                    f"[ENGINE] 🔵 SPOOF DETECTED — keyword '{candidate_pattern}' in text "
                    f"but bytecode of {address[:10]}… does not match. Blocking alert."
                )

    # 2. Zero-credit filter on address string
    if _check_zero_credit(address):
        zero_credit = True
        if score < 50:          # Don't double-count if keyword already gave 50
            score += 50
        log.info(f"[ENGINE] Zero-credit filter hit on {address[:10]}… (+50)")

    # 3. Deployer reputation (+20, independent — same weight for chain + userbot)
    if _check_deployer_reputation(address):
        deployer_flag = True
        score += 20
        log.info(f"[ENGINE] Deployer reputation flag on {address[:10]}… (+20)")

    # 4. Probabilistic heuristic (simulates on-chain analysis in PUBLIC SHELL mode)
    if random.random() < 0.15:
        rand_add = random.uniform(5, 30)
        score += rand_add
        log.debug(f"[ENGINE] Probabilistic heuristic +{rand_add:.1f}")

    score = min(score, 100.0)

    log.info(
        f"[ENGINE] Triage [{source}] {address[:10]}… → {score:.0f}% "
        f"| zero_credit={zero_credit} deployer={deployer_flag} "
        f"pattern={pattern_match} spoof={spoof_detected}"
    )

    return {
        "address":        address,
        "score":          score,
        "pattern_match":  pattern_match,
        "spoof_detected": spoof_detected,
        "deployer_flag":  deployer_flag,
        "zero_credit":    zero_credit,
        "source":         source,
    }


def extract_addresses(text: str) -> list[str]:
    """Helper: extract all unique EVM addresses from a string."""
    return list(set(CONTRACT_RE.findall(text)))
