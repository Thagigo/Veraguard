"""
Verbose Drive upload test — uploads one JSON file to The_Vault and prints
every error detail so we can see exactly why uploads are failing.
"""
import sys, os, json, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv; load_dotenv()

from core.synapse_worker import get_drive_service, ensure_folder_visible

print("[TEST] Getting Drive service...")
service, is_sa = get_drive_service()
print(f"[TEST] Auth type: {'Service Account' if is_sa else 'OAuth'}")

print("[TEST] Getting folder...")
folder_id, link = ensure_folder_visible(service)
print(f"[TEST] Folder ID: {folder_id}")

test_packet = {"test": True, "msg": "Drive upload diagnostic", "folder": folder_id}
content = json.dumps(test_packet, indent=2).encode()

print("[TEST] Uploading test file...")
try:
    from googleapiclient.http import MediaIoBaseUpload
    file_metadata = {"name": "TEST_diagnostic.json", "parents": [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/json")
    result = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink"
    ).execute()
    print(f"[OK] Uploaded! File ID: {result.get('id')}")
    print(f"[OK] Link: {result.get('webViewLink')}")

    # Also share the file directly
    USER_EMAIL = os.getenv("USER_EMAIL")
    if USER_EMAIL:
        service.permissions().create(
            fileId=result["id"],
            body={"type": "user", "role": "reader", "emailAddress": USER_EMAIL},
            fields="id",
            sendNotificationEmail=False
        ).execute()
        print(f"[OK] Shared with {USER_EMAIL} (no email sent)")
except Exception as e:
    import traceback
    print(f"[FAIL] Upload error:")
    traceback.print_exc()
