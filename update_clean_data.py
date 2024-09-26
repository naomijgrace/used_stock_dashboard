# clean_data.py

"""
Created on Tue Sep 24 16:45:54 2024

Author: NAOJOH
"""

import os
import re
from datetime import datetime, timedelta

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# ================================
# Constants and Configuration
# ================================

# Current date for file naming
DATE = datetime.now()

# File paths
RAW_DATA_DIR = 'raw_data'
AUTOGATE_EXCEL_FILE = os.path.join(RAW_DATA_DIR, f'autogate_data_{DATE.strftime("%d%m%y")}.xlsx')
USED_STOCK_DATA_FILE = os.path.join(RAW_DATA_DIR, f'Stock{DATE.strftime("%d%m%y")}.dat')

RESULT_FILE = 'used_stock_data_test.xlsx'

# Selenium Configuration
SELENIUM_OPTIONS = Options()
SELENIUM_OPTIONS.add_argument('--headless')  # Run in headless mode
SELENIUM_OPTIONS.add_argument('--disable-gpu')
SELENIUM_OPTIONS.add_argument('--no-sandbox')

# Maximum number of worker threads for Selenium
MAX_WORKERS = 5  # Adjust based on system capabilities

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
    match = re.search(r'([\d,]+\.?\d*)', str(price_str))
    if match:
        numeric_str = match.group(1).replace(',', '')
        try:
            return float(numeric_str)
        except ValueError:
            return pd.NA
    return pd.NA

# ================================
# Selenium WebDriver Setup
# ================================

