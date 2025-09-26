# sheets_manager.py
"""Google Sheets management utilities with formatting and multi-sheet support."""

import pandas as pd
import gspread
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Dict, List, Optional, Tuple, Any
import time
from datetime import datetime


class SheetsManager:
    """Manages Google Sheets operations including formatting and multi-sheet handling."""
    
    def __init__(self, credentials):
        self.creds = credentials
        self.gc = gspread.authorize(credentials)
        self.sheets_service = build('sheets', 'v4', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)
    
    def find_spreadsheet_by_name(self, title: str) -> Optional[str]:
        """Find spreadsheet by exact name match."""
        query = f"name = '{title}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
        try:
            response = self.drive_service.files().list(
                q=query, 
                spaces='drive', 
                fields='files(id, name, modifiedTime)'
            ).execute()
            files = response.get('files', [])
            if files:
                return files[0]['id']
        except HttpError as e:
            print(f"Error searching for spreadsheet: {e}")
        return None
    
    def find_spreadsheet_by_id(self, spreadsheet_id: str) -> Optional[Dict[str, Any]]:
        """Verify spreadsheet exists by ID and return metadata."""
        try:
            response = self.drive_service.files().get(
                fileId=spreadsheet_id,
                fields='id, name, modifiedTime'
            ).execute()
            return response
        except HttpError as e:
            print(f"Error accessing spreadsheet by ID: {e}")
            return None
    
    def list_user_spreadsheets(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """List user's recent spreadsheets."""
        query = "mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
        try:
            response = self.drive_service.files().list(
                q=query,
                pageSize=max_results,
                orderBy='modifiedTime desc',
                fields='files(id, name, modifiedTime)'
            ).execute()
            return response.get('files', [])
        except HttpError as e:
            print(f"Error listing spreadsheets: {e}")
            return []
    
    def create_new_spreadsheet(self, title: str) -> str:
        """Create a new spreadsheet and return its ID."""
        try:
            body = {"properties": {"title": title}}
            spreadsheet = self.sheets_service.spreadsheets().create(body=body).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            print(f"Created new spreadsheet: '{title}' (ID: {spreadsheet_id})")
            return spreadsheet_id
        except HttpError as e:
            print(f"Error creating spreadsheet: {e}")
            raise
    
    def get_or_create_spreadsheet(self, title: str, spreadsheet_id: Optional[str] = None) -> str:
        """Get existing spreadsheet or create new one."""
        # If ID provided, try to use it
        if spreadsheet_id:
            metadata = self.find_spreadsheet_by_id(spreadsheet_id)
            if metadata:
                print(f"Found existing spreadsheet: '{metadata['name']}' (ID: {spreadsheet_id})")
                return spreadsheet_id
            else:
                print(f"Spreadsheet with ID {spreadsheet_id} not found or not accessible.")
        
        # Try to find by name
        found_id = self.find_spreadsheet_by_name(title)
        if found_id:
            print(f"Found existing spreadsheet: '{title}' (ID: {found_id})")
            return found_id
        
        # Create new
        return self.create_new_spreadsheet(title)
    
    def get_sheet_names(self, spreadsheet_id: str) -> List[str]:
        """Get list of sheet names in spreadsheet."""
        try:
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            sheets = spreadsheet.get('sheets', [])
            return [sheet['properties']['title'] for sheet in sheets]
        except HttpError as e:
            print(f"Error getting sheet names: {e}")
            return []
    
    def create_or_clear_worksheet(self, spreadsheet_id: str, sheet_name: str, 
                                 rows: int = 1000, cols: int = 10) -> gspread.Worksheet:
        """Create new worksheet or clear existing one."""
        try:
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            
            # Try to get existing worksheet
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                worksheet.clear()  # Clear existing data
                print(f"Cleared existing sheet: '{sheet_name}'")
            except gspread.exceptions.WorksheetNotFound:
                # Create new worksheet
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name, 
                    rows=rows, 
                    cols=cols
                )
                print(f"Created new sheet: '{sheet_name}'")
            
            return worksheet
        except Exception as e:
            print(f"Error managing worksheet '{sheet_name}': {e}")
            raise
    
    def upload_dataframe_to_sheet(self, spreadsheet_id: str, sheet_name: str, 
                                 df: pd.DataFrame, overwrite: bool = True) -> bool:
        """Upload DataFrame to specified sheet with formatting."""
        try:
            if df.empty:
                print(f"No data to upload to '{sheet_name}'")
                return False
            
            # Create or get worksheet
            worksheet = self.create_or_clear_worksheet(
                spreadsheet_id, sheet_name, 
                rows=len(df) + 50, cols=len(df.columns) + 5
            )
            
            # Prepare data for upload
            # Convert DataFrame to list of lists
            header = list(df.columns)
            data = df.fillna('').astype(str).values.tolist()
            all_data = [header] + data
            
            # Upload data
            if overwrite:
                worksheet.clear()
            
            # Update in batches for better performance
            worksheet.update(all_data, value_input_option='USER_ENTERED')
            
            print(f"Uploaded {len(df)} rows to '{sheet_name}' in spreadsheet {spreadsheet_id}")
            
            # Apply formatting
            self._format_worksheet(spreadsheet_id, worksheet, df)
            
            return True
            
        except Exception as e:
            print(f"Error uploading to sheet '{sheet_name}': {e}")
            return False
    
    def _format_worksheet(self, spreadsheet_id: str, worksheet: gspread.Worksheet, df: pd.DataFrame):
        """Apply formatting to worksheet."""
        try:
            sheet_id = worksheet.id
            requests = []
            
            # Freeze header row
            requests.append({
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {
                            "frozenRowCount": 1
                        }
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            })
            
            # Bold header row
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": len(df.columns)
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            })
            
            # Format Date column (assuming first column or column named 'Date')
            date_col_index = None
            if 'Date' in df.columns:
                date_col_index = list(df.columns).index('Date')
            elif len(df.columns) > 0:
                # Assume first column is date
                date_col_index = 0
            
            if date_col_index is not None:
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": len(df) + 1,
                            "startColumnIndex": date_col_index,
                            "endColumnIndex": date_col_index + 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "DATE",
                                    "pattern": "yyyy-mm-dd"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                })
            
            # Format Amount column (assuming column named 'Amount')
            amount_col_index = None
            if 'Amount' in df.columns:
                amount_col_index = list(df.columns).index('Amount')
            
            if amount_col_index is not None:
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": len(df) + 1,
                            "startColumnIndex": amount_col_index,
                            "endColumnIndex": amount_col_index + 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {
                                    "type": "CURRENCY",
                                    "pattern": "$#,##0.00"
                                }
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                })
            
            # Auto-resize columns
            requests.append({
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": len(df.columns)
                    }
                }
            })
            
            # Execute all formatting requests
            if requests:
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={"requests": requests}
                ).execute()
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Warning: Could not apply formatting: {e}")
    
    def upload_multiple_sheets(self, spreadsheet_id: str, datasets: Dict[str, pd.DataFrame],
                              overwrite: bool = True) -> Dict[str, bool]:
        """Upload multiple DataFrames to different sheets."""
        results = {}
        
        for sheet_name, df in datasets.items():
            if df.empty:
                print(f"Skipping empty dataset: {sheet_name}")
                results[sheet_name] = False
                continue
                
            success = self.upload_dataframe_to_sheet(
                spreadsheet_id, sheet_name, df, overwrite
            )
            results[sheet_name] = success
            
            # Small delay between uploads to avoid rate limiting
            time.sleep(0.5)
        
        return results
    
    def add_master_links_to_filtered_sheets(self, spreadsheet_id: str, 
                                          filtered_datasets: Dict[str, pd.DataFrame]):
        """Add links from filtered sheets back to Master sheet."""
        # This is handled by the 'Source' column added in data_cleaner.py
        # The formulas are automatically interpreted by Google Sheets
        print("Master-to-filtered links are automatically handled via 'Source' column formulas.")
    
    def get_spreadsheet_url(self, spreadsheet_id: str) -> str:
        """Get the web URL for the spreadsheet."""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"


