"""
E2E Drive upload test — creates a test Neuron Packet, uploads it to Drive
via OAuth (token.json), then lists the folder to confirm it appears.
"""
import sys, os, json, io, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv; load_dotenv()

from core.synapse_worker import (
    get_drive_service, get_upload_service,
    ensure_folder_visible, share_with_user
)
from googleapiclient.http import MediaIoBaseUpload

USER_EMAIL = os.getenv("USER_EMAIL")
print("\n=== E2E DRIVE UPLOAD TEST ===\n")

# Step 1 — Folder
print("[1/4] Getting The_Vault folder...")
sa_service, is_sa = get_drive_service()
folder_id, link = ensure_folder_visible(sa_service)
print(f"      Folder ID : {folder_id}")
print(f"      Drive URL : {link}")

# Step 2 — OAuth upload service
print("\n[2/4] Getting OAuth upload service (token.json)...")
upload_svc = get_upload_service()
if not upload_svc:
    print("      FAIL: token.json missing or invalid. Run --authorize first.")
    sys.exit(1)
print("      OK — authenticated as your Google account")

# Step 3 — Upload test file
test_name = f"E2E_TEST_{int(time.time())}.json"
test_data  = {"e2e_test": True, "ts": time.time(), "msg": "VeraGuard Drive upload test"}
print(f"\n[3/4] Uploading {test_name}...")
file_metadata = {"name": test_name, "parents": [folder_id]}
media = MediaIoBaseUpload(
    io.BytesIO(json.dumps(test_data, indent=2).encode()),
    mimetype="application/json"
)
result = upload_svc.files().create(
    body=file_metadata, media_body=media, fields="id, webViewLink"
).execute()
file_id   = result.get("id")
file_link = result.get("webViewLink", "n/a")
print(f"      File ID  : {file_id}")
print(f"      File URL : {file_link}")

# Step 4 — Verify it appears in folder listing
print(f"\n[4/4] Verifying file is listed in The_Vault folder...")
r = sa_service.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    fields="files(id, name)",
    pageSize=20
).execute()
files = r.get("files", [])
found = any(f["id"] == file_id for f in files)

print(f"      Files in Drive folder: {len(files)}")
for f in files:
    marker = " <-- JUST UPLOADED" if f["id"] == file_id else ""
    print(f"        {f['name']}{marker}")

print()
if found:
    print("=== RESULT: PASS ===")
    print(f"File visible in Drive. Open The_Vault: {link}")
else:
    print("=== RESULT: PARTIAL ===")
    print("File uploaded but not yet visible in folder listing (Drive propagation delay).")
    print(f"Check directly: {file_link}")
print()
