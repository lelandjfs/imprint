"""
Check Gmail for emails with 'Imprint' label containing 'oil'.
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

# Gmail setup
gmail_creds = Credentials.from_authorized_user_file(
    os.path.join(os.path.dirname(__file__), 'token.json')
)
gmail = build('gmail', 'v1', credentials=gmail_creds)

print("="*80)
print("📧 Checking Gmail for 'oil' in Imprint label")
print("="*80)

# Get Imprint label
labels = gmail.users().labels().list(userId='me').execute()
imprint_label = next((l for l in labels['labels'] if l['name'] == 'Imprint'), None)

if not imprint_label:
    print("\n❌ No 'Imprint' label found in Gmail")
    exit()

print(f"\n✅ Found Imprint label (ID: {imprint_label['id']})")

# Search for emails with Imprint label containing 'oil'
result = gmail.users().messages().list(
    userId='me',
    labelIds=[imprint_label['id']],
    q='oil OR surging'
).execute()

messages = result.get('messages', [])

if messages:
    print(f"\n❌ Found {len(messages)} email(s) with 'oil' or 'surging' in Imprint label:\n")
    for msg in messages:
        msg_data = gmail.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
        headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
        subject = headers.get('Subject', 'No subject')
        date = headers.get('Date', 'Unknown date')

        print(f"📧 Subject: {subject}")
        print(f"   Date: {date}")
        print(f"   ID: {msg['id']}")

        if 'surging' in subject.lower() and 'oil' in subject.lower():
            print(f"   ⚠️  THIS IS THE PROBLEMATIC EMAIL!")
            print(f"   🗑️  Remove 'Imprint' label or delete this email")
        print()

    print("\n" + "="*80)
    print("RECOMMENDATION:")
    print("="*80)
    print("Remove the 'Imprint' label from these emails in Gmail.")
    print("The ingestion script only processes emails WITH the Imprint label.")

else:
    print("\n✅ No emails containing 'oil' or 'surging' found in Imprint label")
    print("   The email may have already been removed from the label.")

print("\n" + "="*80)
