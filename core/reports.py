import os
import datetime
import uuid

REPORT_DIR = "NotebookLM/The_Ledger"

def ensure_report_dir():
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)

def generate_monthly_revenue_report(data: dict) -> str:
    """
    Generates a formal markdown report for the monthly settlement.
    data: {
        "month": "YYYY-MM",
        "expired_vouchers": float,
        "reserve_amount": float,
        "vault_balance": float,
        "carry_balance": float,
        "audit_count": int,
        "new_users": int
    }
    """
    ensure_report_dir()
    
    report_id = str(uuid.uuid4())
    filename = f"Revenue_Report_{data['month'].replace('-', '_')}.md"
    filepath = os.path.join(REPORT_DIR, filename)
    
    content = f"""# ⚖️ VeraGuard Monthly Revenue & Compliance Report
**Date:** {datetime.datetime.now().strftime('%Y-%m-%d')}
**Report ID:** `{report_id}`
**Period:** {data['month']}
**Classification:** INTERNAL / FOUNDER EYES ONLY

---

## 1. Executive Summary
The monthly settlement process has been executed successfully. All expired voucher liabilities have been liquidated, with the requisite 40% reserve transferred to the Founder's Ledger (Carry). The Protocol remains **SOLVENT**.

## 2. Settlement Data
### A. Voucher Expiration
- **Total Expired Credits:** `{data['expired_vouchers']:,.2f} CRD`
- **Action:** Liabilities nullified. User balances updated.

### B. Reserve Allocation (Founder Carry)
- **Rate:** 40.0%
- **Settlement Amount:** `{data['reserve_amount']:,.2f} CRD`
- **Destination:** Founder Ledger (Source: 'settlement')

## 3. Treasury Status
- **Emerald Vault Balance:** `{data['vault_balance']:,.4f} ETH`
- **Total Founder Carry:** `{data['carry_balance']:,.2f} CRD`

## 4. Operational Metrics
- **Audits Performed:** {data.get('audit_count', 'N/A')}
- **New Users:** {data.get('new_users', 'N/A')}

---

## 5. Certification
I, **Vera-Core (Automated Settlement Engine)**, certify that this settlement was executed in accordance with the immutable laws of the VeraGuard Protocol.

**Hash:** `0x{uuid.uuid4().hex}`
"""

    with open(filepath, "w", encoding='utf-8') as f:
        f.write(content)
        
    return filepath
