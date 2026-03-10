"""
Find any files containing 'oil' in Google Drive.
"""

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment
with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

# Google Drive setup
drive_creds = Credentials.from_authorized_user_file(
    os.path.join(os.path.dirname(__file__), 'token.json')
)
drive = build('drive', 'v3', credentials=drive_creds)

print("="*80)
print("🔍 Searching ALL Google Drive for files containing 'oil'")
print("="*80)

# Search everywhere (not just Imprint folders)
results = drive.files().list(
    q="name contains 'oil' and trashed=false",
    fields="files(id, name, mimeType, parents, createdTime)",
    pageSize=50
).execute()

files = results.get('files', [])

if files:
    print(f"\n❌ Found {len(files)} file(s) containing 'oil':\n")
    for f in files:
        print(f"📄 {f['name']}")
        print(f"   ID: {f['id']}")
        print(f"   Type: {f['mimeType']}")
        print(f"   Created: {f['createdTime']}")

        # Check if surging
        if 'surging' in f['name'].lower():
            print(f"   ⚠️  THIS IS THE PROBLEMATIC FILE!")
            print(f"   🗑️  Delete with: drive.files().delete(fileId='{f['id']}').execute()")
        print()

    print("\n" + "="*80)
    print("TO DELETE ALL FILES WITH 'oil' in the name, run:")
    print("="*80)
    print("python3 delete_oil_files.py")

else:
    print("\n✅ No files containing 'oil' found in Google Drive!")
    print("   The file may have already been deleted.")

# Also check trash
print("\n" + "="*80)
print("🗑️  Checking trash folder...")
print("="*80)

trash_results = drive.files().list(
    q="name contains 'oil' and trashed=true",
    fields="files(id, name, mimeType)",
    pageSize=50
).execute()

trash_files = trash_results.get('files', [])
if trash_files:
    print(f"\n⚠️  Found {len(trash_files)} file(s) in trash:")
    for f in trash_files:
        print(f"   • {f['name']}")
    print("\n   These are in trash and won't be re-ingested.")
else:
    print("\n✅ No 'oil' files in trash.")

print("\n" + "="*80)
