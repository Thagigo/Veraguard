import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def list_drive_and_shared():
    creds_path = os.path.join("core", "service_account.json")
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=creds)

    print("--- Checking Shared Drives ---")
    try:
        shared_results = service.drives().list(pageSize=10).execute()
        drives = shared_results.get('drives', [])
        if not drives:
            print("No Shared Drives found.")
        else:
            for d in drives:
                print(f"Shared Drive: {d['name']} (ID: {d['id']})")
    except Exception as e:
        print(f"Error listing shared drives: {e}")

    print("\n--- Exhaustive Search (Across all available files) ---")
    results = service.files().list(
        q="trashed = false",
        fields="files(id, name, mimeType)",
        pageSize=1000,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    items = results.get('files', [])
    
    found_intel = False
    for item in items:
        nm = item['name'].lower()
        if "veraguard_intel" in nm or "swc" in nm or "defihacklabs" in nm:
            print(f"MATCH: {item['name']} ({item['id']}) - {item['mimeType']}")
            found_intel = True
            
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # List children
                children = service.files().list(
                    q=f"'{item['id']}' in parents and trashed = false",
                    fields="files(name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                child_items = children.get('files', [])
                print(f"  [{item['name']}] contains {len(child_items)} items.")
                for c in child_items[:10]:
                    print(f"    - {c['name']}")

    if not found_intel:
        print("No matches for VeraGuard_Intel, SWC, or DeFiHackLabs found across any accessible drive.")

if __name__ == "__main__":
    list_drive_and_shared()
