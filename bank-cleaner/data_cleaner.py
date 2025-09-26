# data_cleaner.py
"""Data cleaning utilities for banking CSV files."""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def preview_csv(path: Path, n: int = 5) -> pd.DataFrame:
    """Load and preview CSV file with column detection."""
    df = pd.read_csv(path)
    print(f"\nDetected columns: {list(df.columns)}")
    print(f"\nSample rows:")
    print(df.head(n).to_string(index=False))
    return df


def find_default_column(columns: List[str], key_terms: List[str]) -> str:
    """Find default column mapping based on common terms."""
    for term in key_terms:
        for col in columns:
            if term in col.lower():
                return col
    return ""


def ask_column_mapping(df: pd.DataFrame) -> Dict[str, str]:
    """Interactive column mapping with intelligent defaults."""
    cols = list(df.columns)
    
    # Define common column patterns
    column_patterns = {
        'date': ['date', 'trans', 'time', 'posted'],
        'description': ['description', 'desc', 'memo', 'details', 'payee', 'merchant'],
        'amount': ['amount', 'amt', 'value', 'debit', 'credit', 'balance'],
        'category': ['category', 'cat', 'type', 'class']
    }
    
    mapping = {}
    for field, patterns in column_patterns.items():
        mapping[field] = find_default_column(cols, patterns)
    
    print("\nMap columns for core fields. Press Enter to accept default in ( ).")
    for field in ['date', 'description', 'amount', 'category']:
        default = mapping.get(field, "")
        prompt = f"Column for {field} (default: '{default}'): "
        val = input(prompt).strip()
        mapping[field] = val if val else default
    
    return mapping


def clean_amount_column(series: pd.Series) -> pd.Series:
    """Clean and normalize amount column."""
    # Convert to string for cleaning
    s = series.astype(str)
    
    # Remove currency symbols and commas
    s = s.str.replace(r'[$£€¥,]', '', regex=True)
    
    # Handle parentheses notation (12.00) → -12.00
    s = s.str.replace(r'\((.*)\)', r'-\1', regex=True)
    
    # Handle negative signs that might be at the end
    s = s.str.replace(r'(\d+\.?\d*)-$', r'-\1', regex=True)
    
    # Convert to numeric
    return pd.to_numeric(s, errors='coerce')


def clean_date_column(series: pd.Series) -> pd.Series:
    """Clean and parse date column."""
    return pd.to_datetime(series, errors='coerce', dayfirst=False)


def combine_description_fields(df: pd.DataFrame, desc_col: str) -> pd.Series:
    """Combine description with additional note/memo fields."""
    details = df[desc_col].fillna('') if desc_col in df.columns else pd.Series([''] * len(df))
    
    # Look for additional detail columns
    note_candidates = ['Note', 'note', 'Notes', 'Memo', 'memo', 'Reference', 'ref']
    for candidate in note_candidates:
        if candidate in df.columns:
            additional = df[candidate].fillna('')
            details = details + " " + additional
            break
    
    return details.str.strip()


