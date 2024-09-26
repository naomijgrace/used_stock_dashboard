# clean_data.py

"""
Created on Tue Sep 24 16:45:54 2024

@author: NAOJOH
"""

import os
import re
import pandas as pd
import PyPDF2
from datetime import datetime, timedelta

# ================================
# Constants and Configuration
# ================================

# Current date for file naming
DATE = datetime.now()

# File paths
AUTOGATE_EXCEL_FILE = f'raw_data/autogate_data_{DATE.strftime("%d%m%y")}.xlsx'
USED_STOCK_DATA_FILE = f'raw_data/Stock{DATE.strftime("%d%m%y")}.dat'
REGO_CERT_FOLDER = 'R:/UserData/St Peters RMS Work'

RESULT_FILE = 'used_stock_data.xlsx'

# Regular Expressions
DATE_PATTERN = r"\d{2}-\d{2}-\d{4}"
PROCYCLES_NAME = 'PROCYCLES (HORNSBY) PTY LTD'

# ================================
# Extraction Functions
# ================================

def extract_vin(details_str):
    """Extracts VIN from the Details string."""
    if pd.isna(details_str):
        return pd.NA
    parts = str(details_str).split('|', 1)
    return parts[0].strip() if len(parts) > 1 else pd.NA

def extract_days(age_str):
    """Extracts number of days from the Age string."""
    if pd.isna(age_str):
        return pd.NA
    match = re.match(r'(\d+)\s*days?', str(age_str).lower())
    return int(match.group(1)) if match else pd.NA

def extract_price(price_str):
    """Extracts numeric price from the Price string."""
    if pd.isna(price_str):
        return pd.NA
    match = re.search(r'([\d,]+\.?\d*)', str(price_str).lower())
    if match:
        numeric_str = match.group(1).replace(',', '')
        try:
            return float(numeric_str)
        except ValueError:
            return pd.NA
    return pd.NA

