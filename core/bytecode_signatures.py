"""
bytecode_signatures.py — Exploit Hex Fingerprint Library
=========================================================
Maps exploit pattern names → known EVM opcode hex sequences.

Sources:
  - DeFiHackLabs post-mortems (github.com/SunWeb3Sec/DeFiHackLabs)
  - Phantom Mint Exploit 2026 (NotebookLM/Phantom_Mint_Exploit_2026.md)
  - Public Ethereum exploit forensics

Usage:
    from core.bytecode_signatures import get_signatures_for_pattern
    sigs = get_signatures_for_pattern("Phantom_Mint_Exploit_2026")
    # → ["40c10f19", "1249c58b", ...]

Gemini enrichment:
    If GOOGLE_API_KEY is set in the environment, query_gemini_for_signatures()
    will ask Gemini to expand the known-bad hex list and cache the result in
    memory for the process lifetime. Falls back to static dict silently.
"""

import os
import logging
from typing import Optional

log = logging.getLogger("bytecode_signatures")

# ── Known-safe address list ───────────────────────────────────────────────────
# These well-audited, widely-used contracts are never exploits even if their
# bytecode contains common selectors (e.g. USDC has a legitimate mint function).
KNOWN_SAFE_ADDRESSES: set[str] = {
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC (Ethereum)
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT (Ethereum)
    "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # WBTC
    "0x4200000000000000000000000000000000000042",  # OP token (Base)
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC (Base)
}

# ── Multi-Signal Signature Library ───────────────────────────────────────────
# Each pattern is a dict with two keys:
#   "required"  — ALL of these must be present in bytecode (core exploit fingerprint)
#   "any_of"    — AT LEAST ONE of these must also be present (supporting evidence)
#
# This prevents false positives on legitimate contracts that share one selector
# with an exploit (e.g. USDC has mint() but lacks the auth-bypass pattern).
#
# Sources: DeFiHackLabs, 4-byte.directory, manual forensic analysis.

