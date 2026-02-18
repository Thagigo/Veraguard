
import sys
import os
import json
import time

# Ensure we can import core
sys.path.append(os.getcwd())

from core import database, audit_logic

def debug():
    print("1. Initializing DB...")
    try:
        database.init_db()
        print("DB Init Success.")
    except Exception as e:
        print(f"DB Init Failed: {e}")
        return

    print("2. Testing Rate Limit...")
    try:
        user_id = "test_verifier"
        limit_ok = database.check_rate_limit(user_id)
        print(f"Rate Limit Check: {limit_ok}")
    except Exception as e:
        print(f"Rate Limit Logic Failed: {e}")
        import traceback
        traceback.print_exc()

    print("3. Testing Audit Logic (Safe)...")
    try:
        address = "0xSafeContractForWatermarkTest"
        result_json = audit_logic.check_contract(address)
        result = json.loads(result_json)
        print("Audit Logic Success.")
        print(f"Keys: {list(result.keys())}")
        if 'report_id' not in result:
             print("ERROR: report_id still missing in simulation!")
    except Exception as e:
        print(f"Audit Logic Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("4. Testing Save Report...")
    try:
        if 'report_id' in result:
            database.save_audit_report(result['report_id'], result['report_hash'], address, result_json)
            print("Save Report Success.")
        else:
            print("Report ID missing, skipping save.")
    except Exception as e:
        print(f"Save Report Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug()
