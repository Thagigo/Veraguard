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

# Tracks folder IDs already shared this session — prevents repeated invitation emails
_shared_folder_ids: set[str] = set()

# Cached Drive file ID for Brain_Digest.md — avoids repeated searches
_digest_file_id: str | None = None
DIGEST_FILENAME = "Brain_Digest.md"

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
        print("\n[SUCCESS] NEURAL BRIDGE VISIBLE AT ROOT.")
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

def get_upload_service():
    """
    Returns a Drive service authenticated as the USER (OAuth), not the service account.
    Service accounts cannot upload files to regular Drive (no storage quota).
    Falls back gracefully if no OAuth token exists.
    """
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.valid:
            return build('drive', 'v3', credentials=creds)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as t:
                t.write(creds.to_json())
            return build('drive', 'v3', credentials=creds)
    print("[DRIVE] No token.json — service account cannot upload files (no quota).")
    print("[DRIVE] Run: python -m core.synapse_worker --authorize  to enable Drive uploads.")
    return None

def compile_brain_digest() -> str:
    """
    Reads all Neuron_Packet_*.json files from The_Vault and compiles them
    into a single structured markdown document for NotebookLM.
    """
    packets = []
    if os.path.exists(VAULT_PATH):
        for fname in sorted(os.listdir(VAULT_PATH)):
            if fname.startswith("Neuron_Packet_") and fname.endswith(".json"):
                try:
                    with open(os.path.join(VAULT_PATH, fname)) as f:
                        packets.append(json.load(f))
                except Exception:
                    pass

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    lines = [
        "# VeraGuard Brain Digest",
        f"> Auto-generated by Synapse Worker. Last updated: {now}",
        f"> Total exploits documented: {len(packets)}",
        "",
        "---",
        "",
        "## Context for NotebookLM",
        "This document is a rolling digest of confirmed smart contract exploits detected by",
        "the VeraGuard system. Each section represents a single confirmed bust. Use these",
        "patterns to update your heuristics, FAQ, and threat model.",
        "",
        "---",
        "",
    ]

    for p in packets:
        ts = p.get("timestamp", "unknown")[:10]
        exploit = p.get("exploit_vector", "Unknown")
        address = p.get("target_contract", "unknown")
        score = p.get("vera_score", "?")
        notes = p.get("sheriff_notes", "")
        synapse_id = p.get("synapse_id", "")
        ctx = p.get("technical_context", {})
        report_hash = ctx.get("report_hash", "")

        lines += [
            f"## [BUST] {exploit} — {ts}",
            f"- **Synapse ID**: `{synapse_id}`",
            f"- **Address**: `{address}`",
            f"- **Vera Score**: {score}/100 (lower = more dangerous)",
            f"- **Sheriff Notes**: {notes}",
            f"- **Report Hash**: `{report_hash}`",
            f"- **Instruction**: Analyze this exploit. Update Heuristics/FAQ if this pattern is novel.",
            "",
            "---",
            "",
        ]

    if not packets:
        lines += ["_No confirmed busts recorded yet._", ""]

    return "\n".join(lines)