def extract_rego_info(pdf_path):
    """
    Extracts registration details from a PDF file.

    Returns:
        dict: {
            "rego_name": str or None,
            "is_lam": bool,
            "expiry_date": str or None
        }
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = reader.pages[0].extract_text()
            lines = text.split('\n')
            
            # Extract Rego Name
            plate_number = lines[3].split()[0]
            rego_name = lines[7][len(plate_number):].strip()
            
            # Determine if "LA." condition exists
            is_lam = any(line.startswith("LA.") for line in lines[15:17])
            
            # Find the expiry date in lines 10-13
            expiry_date = next(
                (re.search(DATE_PATTERN, lines[i]).group(0) 
                 for i in range(10, 14) if re.search(DATE_PATTERN, lines[i])),
                None
            )
            
            if not expiry_date:
                raise ValueError("Expiry date not found in lines 10-13")
            
            return {
                "rego_name": rego_name,
                "is_lam": is_lam,
                "expiry_date": expiry_date
            }
    except Exception:
        return {
            "rego_name": None,
            "is_lam": False,
            "expiry_date": None
        }

# ================================
# Autogate Data Cleaning
# ================================

def clean_autogate_data():
    """Cleans the Autogate data and returns a cleaned DataFrame."""
    
    # Headers for Autogate Data
    AUTOGATE_HEADERS = [
        'Make', 'Price', 'Odometer', 'Search Views', 'Detailed Views',
        'Lead Count', 'Contact Watchers', 'Age', 'Health', 'Photos'
    ]
    # Read Excel file with headers
    data = pd.read_excel(AUTOGATE_EXCEL_FILE, header=None, names=AUTOGATE_HEADERS)
    
    # Initialize lists to store cleaned data
    cleaned_data = []
    current_row = None
    invalid_rows = []
    
    # Process each row to associate invalid rows with the current valid row
    for _, row in data.iterrows():
        # A valid row has at least one non-NA value excluding the first column
        if row.iloc[1:].notna().any():
            if current_row:
                # Process invalid rows associated with the previous valid row
                if invalid_rows:
                    details = [str(r.iloc[0]) for r in invalid_rows if '|' in str(r.iloc[0])]
                    if details:
                        first_detail = details[0]
                        current_row['Details'] = first_detail
            if current_row:
                cleaned_data.append(current_row)
            
            # Start a new valid row
            current_row = row.to_dict()
            current_row['Details'] = ''
            invalid_rows = []
        else:
            # Collect invalid rows
            invalid_rows.append(row)
    
    # Append the last valid row after the loop
    if current_row:
        if invalid_rows:
            details = [str(r.iloc[0]) for r in invalid_rows if '|' in str(r.iloc[0])]
            if details:
                first_detail = details[0]
                current_row['Details'] = first_detail
        cleaned_data.append(current_row)
    
    # Convert cleaned_data to DataFrame
    cleaned_df = pd.DataFrame(cleaned_data)
    
    # Apply extraction functions
    cleaned_df['VIN'] = cleaned_df['Details'].apply(extract_vin)
    cleaned_df['Parsed Age (Days)'] = cleaned_df['Age'].apply(extract_days)
    cleaned_df['Date Listed'] = cleaned_df['Parsed Age (Days)'].apply(
        lambda x: (DATE - timedelta(days=x)).date() if pd.notna(x) else pd.NA
    )
    cleaned_df['Listed Price'] = cleaned_df['Price'].apply(extract_price)
    
    # Select relevant columns
    final_df = cleaned_df[['VIN', 'Date Listed', 'Listed Price']]
    
    return final_df

# ================================
# Used Stock Data Cleaning
# ================================

def clean_used_stock_data(autogate_df):
    """Cleans the Used Stock data and merges with Autogate data."""
    # Load and preprocess data
    df = pd.read_csv(USED_STOCK_DATA_FILE, delimiter=',')
    
    # Filter for 'For Sale' status and rename columns
    df = df[df['Status Desc.'] == 'For Sale'].drop(columns=['Status Desc.'])
    df.columns = ['Stock Number', 'Date Into Stock', 'Stock Type', 'Make', 'Model', 'VIN', 'Rego Number']
    
    # Replace 'Consignment Stock' with 'Consignment' in 'Stock Type'
    df['Stock Type'] = df['Stock Type'].replace('Consignment Stock', 'Consignment')
    
    # Initialize new columns
    df[['LAMS?', 'Rego Expiry', 'Rego Details']] = pd.NA
    
    # Convert and sort dates
    df['Date Into Stock'] = pd.to_datetime(df['Date Into Stock'], format='%d/%m/%y', errors='coerce')
    df.sort_values(by='Date Into Stock', ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Update 'Rego Number' where length > 5 to empty string
    df.loc[df['Rego Number'].str.len() > 5, 'Rego Number'] = ''
    
    # Filter valid rego numbers (non-empty)
    valid_regos = df.loc[df['Rego Number'].notna() & (df['Rego Number'] != ''), 'Rego Number'].unique()
    
    # Map rego numbers to their files
    file_list = os.listdir(REGO_CERT_FOLDER)
    file_map = {rego: [] for rego in valid_regos}
    
    for file in file_list:
        for rego in valid_regos:
            if rego in file:
                file_map[rego].append(file)
    
    # Process each rego
    for rego, files in file_map.items():
        if files:
            # Select the latest file based on modification time
            latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(REGO_CERT_FOLDER, f)))
            latest_file_path = os.path.join(REGO_CERT_FOLDER, latest_file)
            
            # Extract rego information
            info = extract_rego_info(latest_file_path)
            df.loc[df['Rego Number'] == rego, 'LAMS?'] = 'Yes' if info['is_lam'] else 'No'
            df.loc[df['Rego Number'] == rego, 'Rego Expiry'] = info['expiry_date'] if info['expiry_date'] else ''
            
            # Update 'Rego Details' based on rego name
            if info['rego_name'] == PROCYCLES_NAME:
                pass  # Rego is valid under Procycles; no additional message needed
            elif info['rego_name']:
                df.loc[df['Rego Number'] == rego, 'Rego Details'] = 'Rego not under Procycles'
            else:
                df.loc[df['Rego Number'] == rego, 'Rego Details'] = 'No rego found'

        else:
            # No matching files for the rego
            df.loc[df['Rego Number'] == rego, 'Rego Details'] = 'No rego found'
    
    # Read and process Autogate data
    df_autogate = autogate_df.copy()
    
    # Ensure 'Date Listed' is in datetime format for merging
    df_autogate['Date Listed'] = pd.to_datetime(df_autogate['Date Listed'], errors='coerce')
    
    # Merge 'Date Listed' and 'Listed Price' into main dataframe based on 'VIN'
    df = df.merge(df_autogate, on='VIN', how='left')
    
    # Create 'Status' column
    df['Status'] = ''
    # Add 'Transfer rego' if there is any value in 'Rego Details'
    df.loc[df['Rego Details'].notna() & (df['Rego Details'] != ''), 'Status'] += 'Transfer rego'
    # Add 'Create listing' if 'Date Listed' is empty
    df.loc[df['Date Listed'].isna() | (df['Date Listed'] == ''), 'Status'] += '; Create listing'
    # Clean up 'Status' column by removing leading/trailing semicolons and spaces
    df['Status'] = df['Status'].str.replace('^; ', '', regex=True).str.replace('; $', '', regex=True).str.strip('; ')
    
    # Select and format columns
    df = df[[
        'Stock Number', 'Date Into Stock', 'Make', 'Model', 
        'LAMS?', 'VIN', 'Rego Number', 'Rego Expiry', 'Rego Details', 
        'Date Listed', 'Listed Price', 'Status'
    ]]
    
    # Format date columns
    df['Date Into Stock'] = df['Date Into Stock'].dt.strftime('%d-%b-%Y')
    df['Rego Expiry'] = pd.to_datetime(df['Rego Expiry'], errors='coerce', dayfirst=True).dt.strftime('%d-%b-%Y').fillna('')
    df['Date Listed'] = df['Date Listed'].dt.strftime('%d-%b-%Y').fillna('')
    
    # Save to Excel
    df.to_excel(RESULT_FILE, index=False)
    
    print(f"Used stock data cleaned and saved to {RESULT_FILE}")

# ================================
# Main Execution
# ================================

def main():
    """Main function to execute data cleaning and processing."""
    # Step 1: Clean Autogate Data
    autogate_cleaned_df = clean_autogate_data()
    
    # Step 2: Clean Used Stock Data and Merge with Autogate Data
    clean_used_stock_data(autogate_cleaned_df)

if __name__ == "__main__":
    main()
