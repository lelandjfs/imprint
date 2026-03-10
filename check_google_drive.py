"""
Check what files are in Google Drive Imprint folders.
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

IMPRINT_FOLDER_ID = '1o3RQOFx4WaFiENkFYRDaAJd5SZOYvDeJ'
VISION_FOLDER_ID = '1fQ6FdK1uUVGfRPpOXW6Yvd3iK4_xkdVo'

print("="*80)
print("GOOGLE DRIVE IMPRINT FOLDERS CHECK")
print("="*80)

# Check main Imprint folder for PDFs
print("\n📁 Main Imprint folder - PDFs:")
print("-"*80)
results = drive.files().list(
    q=f"'{IMPRINT_FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false",
    fields="files(id, name, createdTime, modifiedTime)"
).execute()

pdfs = results.get('files', [])
if pdfs:
    for pdf in pdfs:
        print(f"  • {pdf['name']}")
        print(f"    ID: {pdf['id']}")
        print(f"    Created: {pdf['createdTime']}")
        if 'oil' in pdf['name'].lower():
            print(f"    ⚠️  CONTAINS 'OIL' - This might be the problematic file!")
        print()
else:
    print("  No PDFs found")

# Check Vision subfolder
print("\n📁 Vision subfolder - Images & PDFs:")
print("-"*80)
results = drive.files().list(
    q=f"'{VISION_FOLDER_ID}' in parents and trashed=false",
    fields="files(id, name, mimeType, createdTime)"
).execute()

vision_files = results.get('files', [])
if vision_files:
    for f in vision_files:
        print(f"  • {f['name']} ({f['mimeType']})")
        print(f"    ID: {f['id']}")
        if 'oil' in f['name'].lower():
            print(f"    ⚠️  CONTAINS 'OIL' - This might be the problematic file!")
        print()
else:
    print("  No files found")

# Search for "oil" anywhere in Imprint folders
print("\n🔍 Searching for 'oil' in all Imprint files:")
print("-"*80)
results = drive.files().list(
    q=f"name contains 'oil' and trashed=false and ('{IMPRINT_FOLDER_ID}' in parents or '{VISION_FOLDER_ID}' in parents)",
    fields="files(id, name, mimeType, parents)"
).execute()

oil_files = results.get('files', [])
if oil_files:
    for f in oil_files:
        print(f"  • {f['name']}")
        print(f"    ID: {f['id']}")
        print(f"    Type: {f['mimeType']}")
        print(f"    Parent: {f.get('parents', ['Unknown'])[0]}")
        print(f"    🗑️  DELETE THIS FILE from Google Drive!")
        print()
else:
    print("  ✅ No files containing 'oil' found in Imprint folders")

print("\n" + "="*80)
print("RECOMMENDATIONS:")
print("="*80)
if oil_files:
    print("❌ Found files containing 'oil' in Google Drive!")
    print("   You need to delete these from Google Drive (not just Supabase):")
    for f in oil_files:
        print(f"   - {f['name']} (ID: {f['id']})")
    print("\n   To delete via command line, run:")
    for f in oil_files:
        print(f"   python3 -c \"from googleapiclient.discovery import build; from google.oauth2.credentials import Credentials; drive = build('drive', 'v3', credentials=Credentials.from_authorized_user_file('token.json')); drive.files().delete(fileId='{f['id']}').execute(); print('Deleted {f['name']}')\"")
else:
    print("✅ No 'oil' files found in Google Drive!")
    print("   If the document still re-appears, check:")
    print("   1. Trash folder in Google Drive")
    print("   2. Gmail 'Imprint' label for forwarded email")
    print("   3. Safari bookmarks")