def clean_dataframe(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """Clean and standardize the dataframe based on column mapping."""
    df_clean = df.copy()
    
    # Clean date column
    if mapping['date'] and mapping['date'] in df_clean.columns:
        df_clean['Date'] = clean_date_column(df_clean[mapping['date']])
    else:
        df_clean['Date'] = pd.NaT
    
    # Clean amount column
    if mapping['amount'] and mapping['amount'] in df_clean.columns:
        df_clean['Amount'] = clean_amount_column(df_clean[mapping['amount']])
    else:
        df_clean['Amount'] = 0.0
    
    # Combine description fields
    df_clean['Details'] = combine_description_fields(df_clean, mapping['description'])
    
    # Add category if provided
    if mapping['category'] and mapping['category'] in df_clean.columns:
        df_clean['Category'] = df_clean[mapping['category']].fillna('Uncategorized')
    else:
        df_clean['Category'] = 'Uncategorized'
    
    # Select and reorder final columns
    final_columns = ['Date', 'Amount', 'Details', 'Category']
    df_final = df_clean[final_columns].copy()
    
    # Remove rows with invalid dates or amounts
    df_final = df_final.dropna(subset=['Date', 'Amount'])
    
    return df_final


def categorize_transaction(details: str, amount: float) -> str:
    """Auto-categorize transactions based on details and amount."""
    details_lower = details.lower()
    
    # eBay transactions
    if 'ebay' in details_lower:
        return 'eBay'
    
    # Common income patterns
    income_patterns = ['salary', 'wage', 'deposit', 'transfer in', 'refund']
    if amount > 0 and any(pattern in details_lower for pattern in income_patterns):
        return 'Income'
    
    # Common expense patterns
    expense_categories = {
        'Grocery': ['grocery', 'supermarket', 'food', 'walmart', 'target'],
        'Gas': ['gas', 'fuel', 'petrol', 'shell', 'bp', 'chevron'],
        'Utilities': ['electric', 'gas bill', 'water', 'internet', 'phone'],
        'Dining': ['restaurant', 'cafe', 'pizza', 'mcdonald', 'starbucks'],
        'Shopping': ['amazon', 'store', 'retail', 'purchase']
    }
    
    for category, patterns in expense_categories.items():
        if any(pattern in details_lower for pattern in patterns):
            return category
    
    return 'Other'


def filter_transactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split transactions into different categories."""
    # Add row numbers for linking
    df = df.reset_index(drop=True)
    df['Master_Row'] = df.index + 2  # +2 because sheets are 1-indexed and include header
    
    # Auto-categorize if not already done
    if 'Category' not in df.columns or df['Category'].isna().all():
        df['Category'] = df.apply(lambda row: categorize_transaction(row['Details'], row['Amount']), axis=1)
    
    # Create filtered datasets
    master = df.copy()
    incoming = df[df['Amount'] > 0].copy()
    outgoing = df[df['Amount'] < 0].copy()
    
    # eBay transactions (typically outgoing)
    ebay_mask = df['Details'].str.contains('ebay', case=False, na=False)
    ebay_outgoing = df[ebay_mask & (df['Amount'] < 0)].copy()
    
    # Add source column for filtered views
    for filtered_df in [incoming, outgoing, ebay_outgoing]:
        if not filtered_df.empty:
            filtered_df['Source'] = filtered_df['Master_Row'].apply(lambda x: f"=Master!A{x}")
    
    return master, incoming, outgoing, ebay_outgoing


def save_datasets_to_csv(master: pd.DataFrame, incoming: pd.DataFrame, 
                        outgoing: pd.DataFrame, ebay_outgoing: pd.DataFrame,
                        output_dir: Path = Path("output")) -> Dict[str, Path]:
    """Save all datasets to CSV files in output directory."""
    output_dir.mkdir(exist_ok=True)
    
    files = {
        'master': output_dir / 'cleaned_master.csv',
        'incoming': output_dir / 'incoming_payments.csv',
        'outgoing': output_dir / 'outgoing_payments.csv',
        'ebay': output_dir / 'ebay_outgoing.csv'
    }
    
    datasets = {
        'master': master,
        'incoming': incoming,
        'outgoing': outgoing,
        'ebay': ebay_outgoing
    }
    
    for name, df in datasets.items():
        # Remove Master_Row column from CSV exports (keep it only for Google Sheets linking)
        export_df = df.drop(columns=['Master_Row'], errors='ignore')
        export_df.to_csv(files[name], index=False)
    
    print(f"\nSaved CSV files to {output_dir}:")
    for name, path in files.items():
        print(f"  - {path} ({len(datasets[name])} rows)")
    
    return files


def get_preview_data(df: pd.DataFrame, n: int = 5) -> str:
    """Get formatted preview of cleaned data."""
    if df.empty:
        return "No data to preview."
    
    preview_cols = ['Date', 'Amount', 'Details']
    available_cols = [col for col in preview_cols if col in df.columns]
    
    return df[available_cols].head(n).to_string(index=False)