import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def list_all_accessible_content():
    creds_path = os.path.join("core", "service_account.json")
    if not os.path.exists(creds_path):
        print(f"Error: {creds_path} not found")
        return

    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=creds)

    print("--- Listing ALL Accessible Files & Folders ---")
    results = service.files().list(
        q="trashed = false",
        fields="files(id, name, mimeType, parents)"
    ).execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        for item in items:
            parents = item.get('parents', ['None'])
            print(f"- {item['name']} (ID: {item['id']}) | Type: {item['mimeType']} | Parents: {parents}")

    # Specific search for SWC or DeFiHackLabs
    print("\n--- Searching for 'SWC' or 'DeFiHackLabs' ---")
    results = service.files().list(
        q="(name contains 'SWC' or name contains 'DeFiHackLabs') and trashed = false",
        fields="files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])
    for item in items:
        print(f"MATCH: {item['name']} ({item['id']}) - {item['mimeType']}")

if __name__ == "__main__":
    list_all_accessible_content()
