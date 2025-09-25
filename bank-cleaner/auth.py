# auth.py
from pathlib import Path
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes for Sheets + Drive (read/write)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = Path("token.pickle")

def get_credentials():
    creds = None
    if TOKEN_FILE.exists():
        with TOKEN_FILE.open("rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            # opens browser and runs a local server to capture the auth response
            creds = flow.run_local_server(port=0)
        # save for next time
        with TOKEN_FILE.open("wb") as f:
            pickle.dump(creds, f)
    return creds
