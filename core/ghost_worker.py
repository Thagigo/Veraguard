"""
Ghost Worker: Technical Debt Collector & Public Town Crier.
Runs in the background to:
1. Push certificates to 'NotebookLM' (Google Drive Simulation).
2. Broadcast public alerts to Telegram channel for low-score contracts.
"""
import time
import json
import os
import shutil
import requests
from dotenv import load_dotenv
from . import database as db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Channel ID for public alerts (e.g. @VeraVerify channel)
# For now, we can use the ADMIN_ID as a test, or a specific channel logic.
CHANNEL_ID = os.getenv("ADMIN_TELEGRAM_ID") 

def send_telegram_alert(message: str):
    """Sends a message via Telegram Bot API (Raw HTTP for speed/simplicity in worker)."""
    if not BOT_TOKEN:
        print("[GHOST] Error: No BOT_TOKEN found.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            return True
        else:
            print(f"[GHOST] Telegram Access Failed: {res.text}")
            return False
    except Exception as e:
        print(f"[GHOST] Telegram Sync Error: {e}")
        return False

def format_alert_message(report):
    # report = (report_id, address, vera_score, data)
    r_id, address, score, data_json = report
    try:
        data = json.loads(data_json)
        scam_type = data.get("risk_summary", "Unknown Threat")
    except:
        scam_type = "Analysis Failed"
    
    emoji = "🔴" if score < 30 else "🟠"
    
    msg = (f"{emoji} *VeraGuard Alert*\n"
           f"Contract: `{address[:6]}...{address[-4:]}`\n"
           f"VeraScore: *{score}/100*\n"
           f"Threat: _{scam_type}_\n\n"
           f"[View Protocol Ledger](https://veraguard.app/ledger/{r_id})")
    return msg

def sync_to_notebook_lm(report):
    # report = (report_id, report_hash, address, data)
    r_id, r_hash, addr, data = report
    
    # Check The Vault (Source of Truth)
    cert_filename = f"Certificate_{r_id}.json"
    vault_path = os.path.join("NotebookLM", "The_Vault", cert_filename)
    
    if os.path.exists(vault_path):
        print(f"[GHOST] Verified {cert_filename} in The Vault. Marking synced.")
        return True
    else:
        # If certificate isn't there yet, we wait (it might be generating)
        # But if it's been a long time, we might just skip.
        # For simulation, we assume if it's not there, it's not ready.
        return False

def run_loop():
    print("[GHOST] Worker Active. Monitoring Audit Trail...")
    while True:
        try:
            # 1. Public Alerts
            pending_alerts = db.get_pending_public_alerts()
            for r in pending_alerts:
                # r = (report_id, address, vera_score, data)
                msg = format_alert_message(r)
                if send_telegram_alert(msg):
                    db.mark_alert_sent(r[0])
                    print(f"[GHOST] Alert Sent for {r[1]}")
                time.sleep(1) # Rate limit protection

            # 2. Drive Sync
            pending_syncs = db.get_pending_syncs()
            for r in pending_syncs:
                # r = (report_id, report_hash, address, data)
                if sync_to_notebook_lm(r):
                    db.mark_synced(r[0])
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[GHOST] Critical Loop Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_loop()