def interactive_spreadsheet_selection(sheets_manager: SheetsManager) -> Tuple[str, str]:
    """Interactive selection of spreadsheet to use."""
    print("\nSelect spreadsheet option:")
    print("  1) Use existing spreadsheet by name")
    print("  2) Use existing spreadsheet by ID")
    print("  3) Create new spreadsheet")
    print("  4) Browse recent spreadsheets")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        title = input("Enter exact spreadsheet name: ").strip()
        if not title:
            print("No name provided, creating new spreadsheet.")
            title = input("New spreadsheet title: ").strip() or "Banking Transactions"
        spreadsheet_id = sheets_manager.get_or_create_spreadsheet(title)
        return spreadsheet_id, title
    
    elif choice == "2":
        spreadsheet_id = input("Enter spreadsheet ID: ").strip()
        if not spreadsheet_id:
            print("No ID provided, creating new spreadsheet.")
            title = input("New spreadsheet title: ").strip() or "Banking Transactions"
            spreadsheet_id = sheets_manager.create_new_spreadsheet(title)
        else:
            metadata = sheets_manager.find_spreadsheet_by_id(spreadsheet_id)
            title = metadata['name'] if metadata else "Unknown"
        return spreadsheet_id, title
    
    elif choice == "3":
        title = input("New spreadsheet title: ").strip() or "Banking Transactions"
        spreadsheet_id = sheets_manager.create_new_spreadsheet(title)
        return spreadsheet_id, title
    
    elif choice == "4":
        print("\nRecent spreadsheets:")
        recent = sheets_manager.list_user_spreadsheets(10)
        if not recent:
            print("No spreadsheets found. Creating new one.")
            title = input("New spreadsheet title: ").strip() or "Banking Transactions"
            spreadsheet_id = sheets_manager.create_new_spreadsheet(title)
            return spreadsheet_id, title
        
        for i, sheet in enumerate(recent, 1):
            modified = sheet.get('modifiedTime', 'Unknown')
            print(f"  {i}) {sheet['name']} (Modified: {modified[:10]})")
        
        try:
            idx = int(input(f"Select spreadsheet (1-{len(recent)}) or 0 for new: ").strip())
            if idx == 0:
                title = input("New spreadsheet title: ").strip() or "Banking Transactions"
                spreadsheet_id = sheets_manager.create_new_spreadsheet(title)
                return spreadsheet_id, title
            elif 1 <= idx <= len(recent):
                selected = recent[idx - 1]
                return selected['id'], selected['name']
        except (ValueError, IndexError):
            pass
        
        print("Invalid selection, creating new spreadsheet.")
        title = input("New spreadsheet title: ").strip() or "Banking Transactions"
        spreadsheet_id = sheets_manager.create_new_spreadsheet(title)
        return spreadsheet_id, title
    
    else:
        print("Invalid choice, creating new spreadsheet.")
        title = input("New spreadsheet title: ").strip() or "Banking Transactions"
        spreadsheet_id = sheets_manager.create_new_spreadsheet(title)
        return spreadsheet_id, title


def interactive_sheet_selection(datasets: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Interactive selection of which sheets to upload."""
    print("\nAvailable datasets:")
    valid_datasets = {k: v for k, v in datasets.items() if not v.empty}
    
    if not valid_datasets:
        print("No valid datasets to upload!")
        return {}
    
    for i, (name, df) in enumerate(valid_datasets.items(), 1):
        print(f"  {i}) {name.title()} ({len(df)} rows)")
    
    print("\nUpload options:")
    print("  a) Upload all sheets")
    print("  s) Select specific sheets")
    
    choice = input("Enter choice (a/s): ").strip().lower()
    
    if choice == "a":
        return valid_datasets
    elif choice == "s":
        selected = {}
        for name, df in valid_datasets.items():
            upload = input(f"Upload {name} sheet? (y/n): ").strip().lower()
            if upload in ['y', 'yes']:
                selected[name] = df
        return selected
    else:
        print("Invalid choice, uploading all sheets.")
        return valid_datasets