import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv; load_dotenv()
from core.synapse_worker import get_upload_service, ensure_folder_visible, get_drive_service

sa_svc, _ = get_drive_service()
folder_id, link = ensure_folder_visible(sa_svc)

# List using YOUR OAuth account — sees everything you own in the folder
upload_svc = get_upload_service()
r = upload_svc.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    fields="files(id, name, createdTime)",
    pageSize=50,
    orderBy="createdTime desc"
).execute()
files = r.get("files", [])
print(f"\nFiles in The_Vault (your OAuth view): {len(files)}")
for f in files:
    print(f"  {f['name']}  [{f.get('createdTime','')}]")
print(f"\nFolder: {link}")
