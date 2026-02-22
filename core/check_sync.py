
"""
Brain-Sync Check: Monitors for 'Brain Lag'.
Compares the timestamp of Drive files/DB syncs with the last known NotebookLM sync time.
"""
import os
import sys
import time
import requests
from . import database as db

def check_sync_lag():
    lag_count = db.get_brain_lag()
    
    if lag_count > 0:
        print(f"[WARNING] BRAIN LAG: {lag_count} new patterns detected.")
        
        # Send Telegram Alert
        token = os.getenv("BOT_TOKEN")
        admin_id = os.getenv("ADMIN_TELEGRAM_ID")
        
        if token and admin_id:
            msg = f"⚠️ *BRAIN LAG*: `{lag_count}` new patterns detected.\nPlease re-upload `Brain_Digest.md` from Drive into NotebookLM to update your AI partner."
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": admin_id,
                "text": msg,
                "parse_mode": "Markdown"
            }
            try:
                requests.post(url, json=payload, timeout=10)
                print("[ALERT] Telegram notification sent.")
            except Exception as e:
                print(f"[ERROR] Failed to send Telegram alert: {e}")
        else:
            print("[ERROR] Telegram credentials missing for alerts.")
    else:
        print("[OK] Brain is up to date.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    db.init_db() # [NEW] Ensure migrations (like last_notebooklm_sync) are applied
    check_sync_lag()
