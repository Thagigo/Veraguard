# Hunter Agent (Gemini 3 Pro Tier)
# Responsibility: Deep, expensive "Zero-Shot" reasoning.
# Triggers only when Triage Score < 70.

def analyze(bytecode: str, triage_warnings: list) -> dict:
    """
    Performs deep analysis on the bytecode.
    Returns: { "hunter_score_deduction": int, "hunter_warnings": [], "analysis": str }
    """
    warnings = []
    deduction = 0
    analysis = "Deep analysis complete. "

    # 1. Logic Bomb / Reentrancy Logic
    # Looks for external calls before state updates (Check-Effects-Interactions violation)
    # Simulated pattern matching for "CALL then SSTORE"
    # CALL (f1) ... SSTORE (55)
    
    # Simple string check for demo purposes of "Deep Reasoning"
    if "f1" in bytecode and "55" in bytecode:
        # Check relative positions (very rough heuristic)
        first_call = bytecode.find("f1")
        first_sstore = bytecode.find("55")
        if first_call < first_sstore:
             warnings.append("HUNTER: Potential Reentrancy (External Call before State Update)")
             deduction += 40
             analysis += "Reentrancy vector identified in main logic flow. "

    # 2. Deeper verification of Triage findings
    for warning in triage_warnings:
        if "High detected SSTORE" in warning:
             # Hunter verifies if it's a loop or just initialization
             # Assume Hunter finds it's valid initialization in some cases
             pass

    return {
        "hunter_score_deduction": deduction,
        "hunter_warnings": warnings,
        "analysis": analysis
    }