def push_digest_to_drive() -> bool:
    """
    Compiles the Brain_Digest.md from all local Neuron Packets and upserts
    it to Drive (update existing file in-place, or create it if first time).
    Uses 1 Drive source slot in NotebookLM forever.
    """
    global _digest_file_id

    upload_svc = get_upload_service()
    if not upload_svc:
        print("[DIGEST] No OAuth token — skipping Drive digest sync.")
        return False

    sa_service, is_sa = get_drive_service()
    folder_id, folder_link = ensure_folder_visible(sa_service)

    # Share folder once per session
    if is_sa and USER_EMAIL and folder_id not in _shared_folder_ids:
        share_with_user(sa_service, folder_id, USER_EMAIL)
        _shared_folder_ids.add(folder_id)

    digest_md = compile_brain_digest()
    
    # Save a local copy for transparency — helps the user verify what is being synced
    local_digest_path = os.path.join("NotebookLM", DIGEST_FILENAME)
    try:
        with open(local_digest_path, "w", encoding="utf-8") as f:
            f.write(digest_md)
        print(f"[DIGEST] Saved local copy to {local_digest_path}")
    except Exception as e:
        print(f"[DIGEST] Local save error: {e}")

    media = MediaIoBaseUpload(
        io.BytesIO(digest_md.encode("utf-8")),
        mimetype="text/markdown"
    )

    try:
        if _digest_file_id:
            # Update existing file in-place (no new source slot in NotebookLM)
            upload_svc.files().update(
                fileId=_digest_file_id,
                media_body=media
            ).execute()
            print(f"[DIGEST] Updated Brain_Digest.md in Drive (id={_digest_file_id})")
        else:
            # Search Drive for an existing digest file first
            r = upload_svc.files().list(
                q=f"'{folder_id}' in parents and name='{DIGEST_FILENAME}' and trashed=false",
                fields="files(id)",
                pageSize=1
            ).execute()
            existing = r.get("files", [])

            if existing:
                _digest_file_id = existing[0]["id"]
                upload_svc.files().update(
                    fileId=_digest_file_id,
                    media_body=media
                ).execute()
                print(f"[DIGEST] Updated Brain_Digest.md in Drive (id={_digest_file_id})")
            else:
                # First time — create the file
                result = upload_svc.files().create(
                    body={"name": DIGEST_FILENAME, "parents": [folder_id]},
                    media_body=media,
                    fields="id"
                ).execute()
                _digest_file_id = result["id"]
                print(f"[DIGEST] Created Brain_Digest.md in Drive (id={_digest_file_id})")
                print(f"[DIGEST] Add this file as a source in NotebookLM: {folder_link}")

        return True
    except Exception as e:
        print(f"[DIGEST] Drive sync error: {e}")
        return False


def push_to_brain(packet):
    filename = f"Neuron_Packet_{packet['synapse_id']}.json"
    
    # 1. Local Persistence (The Vault) — always runs
    if not os.path.exists(VAULT_PATH):
        os.makedirs(VAULT_PATH, exist_ok=True)
        
    local_path = os.path.join(VAULT_PATH, filename)
    with open(local_path, "w") as f:
        json.dump(packet, f, indent=2)
        
    print(f"[SYNAPSE] Neuron Fired: {filename} -> {VAULT_PATH}")

    # 2. Google Drive Sync — consolidation into rolling digest
    if DRIVE_SYNC_ENABLED:
        push_digest_to_drive()
    
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

def run_authorize():
    """
    One-time OAuth authorization flow.
    Opens a browser window, asks you to log in with your Google account,
    and saves the resulting token to core/token.json.
    Requires core/credentials.json (download from Google Cloud Console).
    """
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"[AUTH] ERROR: credentials.json not found at {CREDENTIALS_FILE}")
        print("[AUTH] Steps to get it:")
        print("  1. Go to https://console.cloud.google.com")
        print("  2. APIs & Services -> Credentials -> Create Credentials -> OAuth client ID")
        print("  3. Application type: Desktop app")
        print("  4. Download JSON -> save as core/credentials.json")
        return

    print("[AUTH] Starting OAuth flow — your browser will open...")
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print(f"[AUTH] SUCCESS — token saved to {TOKEN_FILE}")
    print("[AUTH] Drive uploads will now work. Restart synapse_worker.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VeraGuard Synapse Worker")
    parser.add_argument("--check-visibility", action="store_true", help="Verify Drive folder is visible at root")
    parser.add_argument("--authorize", action="store_true", help="One-time OAuth login to enable Drive file uploads")
    args = parser.parse_args()

    if args.check_visibility:
        check_visibility()
    elif args.authorize:
        run_authorize()
    else:
        run_loop()