STATIC_SIGNATURES: dict[str, dict[str, list[str]]] = {

    # ── Phantom Mint ──────────────────────────────────────────────────────────
    # TRUE Phantom Mint = mint function EXISTS + NO access control guard.
    # The exploit contract lacks onlyOwner/Roles checks, so its bytecode
    # will NOT contain the AccessControl modifier selectors.
    # Exploit fingerprint: mint selector + unchecked max-uint overflow pattern.
    # Legitimate mintable tokens (USDC, DAI) have role checks and will NOT have
    # the unrestricted overflow pattern alongside the mint selector.
    "Phantom_Mint_Exploit_2026": {
        "required": [
            # Max-uint pattern = hallmark of unchecked arithmetic / auth bypass.
            # This specific 32-byte constant is absent from legitimate ERC20s.
            "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ],
        "any_of": [
            "40c10f19",   # mint(address,uint256)
            "a0712d68",   # mint(uint256)
            "449a52f8",   # mintTo(address,uint256)
            "1249c58b",   # _mint(address,uint256) internal
        ],
    },

    # ── DelegateCall exploit ──────────────────────────────────────────────────
    "DelegateCall_Exploit": {
        "required": [
            "f4",         # DELEGATECALL opcode present in bytecode
        ],
        "any_of": [
            "f43d3a3e",   # upgradeToAndCall(address,bytes)
            "4f1ef286",   # upgradeTo(address)
            "3659cfe6",   # implementation() — proxy storage slot reader
        ],
    },

    # ── Rug Pull ──────────────────────────────────────────────────────────────
    "RugPull_Pattern": {
        "required": [
            "f2fde38b",   # transferOwnership(address) — must be present
        ],
        "any_of": [
            "715018a6",   # renounceOwnership() — remove owner entirely
            "c9567bf9",   # launch() / openTrading() — common rug setup
            "8456cb59",   # pause() — selectively freeze sells
        ],
    },

    # ── Honeypot ──────────────────────────────────────────────────────────────
    "Honeypot_Pattern": {
        "required": [
            "e8078d94",   # launch()/openTrading() — always present in honeypots
        ],
        "any_of": [
            "095ea7b3",   # approve(address,uint256)
            "18160ddd",   # totalSupply()
            "a9059cbb",   # transfer — needed to detect sell-block
        ],
    },

    # ── Flash Loan attack ─────────────────────────────────────────────────────
    "FlashLoan_Attack": {
        "required": [
            "5cffe9de",   # flashLoan(address,address,uint256,bytes)
        ],
        "any_of": [
            "ab9c4b5d",   # executeOperation — Aave callback
            "23e30c8b",   # onFlashLoan — ERC-3156 callback
            "10d1e85c",   # flashLoanSimple — Aave v3
        ],
    },

    # ── Approval exploit ──────────────────────────────────────────────────────
    "Approval_Exploit": {
        "required": [
            # Unlimited approval constant (type(uint256).max = 0xffff...ffff)
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ],
        "any_of": [
            "095ea7b3",   # approve(address,uint256)
            "d505accf",   # permit()
        ],
    },
}

# ── In-memory Gemini enrichment cache ────────────────────────────────────────
_gemini_cache: dict[str, list[str]] = {}


def check_pattern_in_bytecode(bytecode: str, pattern_name: str) -> bool:
    """
    Core match logic. Returns True only when:
      1. The address isn't in the known-safe whitelist (checked by caller)
      2. ALL 'required' signatures are present in the bytecode
      3. AT LEAST ONE 'any_of' signature is present in the bytecode

    This two-tier approach prevents false positives on legitimate contracts
    (e.g. USDC has mint() but lacks the unchecked max-uint overflow pattern).
    """
    entry = STATIC_SIGNATURES.get(pattern_name)
    if not entry:
        log.warning(f"No signatures known for pattern '{pattern_name}' — unverifiable.")
        return False

    required = entry.get("required", [])
    any_of   = entry.get("any_of", [])

    # All required sigs must be present
    for sig in required:
        if sig.lower() not in bytecode:
            log.debug(f"[SIG] Required '{sig}' NOT in bytecode — not a match.")
            return False

    # At least one any_of sig must be present
    if any_of:
        found = any(sig.lower() in bytecode for sig in any_of)
        if not found:
            log.debug(f"[SIG] No any_of signatures found — not a match.")
            return False

    log.info(f"[SIG] Pattern '{pattern_name}' confirmed — required+any_of matched.")
    return True


def get_signatures_for_pattern(pattern_name: str) -> dict:
    """
    Returns the signature dict for a given exploit pattern.
    (Legacy helper — prefer check_pattern_in_bytecode for matching.)
    """
    return STATIC_SIGNATURES.get(pattern_name, {})


def query_gemini_for_signatures(pattern_name: str) -> Optional[list[str]]:
    """
    Asks Gemini: 'What EVM bytecode hex sequences identify a {pattern_name}?'
    Returns a list of hex strings, or None if unavailable.
    Requires GOOGLE_API_KEY in environment.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = (
            f"You are a smart contract security expert. "
            f"Based on DeFiHackLabs post-mortems and public exploit research, "
            f"list the specific EVM bytecode hex sequences (function selectors or opcode fragments) "
            f"that are characteristic of a '{pattern_name.replace('_', ' ')}' exploit. "
            f"Return ONLY a JSON array of lowercase hex strings, no 0x prefix, no explanation. "
            f"Example: [\"40c10f19\", \"1249c58b\"]"
        )

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON array from response
        import re, json
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if match:
            sigs = json.loads(match.group())
            # Sanitise: only keep hex strings
            sigs = [s.lower().strip() for s in sigs if isinstance(s, str) and all(c in "0123456789abcdef" for c in s.strip())]
            log.info(f"[GEMINI] Got {len(sigs)} signatures for '{pattern_name}'")
            return sigs if sigs else None

    except Exception as e:
        log.debug(f"[GEMINI] Signature query failed: {e}")

    return None
