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
"""

import re
import random
import logging
from typing import Optional

from core.scout import scout

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
            pattern_match:  str | None,   # exploit pattern name if keyword hit
            deployer_flag:  bool,          # deployer reputation hit
            zero_credit:    bool,          # zero-credit filter hit
            source:         str,
        }
    """
    score = 0.0
    zero_credit = False
    deployer_flag = False
    pattern_match: Optional[str] = None

    # 1. Exploit keyword match on context text (highest priority signal)
    if context_text:
        pattern_match = match_exploit_keyword(context_text)
        if pattern_match:
            score += 50
            log.info(f"[ENGINE] Keyword hit → {pattern_match} (+50)")

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
        f"| zero_credit={zero_credit} deployer={deployer_flag} pattern={pattern_match}"
    )

    return {
        "address":       address,
        "score":         score,
        "pattern_match": pattern_match,
        "deployer_flag": deployer_flag,
        "zero_credit":   zero_credit,
        "source":        source,
    }


def extract_addresses(text: str) -> list[str]:
    """Helper: extract all unique EVM addresses from a string."""
    return list(set(CONTRACT_RE.findall(text)))
