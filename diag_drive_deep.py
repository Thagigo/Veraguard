import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def deep_search_sources():
    creds_path = os.path.join("core", "service_account.json")
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=creds)

    print("--- Searching for Source Markers (SWC, DeFiHackLabs) ---")
    query = "name contains 'SWC' or name contains 'DeFiHackLabs' or name contains 'DeFi'"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, parents)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    items = results.get('files', [])

    if not items:
        print("No matches found for SWC, DeFiHackLabs, or DeFi.")
        # List everything else to be sure
        print("\n--- Listing ALL accessible items (limit 50) ---")
        all_results = service.files().list(pageSize=50, fields="files(name)").execute()
        for f in all_results.get('files', []):
            print(f"- {f['name']}")
    else:
        for item in items:
            parents = item.get('parents', ['None'])
            print(f"MATCH: {item['name']} (ID: {item['id']}) | Parents: {parents}")

if __name__ == "__main__":
    deep_search_sources()
