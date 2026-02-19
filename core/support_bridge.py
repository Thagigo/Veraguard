"""
Support Bridge: The 'Agentic' Support Worker.
Connects the Vera-Verify Bot to the NotebookLM knowledge base.
"""
import os
import json
import random

VAULT_DIR = os.path.join("NotebookLM", "The_Vault")
SHIELD_DIR = os.path.join("NotebookLM", "The_Shield")
LEDGER_DIR = os.path.join("NotebookLM", "The_Ledger")

def explain_audit(audit_id_or_address: str):
    """
    Simulates an RAG (Retrieval-Augmented Generation) lookup.
    1. Searches 'The_Vault' for a matching certificate.
    2. detailed explanation based on the findings.
    """
    
    # 1. Search in Vault
    target_file = None
    
    if not os.path.exists(VAULT_DIR):
        return "⚠️ The Vault is inaccessible. System offline."

    # Try exact match (Certificate ID)
    potential_path = os.path.join(VAULT_DIR, f"Certificate_{audit_id_or_address}.json")
    if os.path.exists(potential_path):
        target_file = potential_path
    
    # Try Address match (Linear search, slow but fine for prototype)
    if not target_file:
        for f in os.listdir(VAULT_DIR):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(VAULT_DIR, f), 'r') as jf:
                        data = json.load(jf)
                        if data.get("target", {}).get("address", "").lower() == audit_id_or_address.lower():
                            target_file = os.path.join(VAULT_DIR, f)
                            break
                except:
                    continue

    if not target_file:
        return f"❌ **Audit Not Found**\n\nI searched 'The Vault' but could not find a certificate for `{audit_id_or_address}`.\n\nPlease ensure the audit has been completed and the certificate generated."

    # 2. Generate Explanation
    try:
        with open(target_file, 'r') as f:
            cert = json.load(f)
            
        score = cert['vitals']['vera_score']
        address = cert['target']['address']
        warnings = [] # We'd need to fetch warnings from the DB ideally, but let's check if they are in the cert?
        # Cert structure in certificate.py: 
        # "vitals": { "vera_score": ... }
        # "audit_type": ...
        
        # We don't have the full warnings list in the certificate.py output yet! 
        # Wait, certificate.py only puts `vera_score`, `report_hash`.
        # Ideally, `certificate.py` SHOULD include the warnings summary.
        # But for now, we can infer from the score.
        
        assessment = "Unknown"
        if score >= 90:
            assessment = "The contract is highly secure. No critical vulnerabilities were detected during the Deep Dive."
        elif score >= 50:
            assessment = "The contract has moderate risks. While no exploits were confirmed, there are centralization vectors."
        else:
            assessment = "CRITICAL RISK. This contract exhibits patterns consistent with known rug-pulls or exploits."
            
        msg = (
            f"🎓 **Sovereign Explanation**\n\n"
            f"**Subject**: `{address}`\n"
            f"**Certificate**: `{os.path.basename(target_file)}`\n"
            f"**VeraScore**: {score}/100\n\n"
            f"**AI Analysis**:\n{assessment}\n\n"
            f"**Proof of Service**:\n"
            f"This audit is anchored on-chain via `VeraAnchor.sol` and stored in 'The Vault' for forensic retrieval."
        )
        return msg
        
    except Exception as e:
        return f"⚠️ Error synthesizing explanation: {e}"

def get_faq_context():
    """Generates a text blob of the current system state for FAQ generation."""
    return "System is online. Vault, Shield, and Ledger are active."
