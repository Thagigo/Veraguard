import os
import json
from core import support_bridge

# 1. Create a Keyframe Certificate (Mocking a completed audit)
mock_cert = {
    "header": { "title": "Sovereign Audit Certificate" },
    "target": { "address": "0x1234567890abcdef1234567890abcdef12345678" },
    "vitals": { "vera_score": 92, "report_hash": "0xabc..." },
    "audit_type": "Deep Dive"
}

vault_path = os.path.join("NotebookLM", "The_Vault")
if not os.path.exists(vault_path):
    os.makedirs(vault_path)

cert_path = os.path.join(vault_path, "Certificate_TEST_AUDIT.json")
with open(cert_path, "w") as f:
    json.dump(mock_cert, f)

print(f"Created Mock Certificate at {cert_path}")

# 2. Test Explain Function
print("\n--- Testing /explain 0x1234... ---")
response = support_bridge.explain_audit("0x1234567890abcdef1234567890abcdef12345678")
print(response)

# 3. Test Fail Case
print("\n--- Testing /explain INVALID ---")
response_fail = support_bridge.explain_audit("0x9999999999999999999999999999999999999999")
print(response_fail)
