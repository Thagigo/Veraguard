"""
Live-Synapse Worker: The Autonomous CNS.
Triggers on every Audit_Verdict (Bust) -> Generates Neuron_Packet -> Syncs to Brain (NotebookLM).
"""
import argparse
import sys
import os
import json
import time
import datetime
import requests
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io
from dotenv import load_dotenv
from . import database as db

load_dotenv()

# Configuration
VAULT_PATH = os.path.join("NotebookLM", "The_Vault")
DRIVE_SYNC_ENABLED = True # Enabled for production neural bridge
USER_EMAIL = os.getenv("USER_EMAIL") # Set this in .env for Service Account sharing

# Google API Config
SCOPES = ['https://www.googleapis.com/auth/drive.file']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'service_account.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')

def send_telegram_alert(message):
    """Sends a notification to the Admin Telegram ID."""
    token = os.getenv("BOT_TOKEN")
    admin_id = os.getenv("ADMIN_TELEGRAM_ID")
    if not token or not admin_id:
        print("[WARNING] Telegram credentials missing for alerts.")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": admin_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram alert: {e}")

def get_drive_service():
    """Authenticates and returns the Drive service."""
    creds = None
    is_sa = False
    
    # 1. Try Service Account
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        is_sa = True
    # 2. Try User Token
    elif os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # 3. Handle Refresh/Auth Flow (Only for User OAuth, Service Accounts are self-contained)
    if not creds or (not is_sa and not creds.valid):
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.path.exists(CREDENTIALS_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            else:
                return None, False
                
    return build('drive', 'v3', credentials=creds), is_sa

def ensure_folder_visible(service, folder_name="The_Vault"):
    """
    Ensures the folder exists and is in the 'root' for visibility.
    [Requirement 2 & 3]
    """
    # Search for folder with this name
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, parents)").execute()
    items = results.get('files', [])

    if not items:
        # Create at root [Requirement 2]
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': ['root']
        }
        folder = service.files().create(body=file_metadata, fields='id, webViewLink').execute()
        print(f"[DRIVE] Created fresh '{folder_name}' at Root.")
        return folder.get('id'), folder.get('webViewLink')
    else:
        folder = items[0]
        folder_id = folder['id']
        parents = folder.get('parents', [])
        
        # If not in root, move it [Requirement 2]
        if 'root' not in parents:
            print(f"[DRIVE] Folder '{folder_name}' exists but not at root. Moving...")
            # Remove existing parents and add root
            previous_parents = ",".join(parents)
            service.files().update(fileId=folder_id,
                                    addParents='root',
                                    removeParents=previous_parents,
                                    fields='id, parents').execute()
        
        # Get link
        f_data = service.files().get(fileId=folder_id, fields='webViewLink').execute()
        return folder_id, f_data.get('webViewLink')

def share_with_user(service, file_id, email, role='writer'):
    """Explicitly share with personal email if using Service Account [Requirement 1]"""
    if not email:
        print("[WARNING] No USER_EMAIL provided for sharing.")
        return False
    
    try:
        user_permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }
        service.permissions().create(
            fileId=file_id,
            body=user_permission,
            fields='id',
        ).execute()
        print(f"[DRIVE] shared '{file_id}' with {email} ({role})")
        return True
    except Exception as e:
        print(f"[DRIVE] Sharing failed: {e}")
        return False

def check_visibility():
    """[Requirement 4] Verification logic."""
    service, is_sa = get_drive_service()
    if not service:
        print("[ERROR] Could not initialize Drive. Credentials missing?")
        return
    
    print(f"[VERIFY] Auth Type: {'Service Account' if is_sa else 'User OAuth'}")
    
    try:
        folder_id, web_link = ensure_folder_visible(service)
        print(f"[VERIFY] Folder ID: {folder_id}")
        print(f"[VERIFY] Direct Link: {web_link}")
        
        if is_sa and USER_EMAIL:
            share_with_user(service, folder_id, USER_EMAIL, role='owner' if 'owner' in sys.argv else 'writer')
            
        success_msg = f"✅ *Neural Bridge Re-established*\nFolder ID: `{folder_id}`\n[Open in Drive]({web_link})"
        send_telegram_alert(success_msg)
        print("\n✅ NEURAL BRIDGE VISIBLE AT ROOT.")
    except Exception as e:
        fail_msg = f"❌ *Neural Bridge Visibility Failed*\nError: {str(e)}"
        send_telegram_alert(fail_msg)
        print(f"[FAIL] Folder not visible: {e}")

# Already defined above

def generate_neuron_packet(report):
    # report = (report_id, report_hash, address, data, vera_score)
    r_id, r_hash, address, data_json, score = report
    
    try:
        data = json.loads(data_json)
        risk_summary = data.get("risk_summary", "Unknown Vulnerability")
    except:
        data = {}
        risk_summary = "Parse Error"

    timestamp = datetime.datetime.now().isoformat()
    synapse_id = f"neu_{int(time.time())}_{r_id[-6:]}"

    packet = {
        "synapse_id": synapse_id,
        "timestamp": timestamp,
        "verdict": "BUST_CONFIRMED",
        "vera_score": score,
        "target_contract": address,
        "sheriff_notes": f"Automated flagging of {risk_summary}.",
        "exploit_vector": risk_summary,
        "technical_context": {
            "report_hash": r_hash,
            "raw_data_snippet": str(data)[:500] # Truncated for token optimization
        },
        "instruction_to_brain": "Analyze this exploit pattern. Update Heuristics/FAQ if novel."
    }
    return packet

def push_to_brain(packet):
    filename = f"Neuron_Packet_{packet['synapse_id']}.json"
    
    # 1. Local Persistence (The Vault)
    if not os.path.exists(VAULT_PATH):
        os.makedirs(VAULT_PATH, exist_ok=True)
        
    local_path = os.path.join(VAULT_PATH, filename)
    with open(local_path, "w") as f:
        json.dump(packet, f, indent=2)
        
    print(f"[SYNAPSE] Neuron Fired: {filename} -> {VAULT_PATH}")

    # 2. Google Drive Sync
    if DRIVE_SYNC_ENABLED:
        try:
            service, is_sa = get_drive_service()
            if service:
                folder_id, _ = ensure_folder_visible(service)
                
                if is_sa and USER_EMAIL:
                     share_with_user(service, folder_id, USER_EMAIL)

                # Upload file
                file_metadata = {
                    'name': filename,
                    'parents': [folder_id]
                }
                
                media = MediaIoBaseUpload(io.BytesIO(json.dumps(packet, indent=2).encode()), 
                                          mimetype='application/json')
                
                service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
                db.increment_neurons_active() # [NEW] Tracking neural evolution
                print(f"[DRIVE] Synced: {filename} -> Drive")
        except Exception as e:
            print(f"[DRIVE] Sync Error: {e}")
    
    return True

def run_loop():
    print("[SYNAPSE] Neural Bridge Active. Listening for Audit Verdicts...")
    while True:
        try:
            pending = db.get_pending_synapse_syncs()
            for r in pending:
                packet = generate_neuron_packet(r)
                if push_to_brain(packet):
                    db.mark_synapse_synced(r[0])
            
            time.sleep(5) # Fast poll for "Live" feel
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[SYNAPSE] Critical Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VeraGuard Synapse Worker")
    parser.add_argument("--check-visibility", action="store_true", help="Verification: Ensure folder is visible at root")
    args = parser.parse_args()

    if args.check_visibility:
        check_visibility()
    else:
        run_loop()
