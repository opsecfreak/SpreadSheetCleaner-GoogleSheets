# main.py
"""Enhanced CSV to Google Sheets uploader with multi-sheet support and formatting."""

import argparse
from pathlib import Path
import sys

from auth import get_credentials
from data_cleaner import (
    preview_csv, ask_column_mapping, clean_dataframe, filter_transactions,
    save_datasets_to_csv, get_preview_data
)
from sheets_manager import (
    SheetsManager, interactive_spreadsheet_selection, interactive_sheet_selection
)


def main():
    """Main workflow for CSV cleaning and Google Sheets upload."""
    parser = argparse.ArgumentParser(
        description="Enhanced CSV to Google Sheets uploader with multi-sheet support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py transactions.csv
  python main.py report.csv --output-dir custom_output
  python main.py data.csv --spreadsheet-id 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
        """
    )
    
    parser.add_argument(
        "csv_file", 
        help="Path to the CSV file to process"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=Path,
        default=Path("output"),
        help="Directory to save cleaned CSV files (default: output)"
    )
    
    parser.add_argument(
        "--spreadsheet-id",
        help="Google Sheets ID to use (optional, will prompt if not provided)"
    )
    
    parser.add_argument(
        "--spreadsheet-name",
        help="Google Sheets name to find/create (optional)"
    )
    
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Only clean and save CSV files, skip Google Sheets upload"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=True,
        help="Overwrite existing sheet data (default: True)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("  Enhanced Banking CSV to Google Sheets Uploader")
    print("=" * 60)
    
    try:
        # Step 1: Load and preview CSV
        print(f"\n📁 Loading CSV file: {csv_path}")
        df_raw = preview_csv(csv_path, n=5)
        
        if df_raw.empty:
            print("Error: CSV file is empty or could not be read.")
            sys.exit(1)
        
        # Step 2: Column mapping
        print(f"\n🔍 Column Mapping")
        print("-" * 30)
        mapping = ask_column_mapping(df_raw)
        
        if not mapping['amount']:
            print("Error: Amount column is required. Exiting.")
            sys.exit(1)
        
        # Step 3: Clean data
        print(f"\n🧹 Cleaning Data")
        print("-" * 30)
        df_clean = clean_dataframe(df_raw, mapping)
        
        if df_clean.empty:
            print("Error: No valid data after cleaning.")
            sys.exit(1)
        
        print(f"✅ Cleaned {len(df_clean)} transactions")
        
        # Step 4: Show preview
        print(f"\n👀 Preview of Cleaned Data:")
        print("-" * 30)
        print(get_preview_data(df_clean, n=5))
        
        # Step 5: Filter and categorize transactions
        print(f"\n📊 Filtering Transactions")
        print("-" * 30)
        master, incoming, outgoing, ebay_outgoing = filter_transactions(df_clean)
        
        datasets = {
            'Master': master,
            'Incoming': incoming, 
            'Outgoing': outgoing,
            'eBay_Outgoing': ebay_outgoing
        }
        
        # Print summary
        print(f"Dataset Summary:")
        for name, df in datasets.items():
            if not df.empty:
                print(f"  - {name}: {len(df)} transactions")
            else:
                print(f"  - {name}: 0 transactions (empty)")
        
        # Step 6: Save to CSV files
        print(f"\n💾 Saving CSV Files")
        print("-" * 30)
        saved_files = save_datasets_to_csv(master, incoming, outgoing, ebay_outgoing, args.output_dir)
        
        if args.skip_upload:
            print(f"\n✅ CSV processing complete! Files saved in {args.output_dir}")
            print("Skipping Google Sheets upload as requested.")
            return
        
        # Step 7: Google Sheets Authentication
        print(f"\n🔐 Authenticating with Google Sheets")
        print("-" * 30)
        try:
            creds = get_credentials()
            sheets_manager = SheetsManager(creds)
        except Exception as e:
            print(f"Error: Failed to authenticate with Google: {e}")
            print("CSV files have been saved. You can upload them manually.")
            return
        
        # Step 8: Spreadsheet selection
        print(f"\n📋 Spreadsheet Selection")
        print("-" * 30)
        
        if args.spreadsheet_id:
            # Use provided spreadsheet ID
            spreadsheet_id = args.spreadsheet_id
            metadata = sheets_manager.find_spreadsheet_by_id(spreadsheet_id)
            if not metadata:
                print(f"Error: Cannot access spreadsheet with ID: {spreadsheet_id}")
                return
            spreadsheet_name = metadata['name']
            print(f"Using spreadsheet: '{spreadsheet_name}' (ID: {spreadsheet_id})")
        elif args.spreadsheet_name:
            # Use provided spreadsheet name
            spreadsheet_id = sheets_manager.get_or_create_spreadsheet(args.spreadsheet_name)
            spreadsheet_name = args.spreadsheet_name
        else:
            # Interactive selection
            spreadsheet_id, spreadsheet_name = interactive_spreadsheet_selection(sheets_manager)
        
        # Step 9: Sheet selection and upload
        print(f"\n📤 Upload Configuration")
        print("-" * 30)
        
        # Remove empty datasets before selection
        non_empty_datasets = {k: v for k, v in datasets.items() if not v.empty}
        
        if not non_empty_datasets:
            print("Error: No data to upload!")
            return
        
        selected_datasets = interactive_sheet_selection(non_empty_datasets)
        
        if not selected_datasets:
            print("No datasets selected for upload. Exiting.")
            return
        
        # Step 10: Upload to Google Sheets
        print(f"\n🚀 Uploading to Google Sheets")
        print("-" * 30)
        print(f"Target: '{spreadsheet_name}' ({spreadsheet_id})")
        
        results = sheets_manager.upload_multiple_sheets(
            spreadsheet_id, selected_datasets, overwrite=args.overwrite
        )
        
        # Step 11: Summary
        print(f"\n✅ Upload Complete!")
        print("=" * 60)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"📊 Results: {success_count}/{total_count} sheets uploaded successfully")
        
        for sheet_name, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            row_count = len(selected_datasets[sheet_name])
            print(f"  - {sheet_name}: {status} ({row_count} rows)")
        
        print(f"\n🔗 Spreadsheet URL:")
        print(f"   {sheets_manager.get_spreadsheet_url(spreadsheet_id)}")
        
        print(f"\n💾 Local CSV files saved in: {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("\nCSV files may have been saved. Check the output directory.")
        sys.exit(1)


if __name__ == "__main__":
    main()
