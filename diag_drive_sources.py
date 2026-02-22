import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def list_drive_root():
    # Use the service account from core/service_account.json
    creds_path = os.path.join("core", "service_account.json")
    if not os.path.exists(creds_path):
        print(f"Error: {creds_path} not found")
        return

    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=creds)

    print("--- Listing Drive Root (Service Account) ---")
    results = service.files().list(
        q="'root' in parents and trashed = false",
        fields="files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        for item in items:
            print(f"{item['name']} ({item['id']}) - {item['mimeType']}")

    # Try searching for VeraGuard_Intel specifically if not in root
    print("\n--- Searching for 'VeraGuard_Intel' ---")
    results = service.files().list(
        q="name contains 'VeraGuard_Intel' and trashed = false",
        fields="files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])
    for item in items:
        print(f"FOUND: {item['name']} ({item['id']}) - {item['mimeType']}")
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            # List contents of this folder
            print(f"  Contents of {item['name']}:")
            folder_results = service.files().list(
                q=f"'{item['id']}' in parents and trashed = false",
                fields="files(id, name)"
            ).execute()
            folder_items = folder_results.get('files', [])
            print(f"  Count: {len(folder_items)}")
            for f in folder_items[:5]:
                print(f"    - {f['name']}")

if __name__ == "__main__":
    list_drive_root()
