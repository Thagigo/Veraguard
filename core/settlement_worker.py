import time
import datetime
import uuid
try:
    from . import database
    from . import reports
except ImportError:
    import database
    import reports

def get_start_of_current_month():
    now = datetime.datetime.now()
    return datetime.datetime(now.year, now.month, 1).timestamp()

def run_settlement():
    print("--- Starting Monthly Settlement ---")
    
    cutoff = get_start_of_current_month()
    print(f"Cutoff Timestamp: {cutoff}")
    
    expired_amount = database.expire_vouchers(cutoff)
    print(f"Total Expired Vouchers: {expired_amount} Credits")
    
    # Always generate report even if 0 expired? Ideally yes for compliance.
    # But logic was 'if expired_amount > 0'. Let's keep it but maybe record 0 settlement.
    
    reserve_share = 0.0
    if expired_amount > 0:
        # Calculate Reserve (40%)
        reserve_share = expired_amount * 0.40
        # Record to Founder Ledger
        database.record_founder_carry(reserve_share, 'settlement')
        print(f"Settlement Executed: {reserve_share} Credits moved to Founder Ledger.")
    else:
        print("No vouchers to expire.")

    # Generate Report
    stats = database.get_executive_stats()
    
    report_data = {
        "month": datetime.datetime.now().strftime('%Y-%m'),
        "expired_vouchers": expired_amount,
        "reserve_amount": reserve_share,
        "vault_balance": stats['vault_balance_eth'],
        "carry_balance": stats['total_carry'],
        "audit_count": 0, # Placeholder
        "new_users": 0 # Placeholder
    }
    
    filepath = reports.generate_monthly_revenue_report(report_data)
    print(f"Report Generated: {filepath}")

if __name__ == "__main__":
    # Create The_Ledger if not exists
    import os
    if not os.path.exists("NotebookLM/The_Ledger"):
        os.makedirs("NotebookLM/The_Ledger")
        
    run_settlement()
