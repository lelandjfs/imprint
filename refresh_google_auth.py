#!/usr/bin/env python3
"""
Refresh Google OAuth token for Imprint ingestion.
Run this when you get 'Token has been expired or revoked' errors.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes needed for Imprint
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/drive.readonly'
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(SCRIPT_DIR, 'token.json')
CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, 'credentials.json')


def main():
    print("=" * 60)
    print("Google OAuth Token Refresh")
    print("=" * 60)
    print()

    creds = None

    # Try to load existing token
    if os.path.exists(TOKEN_PATH):
        print(f"Found existing token at: {TOKEN_PATH}")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If credentials are invalid or don't exist, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Attempting to refresh expired token...")
            try:
                creds.refresh(Request())
                print("✓ Token refreshed successfully!")
            except Exception as e:
                print(f"✗ Refresh failed: {e}")
                print("Starting new OAuth flow...")
                creds = None

        if not creds:
            print("Starting OAuth authorization flow...")
            print("Your browser will open to authorize access.")
            print()
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
            print("✓ Authorization successful!")
    else:
        print("✓ Existing token is still valid!")

    # Save the credentials
    print(f"Saving token to: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'w') as token_file:
        token_file.write(creds.to_json())

    print()
    print("=" * 60)
    print("✓ Done! Your token is ready.")
    print("=" * 60)


if __name__ == '__main__':
    main()
