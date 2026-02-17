# Triage Agent (Gemini 3 Flash Tier)
# Responsibility: Fast, low-cost scanning for obvious issues.

def scan(bytecode: str) -> dict:
    """
    Performs a fast scan of the bytecode.
    Returns: { "triage_score": 0-100, "triage_warnings": [] }
    """
    warnings = []
    triage_score = 100

    # 1. Gas Spike Detection (Loop Patterns)
    # Looking for JUMPDEST followed by costly ops in a loop structure (simplified heuristic)
    # OpCodes: 0x5b (JUMPDEST), 0x55 (SSTORE), 0x54 (SLOAD)
    # A real implementation would construct a CFG. Here we look for density of SSTOREs.
    sstore_count = bytecode.count("55")
    if sstore_count > 50: # Arbitrary threshold for "high gas potential"
        warnings.append("TRIAGE: High detected SSTORE count (Gas Spike Risk)")
        triage_score -= 10

    # 2. Suspicious Imports
    # Look for known malicious library hashes or patterns
    # (Simulated check)
    if "bad1dea" in bytecode:
        warnings.append("TRIAGE: Suspicious library import detected")
        triage_score -= 30

    # 3. Basic Code Quality
    if len(bytecode) < 50:
         warnings.append("TRIAGE: Contract size too small (Likely incomplete or proxy)")
         triage_score -= 5

    return {
        "triage_score": max(0, triage_score),
        "triage_warnings": warnings
    }
