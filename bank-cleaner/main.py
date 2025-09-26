# main.py
import argparse
from pathlib import Path
import pandas as pd
import re
import gspread
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth import get_credentials

def preview_csv(path, n=5):
    df = pd.read_csv(path)
    print("\nDetected columns:", list(df.columns))
    print("\nSample rows:")
    print(df.head(n).to_string(index=False))
    return df

def ask_mapping(df):
    # heuristic defaults
    cols = list(df.columns)
    def find_default(key_terms):
        for t in key_terms:
            for c in cols:
                if t in c.lower():
                    return c
        return ""
    mapping = {}
    mapping['date'] = find_default(['date','trans'])
    mapping['description'] = find_default(['description','desc','memo','details'])
    mapping['amount'] = find_default(['amount','amt','value'])
    mapping['category'] = find_default(['category','cat'])
    print("\nMap columns for core fields. Press Enter to accept default in ( ).")
    for k in ['date','description','amount','category']:
        default = mapping.get(k,"")
        val = input(f"Column for {k} (default: '{default}'): ").strip()
        mapping[k] = val if val else default
    return mapping

def clean_dataframe(df, mp):
    df = df.copy()
    # Parse date
    if mp['date'] and mp['date'] in df.columns:
        df[mp['date']] = pd.to_datetime(df[mp['date']], errors='coerce', dayfirst=False)
    # Normalize amount: remove currency symbols & parentheses => negative
    if mp['amount'] and mp['amount'] in df.columns:
        s = df[mp['amount']].astype(str)
        s = s.str.replace(r'[$,]', '', regex=True)
        s = s.str.replace(r'\((.*)\)', r'-\1', regex=True)  # (12.00) → -12.00
        df[mp['amount']] = pd.to_numeric(s, errors='coerce')
    # Combine Description + Note if present
    desc_col = mp['description'] if mp['description'] in df.columns else None
    if desc_col:
        other_note = None
        for candidate in ['Note','note','Notes','Memo','memo']:
            if candidate in df.columns:
                other_note = candidate
                break
        if other_note:
            df['Details'] = df[desc_col].fillna('') + " " + df[other_note].fillna('')
        else:
            df['Details'] = df[desc_col].fillna('')
        df['Details'] = df['Details'].str.strip()
    else:
        df['Details'] = ""
    return df

def split_and_export(df, amount_col):
    incoming = df[df[amount_col] > 0].copy()
    outgoing = df[df[amount_col] < 0].copy()
    ebay_mask = df['Details'].str.contains('ebay', case=False, na=False)
    ebay_outgoing = df[ebay_mask & (df[amount_col] < 0)].copy()

    incoming.to_csv("incoming_payments.csv", index=False)
    outgoing.to_csv("outgoing_payments.csv", index=False)
    ebay_outgoing.to_csv("ebay_outgoing.csv", index=False)
    print("\nSaved CSVs: incoming_payments.csv, outgoing_payments.csv, ebay_outgoing.csv")
    return incoming, outgoing, ebay_outgoing

def ensure_spreadsheet(creds, title):
    # use Drive API to search for a spreadsheet with that exact name
    drive = build('drive', 'v3', credentials=creds)
    q = f"name = '{title}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
    resp = drive.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
    files = resp.get('files', [])
    if files:
        print("Found existing spreadsheet:", files[0]['name'])
        return files[0]['id']
    # else create with Sheets API
    sheets = build('sheets', 'v4', credentials=creds)
    body = {"properties": {"title": title}}
    spreadsheet = sheets.spreadsheets().create(body=body).execute()
    sid = spreadsheet.get('spreadsheetId')
    print("Created new spreadsheet:", title, "(id:", sid, ")")
    return sid

def upload_df_to_spreadsheet(creds, spreadsheet_id, df, worksheet="Sheet1"):
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet(worksheet)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet, rows=str(len(df)+10), cols=str(len(df.columns)+5))
    ws.clear()
    rows = [list(df.columns)] + df.fillna('').astype(str).values.tolist()
    ws.update(rows)
    print(f"Uploaded {len(df)} rows to '{worksheet}' in spreadsheet id {spreadsheet_id}")

def main():
    parser = argparse.ArgumentParser(description="CSV -> clean -> Google Sheets uploader (interactive)")
    parser.add_argument("csv", help="path to transactions CSV file")
    args = parser.parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print("CSV not found:", csv_path)
        return

    creds = get_credentials()
    df = preview_csv(csv_path, n=5)
    mapping = ask_mapping(df)
    if not mapping['amount']:
        print("You must specify an amount column. Exiting.")
        return
    df_clean = clean_dataframe(df, mapping)
    # show a quick preview of cleaned
    print("\nCleaned preview:")
    print(df_clean[[mapping['date'], mapping['amount'], 'Details']].head(5).to_string(index=False))
    incoming, outgoing, ebay_outgoing = split_and_export(df_clean, mapping['amount'])

    # choose which dataset to upload
    print("\nWhich dataset would you like to upload to Google Sheets?")
    print("  1) Cleaned master")
    print("  2) Incoming payments only")
    print("  3) Outgoing payments only")
    print("  4) eBay outgoing only")
    choice = input("Enter 1/2/3/4 (default 1): ").strip() or "1"
    dataset = {"1": df_clean, "2": incoming, "3": outgoing, "4": ebay_outgoing}[choice]

    title = input("Spreadsheet title to create/open (default 'My Transactions'): ").strip() or "My Transactions"
    try:
        sid = ensure_spreadsheet(creds, title)
    except HttpError as e:
        print("Drive/Sheets API error:", e)
        return

    ws_name = input("Worksheet name (default 'Sheet1'): ").strip() or "Sheet1"
    upload_df_to_spreadsheet(creds, sid, dataset, worksheet=ws_name)
    print("All done. Open your spreadsheet in Google Sheets to verify.")

if __name__ == "__main__":
    main()