def extract_rego_info(rego_number):
    """Extracts registration expiry date and LA condition from NSW vehicle registration."""
    driver = webdriver.Chrome(options=SELENIUM_OPTIONS)

    try:
        # Navigate to the NSW vehicle registration page
        driver.get("https://check-registration.service.nsw.gov.au/frc?isLoginRequired=true")

        # Input the registration number
        regnum = driver.find_element(By.CSS_SELECTOR, "input#plateNumberInput")
        regnum.send_keys(rego_number)

        # Accept the Terms and Conditions
        terms_checkbox = driver.find_element(By.CSS_SELECTOR, "input#termsAndConditions")
        terms_checkbox.click()

        # Submit the form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button#id-2")
        submit_button.click()

        # Wait for the results to load
        driver.implicitly_wait(10)

        # Extract registration expiry
        registration_expiry_text = driver.find_element(By.CSS_SELECTOR, "div.sc-ibxdXY p:nth-of-type(3) strong").text
        if ':' in registration_expiry_text:
            cleaned_expiry_text = registration_expiry_text.split(':', 1)[1].strip()
        else:
            # Unexpected format; treat as invalid rego
            print(f"Unexpected format for registration expiry text: '{registration_expiry_text}' for Rego Number: {rego_number}")
            return {
                'expiry_date': pd.NA,
                'is_lams': pd.NA
            }

        registration_expiry_date = datetime.strptime(cleaned_expiry_text, "%d %B %Y")

        # Extract condition codes
        condition_codes = driver.find_element(By.XPATH, "//div[text()='Condition codes']/following-sibling::div").text
        contains_la = 'LA' in condition_codes

        return {
            'expiry_date': registration_expiry_date,
            'is_lams': contains_la
        }

    except NoSuchElementException as e:
        # Handle cases where elements are not found, indicating invalid rego number
        print(f"Invalid rego number '{rego_number}': {e}")
        return {
            'expiry_date': pd.NA,
            'is_lams': pd.NA
        }

    except Exception as e:
        # Handle other unforeseen exceptions
        print(f"An error occurred while processing rego number '{rego_number}': {e}")
        return {
            'expiry_date': pd.NA,
            'is_lams': pd.NA
        }

    finally:
        driver.quit()

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
                        current_row['Details'] = details[0]
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
                current_row['Details'] = details[0]
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
def clean_used_stock_data(autogate_df, rego_limit=None):
    """Cleans the Used Stock data and updates it directly with rego information."""
    df = pd.read_csv(USED_STOCK_DATA_FILE, delimiter=',')
    
    # Filter for 'For Sale' status and rename columns
    df = df[df['Status Desc.'] == 'For Sale'].drop(columns=['Status Desc.'])
    df.columns = ['Stock Number', 'Date Into Stock', 'Stock Type', 'Make', 'Model', 'VIN', 'Rego Number']
    
    # Replace 'Consignment Stock' with 'Consignment' in 'Stock Type'
    df['Stock Type'].replace('Consignment Stock', 'Consignment', inplace=True)
    
    # Convert and sort dates
    df['Date Into Stock'] = pd.to_datetime(df['Date Into Stock'], format='%d/%m/%y', errors='coerce')
    df.sort_values(by='Date Into Stock', ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Update 'Rego Number' where length > 5 to empty string
    df.loc[df['Rego Number'].str.len() > 5, 'Rego Number'] = ''
    
    # Initialize 'LAMS?' and 'Rego Expiry' columns
    df[['LAMS?', 'Rego Expiry']] = pd.NA
    
    # Check if RESULT_FILE exists
    if os.path.exists(RESULT_FILE):
        existing_df = pd.read_excel(RESULT_FILE)
        
        # Merge df with existing_df on 'VIN'
        df = df.merge(existing_df[['VIN', 'LAMS?', 'Rego Expiry']], on='VIN', how='left', suffixes=('', '_existing'))
        
        # Use combine_first to fill missing values
        df['LAMS?'] = df['LAMS?'].combine_first(df['LAMS?_existing'])
        df['Rego Expiry'] = df['Rego Expiry'].combine_first(df['Rego Expiry_existing'])
        
        # Drop the '_existing' columns
        df.drop(columns=['LAMS?_existing', 'Rego Expiry_existing'], inplace=True)
    else:
        existing_df = pd.DataFrame()
    
    # Identify rego numbers that need processing
    regos_to_process = df.loc[
        (df['Rego Number'].notna()) & (df['Rego Number'] != '') & (df['LAMS?'].isna()), 'Rego Number'
    ].unique()
    
    # Apply rego limit for testing
    if rego_limit:
        regos_to_process = regos_to_process[:rego_limit]
    
    # **New Addition: Print the new regos to be processed**
    if len(regos_to_process) > 0:
        print("New rego numbers to process:")
        for rego in regos_to_process:
            print(f"- {rego}")
    else:
        print("No new rego numbers to process.")
    
    # Process rego numbers and update 'LAMS?' and 'Rego Expiry'
    for rego in regos_to_process:
        info = extract_rego_info(rego)
        df.loc[df['Rego Number'] == rego, 'LAMS?'] = 'Yes' if info['is_lams'] is True else 'No'
        df.loc[df['Rego Number'] == rego, 'Rego Expiry'] = info['expiry_date'].strftime('%d-%b-%Y') if isinstance(info['expiry_date'], datetime) else ''
    
    # Read and process Autogate data
    autogate_df['Date Listed'] = pd.to_datetime(autogate_df['Date Listed'], errors='coerce')
    
    # Merge Autogate data with Used Stock data on 'VIN'
    df = df.merge(autogate_df, on='VIN', how='left')
    
    # Create 'Status' column
    df['Status'] = df['Date Listed'].isna().map({True: 'Create listing', False: ''})
    
    # Format date columns
    df['Date Into Stock'] = df['Date Into Stock'].dt.strftime('%d-%b-%Y')
    df['Date Listed'] = df['Date Listed'].dt.strftime('%d-%b-%Y').fillna('')
    
    # Save to Excel
    df.to_excel(RESULT_FILE, index=False)
    
    print(f"Used stock data cleaned and saved to {RESULT_FILE}")

# ================================
# Main Execution
# ================================

def main(rego_limit=None):
    """Main function to execute data cleaning and processing."""
    # Step 1: Clean Autogate Data
    autogate_cleaned_df = clean_autogate_data()

    # Step 2: Clean Used Stock Data and Update with Rego Info
    clean_used_stock_data(autogate_cleaned_df, rego_limit=rego_limit)

if __name__ == "__main__":
    main()