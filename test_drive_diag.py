"""
Quick diagnostic: lists files in The_Vault on Google Drive and optionally
re-shares each file individually so they appear in the user's Drive view.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv; load_dotenv()

from core.synapse_worker import get_drive_service, ensure_folder_visible, share_with_user
USER_EMAIL = os.getenv("USER_EMAIL")

print("\n[DRIVE DIAG] Connecting...")
service, is_sa = get_drive_service()
if not service:
    print("[ERROR] Could not get Drive service. Check credentials.")
    sys.exit(1)

folder_id, link = ensure_folder_visible(service)
print(f"[DRIVE DIAG] Folder ID : {folder_id}")
print(f"[DRIVE DIAG] Drive link: {link}")

# List files inside the folder
results = service.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    fields="files(id, name, owners, webViewLink)",
    pageSize=50
).execute()
files = results.get("files", [])
print(f"\n[DRIVE DIAG] Files in The_Vault: {len(files)}")

for f in files:
    owner = f.get("owners", [{}])[0].get("emailAddress", "?")
    print(f"  {f['name']}  (owner: {owner})")

# Re-share each file individually with the user so they appear in Drive
if files and USER_EMAIL:
    print(f"\n[FIX] Sharing each file with {USER_EMAIL} so they appear in your Drive view...")
    for f in files:
        try:
            service.permissions().create(
                fileId=f["id"],
                body={"type": "user", "role": "reader", "emailAddress": USER_EMAIL},
                fields="id",
                sendNotificationEmail=False   # no email spam
            ).execute()
            print(f"  [OK] Shared: {f['name']}")
        except Exception as e:
            print(f"  [ERR] {f['name']}: {e}")
elif not USER_EMAIL:
    print("\n[WARN] USER_EMAIL not set in .env — cannot auto-share files.")

print("\n[DONE] Check your Google Drive now.")
