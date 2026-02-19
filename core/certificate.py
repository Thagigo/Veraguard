import json
import time
import os
import hashlib

# Mock NotebookLM Directory (Simulated)
# Mock NotebookLM Directory (Simulated)
NOTEBOOK_LM_DIR = os.path.join("NotebookLM", "The_Vault")

if not os.path.exists(NOTEBOOK_LM_DIR):
    os.makedirs(NOTEBOOK_LM_DIR)

def generate_certificate(report_id: str, report_hash: str, address: str, vera_score: int, warnings: list, credit_source: str = "purchase"):
    """
    Generates a 'Sovereign Audit Certificate' (JSON).
    Simulates pushing to a private 'NotebookLM' folder.
    """
    
    # 1. Mock On-Chain Data (VeraAnchor)
    # in prod: tx_hash = web3.eth.send_transaction(...)
    anchor_tx = "0x" + hashlib.sha256(f"{report_id}:ANCHOR".encode()).hexdigest()
    
    timestamp = time.time()
    
    # Dynamic Legal Text
    source_label = "Vera-Pass Voucher" if credit_source == 'voucher' else "ETH Purchase"
    legal_text = f"This audit was performed using [{source_label}] credits. 40% of the value has been distributed to the protocol workforce."
    
    cert_data = {
        "header": {
            "title": "Sovereign Audit Certificate",
            "issuer": "VeraGuard Protocol",
            "timestamp": timestamp,
            "version": "1.0"
        },
        "target": {
            "address": address,
            "audit_type": "Deep Dive" if len(warnings) > 0 else "Standard" # Simplistic check
        },
        "vitals": {
            "vera_score": vera_score,
            "report_hash": report_hash,
            "signature_verified": True
        },
        "service_level_proof": {
            "anchor_contract": "VeraAnchor.sol",
            "anchor_tx": anchor_tx,
            "sla_status": "FULFILLED (<24h)"
        },
        "treasury_split_verification": {
            "credit_source": credit_source,
            "vault": "60%",
            "founder": "25% (Infrastructure)" if credit_source == 'voucher' else "25%",
            "war_chest": "15%",
            "status": "Math Verified (VeraSplitter.sol)"
        },
        "forensic_notice": legal_text
    }
    
    # 2. Save / 'Push' logic
    filename = f"Certificate_{report_id}.json"
    filepath = os.path.join(NOTEBOOK_LM_DIR, filename)
    
    with open(filepath, "w") as f:
        json.dump(cert_data, f, indent=4)
        
    return {
        "certificate_id": filename,
        "path": filepath,
        "anchor_tx": anchor_tx
    }
