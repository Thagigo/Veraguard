# Sovereign Utility Terms & Service-Level Guarantee

**Effective Date:** 2026-02-19

## 1. Nature of Utility Credits
Veraguard Credits ("CRD") are strictly functional utility tokens used to access the VeraGuard Audit Engine. They verify your request's priority in the computation queue.
- **NOT A SECURITY:** CRD are not investment contracts. They represent prepaid compute time.
- **NON-REFUNDABLE:** All sales are final upon cryptographic settlement, subject to the Service-Level Guarantee below.

## 2. Service-Level Guarantee (The "Anchor")
Veraguard guarantees that for every credit deducted, a **Verifiable Audit Proof** will be generated and anchored to the VeraGuard Ledger (or public chain).

**The "24-Hour Restitution" Clause:**
If an `Audit_Proof` hash is not pushed to the `VeraAnchor` smart contract within **24 hours** of credit deduction:
1. You are entitled to a full restitution of privacy-credits.
2. The `claimRestitution()` function on the `VeraAnchor` contract becomes executable by your wallet.

## 3. Data Privacy & "Vaporization"
- We do not store source code beyond the duration of the audit session.
- "Red Team" logs are generated ephemerally and then shredded from memory.
- You acknowledge that you are the authorized owner or administrator of the contracts you submit for audit.

## 4. Limitation of Liability
The VeraGuard Audit Engine uses probabilistic AI models (Gemini Pro/Flash). While we strive for 99.9% accuracy, false negatives are possible in non-deterministic environments.
- **NO WARRANTY:** The service is provided "AS IS".
- **MAX LIABILITY:** Limited to the value of the Credits used for the specific audit session.

---
*By interacting with the VeraAnchor contract, you cryptographically sign these terms.*
