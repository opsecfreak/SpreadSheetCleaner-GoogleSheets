# auth.py
"""Google authentication utilities for Sheets and Drive APIs."""

from pathlib import Path
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Scopes for Sheets + Drive (read/write)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly"
]

CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = Path("token.json")


def get_credentials():
    """Get valid Google API credentials with refresh capability."""
    creds = None
    
    # Load existing token
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"Warning: Could not load existing token: {e}")
            creds = None
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("✅ Refreshed existing credentials")
            except Exception as e:
                print(f"Warning: Could not refresh credentials: {e}")
                creds = None
        
        if not creds:
            # Get new credentials via OAuth flow
            if not Path(CLIENT_SECRET_FILE).exists():
                print(f"Error: {CLIENT_SECRET_FILE} not found!")
                print("Please download your OAuth 2.0 client credentials from Google Cloud Console")
                print("and save them as 'client_secret.json' in this directory.")
                raise FileNotFoundError(f"Missing {CLIENT_SECRET_FILE}")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ Obtained new credentials")
            except Exception as e:
                print(f"Error during OAuth flow: {e}")
                raise
        
        # Save credentials for next time
        try:
            with TOKEN_FILE.open("w") as token:
                token.write(creds.to_json())
            print("✅ Saved credentials for future use")
        except Exception as e:
            print(f"Warning: Could not save credentials: {e}")
    
    return creds


def check_credentials_exist():
    """Check if credential files exist."""
    client_secret_exists = Path(CLIENT_SECRET_FILE).exists()
    token_exists = TOKEN_FILE.exists()
    
    return {
        'client_secret': client_secret_exists,
        'token': token_exists,
        'client_secret_path': CLIENT_SECRET_FILE,
        'token_path': str(TOKEN_FILE)
    }
