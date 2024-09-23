# Imports
import os
import re
from datetime import datetime, timedelta
import pandas as pd
import PyPDF2

# Constants
DATE = datetime.now()

DATA_FILE = f'Stock{DATE.strftime("%d%m%y")}.dat'
REGO_CERT_FOLDER = 'R:/UserData/St Peters RMS Work'
AUTOGATE_FILE = 'autogate_data.xlsx'

RESULT_FILE = f'used_stock_data.xlsx'

DATE_PATTERN = r"\d{2}-\d{2}-\d{4}"
PROCYCLES_NAME = 'PROCYCLES (HORNSBY) PTY LTD'


def extract_rego_info(pdf_path):
    """
    Extracts rego details from a PDF file.

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


def determine_expiry_status(expiry_date_str):
    """
    Determines the expiry status based on the expiry date string.

    Args:
        expiry_date_str (str): Expiry date in 'dd-mm-yyyy' format.

    Returns:
        str: 'Rego expired', 'Rego expires soon', or ''
    """
    try:
        expiry_date = datetime.strptime(expiry_date_str, '%d-%m-%Y')
        if expiry_date < DATE:
            return 'Rego expired'
        elif expiry_date <= DATE + timedelta(days=30):
            return 'Rego expires soon'
        else:
            return ''
    except ValueError:
        return ''


def main():
    try:
        # Load and preprocess data
        df = pd.read_csv(DATA_FILE, delimiter=',')
        
        df = df[df['Status Desc.'] == 'For Sale'].drop(columns=['Status Desc.'])
        df.columns = ['Stock Number', 'Date Into Stock', 'Stock Type', 'Make', 'Model', 'VIN', 'Rego Number']
        
        # Replace 'Consignment Stock' with 'Consignment' in 'Stock Type'
        df['Stock Type'] = df['Stock Type'].replace('Consignment Stock', 'Consignment')
        
        # Initialize new columns
        df[['LAMS?', 'Rego Expiry', 'Rego Details', 'Rego Certificate']] = ''
        
        # Convert and sort dates
        df['Date Into Stock'] = pd.to_datetime(df['Date Into Stock'], format='%d/%m/%y')
        df.sort_values(by='Date Into Stock', ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Update 'Rego Number' where length > 5 to empty string
        df.loc[df['Rego Number'].str.len() > 5, 'Rego Number'] = ''
        
        # Filter valid rego numbers (non-empty)
        valid_regos = df.loc[df['Rego Number'] != '', 'Rego Number'].unique()
        
        file_list = os.listdir(REGO_CERT_FOLDER)
        file_map = {rego: [] for rego in valid_regos}

        # Map rego numbers to their files
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
                df.loc[df['Rego Number'] == rego, 'Rego Certificate'] = latest_file_path
                
                # Extract rego information
                info = extract_rego_info(latest_file_path)
                df.loc[df['Rego Number'] == rego, ['LAMS?', 'Rego Expiry']] = [
                    'Yes' if info['is_lam'] else 'No',
                    info['expiry_date'] if info['expiry_date'] else ''
                ]
                
                # Initialize a list to hold 'Rego Details' messages
                details_messages = []
                
                # Determine and append expiry status
                if info['expiry_date']:
                    expiry_status = determine_expiry_status(info['expiry_date'])
                    if expiry_status:
                        details_messages.append(expiry_status)
                
                # Update 'Rego Details' based on rego name
                if info['rego_name'] == PROCYCLES_NAME:
                    pass  # Rego is valid under Procycles; no additional message needed
                elif info['rego_name']:
                    details_messages.append('Rego not under Procycles')
                else:
                    details_messages.append('No rego found')
                
                # Combine all messages and update 'Rego Details'
                combined_details = '; '.join(details_messages)
                df.loc[df['Rego Number'] == rego, 'Rego Details'] = combined_details
            else:
                # No matching files for the rego
                df.loc[df['Rego Number'] == rego, 'Rego Details'] = 'No rego found'
        
        # Read and process AUTOGATE_FILE
        df_autogate = pd.read_excel(AUTOGATE_FILE)
        
        # Rename columns
        df_autogate.columns = ['Stock Number', 'Date Listed', 'Listed Price']
        
        # Ensure 'Date Listed' is in '%d-%b-%Y' format
        df_autogate['Date Listed'] = pd.to_datetime(df_autogate['Date Listed'], errors='coerce').dt.strftime('%d-%b-%Y')
        
        # Merge 'Date Listed' and 'Listed Price' into main dataframe based on 'Stock Number'
        df = df.merge(df_autogate, on='Stock Number', how='left')
        
        # Remove 'Rego expired' and 'Rego expires soon' from 'Rego Details'
        df['Rego Details'] = df['Rego Details'].replace({'Rego expired': '', 'Rego expires soon': ''}, regex=True)
        df['Rego Details'] = df['Rego Details'].str.replace(';;', ';').str.strip('; ')
        
        # Create 'Status' column
        df['Status'] = ''
        # Add 'Transfer rego' if there is any value in 'Rego Details'
        df.loc[df['Rego Details'].notna() & (df['Rego Details'] != ''), 'Status'] += 'Transfer rego'
        # Add 'Create listing' if 'Date Listed' is empty
        df.loc[df['Date Listed'].isna() | (df['Date Listed'] == ''), 'Status'] += '; Create listing'
        # Clean up 'Status' column by removing leading/trailing semicolons and spaces
        df['Status'] = df['Status'].str.replace('^; ', '', regex=True).str.replace('; $', '', regex=True).str.strip('; ')
        
        # Select and format columns (dropping 'Rego Certificate')
        df = df[['Stock Number', 'Date Into Stock', 'Make', 'Model', 
                 'LAMS?', 'VIN', 'Rego Number', 'Rego Expiry', 'Rego Details', 
                 'Date Listed', 'Listed Price', 'Status']]
        
        df['Date Into Stock'] = df['Date Into Stock'].dt.strftime('%d-%b-%Y')
        df['Rego Expiry'] = pd.to_datetime(df['Rego Expiry'], errors='coerce', dayfirst=True).dt.strftime('%d-%b-%Y').fillna('')
        
        # Save to Excel
        df.to_excel(RESULT_FILE, index=False)
        
    except Exception:
        pass  # Handle exceptions silently or implement alternative error handling as needed


if __name__ == "__main__":
    main()






