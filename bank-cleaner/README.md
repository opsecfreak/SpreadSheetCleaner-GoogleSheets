# Enhanced Banking CSV to Google Sheets Uploader

A Python tool that processes exported banking CSV files, cleans and categorizes the data, and uploads it to Google Sheets with professional formatting and multi-sheet organization.

## Features

### 🧹 Data Cleaning
- **Smart Column Detection**: Automatically detects Date, Description, Amount, and Category columns
- **Amount Normalization**: Handles various currency formats, parentheses notation for negatives
- **Date Parsing**: Converts various date formats to standardized format
- **Duplicate Field Combination**: Merges description with memo/note fields

### 📊 Data Organization  
- **Master Sheet**: All cleaned transactions with row numbers for linking
- **Incoming Payments**: Filtered view of positive amounts only
- **Outgoing Payments**: Filtered view of negative amounts only  
- **eBay Transactions**: Filtered view of eBay-related purchases
- **Auto-Categorization**: Intelligent categorization based on transaction details

### 🎨 Professional Formatting
- **Bold Headers**: All sheet headers are bolded
- **Frozen Headers**: Top row stays visible when scrolling
- **Currency Formatting**: Amount columns display as currency ($#,##0.00)
- **Date Formatting**: Date columns formatted as yyyy-mm-dd
- **Auto-Resize**: Columns automatically sized for readability

### 🔗 Sheet Linking
- **Master Links**: Each filtered sheet includes a "Source" column linking back to Master sheet
- **Cross-References**: Easy navigation between related transactions

### 📁 File Organization
- **CSV Exports**: All processed data saved to `output/` folder
- **Clean Structure**: Organized file naming convention
- **Backup Copies**: Local CSV backups of all processed data

## Setup

### 1. Google Cloud Configuration
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Google Sheets API** and **Google Drive API**
3. Create OAuth 2.0 credentials (Desktop Application type)
4. Download the credentials JSON file as `client_secret.json`

### 2. Installation
```bash
# Navigate to the bank-cleaner directory
cd bank-cleaner

# Install dependencies
pip install -r requirements.txt
```

### 3. Authentication
On first run, the tool will:
- Open your browser for Google OAuth authentication
- Request permissions for Google Sheets and Drive access
- Save authentication tokens for future use

## Usage

### Basic Usage
```bash
python main.py transactions.csv
```

### Advanced Options
```bash
# Specify custom output directory
python main.py report.csv --output-dir custom_output

# Use existing spreadsheet by ID
python main.py data.csv --spreadsheet-id 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms

# Use existing spreadsheet by name
python main.py data.csv --spreadsheet-name "My Bank Data"

# Only clean and save CSV files (skip Google Sheets upload)
python main.py data.csv --skip-upload

# Show help
python main.py --help
```

## Interactive Workflow

1. **CSV Loading**: Tool loads and previews your CSV file
2. **Column Mapping**: Confirm or adjust column mappings
3. **Data Cleaning**: Automatic cleaning and standardization
4. **Preview**: Review cleaned data before processing
5. **Filtering**: Transactions split into categorized datasets
6. **Spreadsheet Selection**: Choose existing or create new spreadsheet
7. **Sheet Selection**: Choose which datasets to upload
8. **Upload & Format**: Data uploaded with professional formatting
9. **Summary**: Review results with links to spreadsheet

## File Structure

```
bank-cleaner/
├── main.py              # Main application workflow
├── auth.py              # Google authentication
├── data_cleaner.py      # Data cleaning utilities  
├── sheets_manager.py    # Google Sheets management
├── requirements.txt     # Python dependencies
├── client_secret.json   # Google OAuth credentials (you provide)
├── token.json          # Stored authentication (auto-generated)
└── output/             # CSV export directory
    ├── cleaned_master.csv
    ├── incoming_payments.csv
    ├── outgoing_payments.csv
    └── ebay_outgoing.csv
```

## Spreadsheet Organization

### Master Sheet
- **Date**: Transaction date (yyyy-mm-dd format)
- **Amount**: Transaction amount (currency formatted)
- **Details**: Combined description and memo fields
- **Category**: Auto-detected or manual category
- **Master_Row**: Row number for linking (hidden in CSV exports)

### Filtered Sheets (Incoming/Outgoing/eBay)
- Same columns as Master
- **Source**: Formula linking back to Master sheet row
- Only relevant transactions included

## Common CSV Formats Supported

- **Chase Bank**: Date, Description, Amount, Balance
- **Bank of America**: Date, Description, Amount, Running Bal.
- **Wells Fargo**: Date, Amount, Description
- **PayPal**: Date, Name, Type, Status, Amount
- **Custom Formats**: Manual column mapping for any CSV structure

## Troubleshooting

### Authentication Issues
- Ensure `client_secret.json` is in the correct directory
- Delete `token.json` and re-authenticate if having permission issues
- Check that Google Sheets and Drive APIs are enabled in your project

### CSV Processing Issues
- Ensure CSV has proper headers
- Check that amount column contains numeric data
- Verify date column is in a recognizable format

### Upload Issues
- Check internet connection
- Verify Google Sheets API quotas haven't been exceeded
- Ensure you have edit permissions for the target spreadsheet

## Future Enhancements

- [ ] Duplicate transaction detection and merging
- [ ] Summary sheet with category totals and charts
- [ ] Export functionality to download modified data from Google Sheets
- [ ] Scheduled data synchronization
- [ ] Support for multiple bank account consolidation
- [ ] Advanced categorization rules and machine learning

## Security Notes

- All credential files (`.json`) are excluded from git via `.gitignore`
- CSV files containing sensitive data are also excluded from version control
- OAuth tokens are stored locally and encrypted by Google's auth library
- The tool only requests minimum necessary permissions (file-level access)