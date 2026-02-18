
import sqlite3
import json

def check_db():
    conn = sqlite3.connect('credits.db')
    c = conn.cursor()
    c.execute("SELECT report_id, report_hash, address, data FROM audit_reports ORDER BY timestamp DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if row:
        print(f"LATEST REPORT ID: {row[0]}")
        print(f"HASH: {row[1]}")
        print(f"ADDRESS: {row[2]}")
        data = json.loads(row[3])
        if 'report_id' in data and 'risk_summary' in data:
            print("VERIFICATION SUCCESS: Data JSON contains report_id and risk_summary.")
        else:
            print("VERIFICATION FAILED: Data JSON missing key fields.")
    else:
        print("VERIFICATION FAILED: No reports found in DB.")

if __name__ == "__main__":
    check_db()
