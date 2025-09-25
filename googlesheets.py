import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# === SETUP AUTH ===
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Also auth for Google Drive
gauth = GoogleAuth()
gauth.credentials = creds
drive = GoogleDrive(gauth)

# === STEP 1: Load CSV ===
df = pd.read_csv("transactions.csv")
df = df[["Date", "Description", "Amount", "Category"]]  # simplified

# === STEP 2: Push to Google Sheets ===
sheet = client.open("My Transactions").sheet1
sheet.clear()
sheet.update([df.columns.values.tolist()] + df.values.tolist())

print("✅ Data pushed to Google Sheets")

# === STEP 3: Upload CSV backup to Drive ===
file = drive.CreateFile({"title": "transactions_cleaned.csv", "mimeType": "text/csv"})
file.SetContentFile("transactions.csv")
file.Upload()
print("✅ CSV uploaded to Google Drive")
