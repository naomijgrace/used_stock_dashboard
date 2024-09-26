# dashboard.py

#cd C:\Users\naojoh\Desktop\projects_v3\project_beta_v2
#python -m streamlit run dashboard.py
# http://192.168.42.182:8501

"""
Created on Fri Sep 20 10:14:55 2024

Author: NAOJOH
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from streamlit_pills import pills

DATE = datetime.now()

# ============================
# Set Page Configuration
# ============================
st.set_page_config(
    page_title="Used Stock Dashboard",
    page_icon="🏍️",
    layout="wide",  # Sets the app to wide mode
    initial_sidebar_state="collapsed"  # Sidebar is collapsed by default
)

# ============================
# Custom CSS for Enhanced Aesthetics
# ============================

def add_custom_css():
    """Add custom CSS to the Streamlit app for enhanced aesthetics."""
    custom_css = """
        <style>
            /* Import Google Font */
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

            /* Apply font to the entire app */
            body, .css-1d391kg, .css-1adrfps {
                font-family: 'Roboto', sans-serif;
            }

            /* Style the title */
            .title {
                color: #333333;
                margin-bottom: 5px;
            }

            /* Scrollable Table Container */
            .scrollable-table {
                max-height: calc(100vh - 300px); /* Adjusted height */
                overflow-y: auto;
                display: block;
                width: 100%;
                margin: 0;
                padding: 0;
                border: 1px solid #ddd; /* Added border */
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                background-color: #ffffff;
            }

            /* Table Styling */
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 0;
                padding: 0;
                table-layout: fixed; /* Fixed table layout */
            }
            th {
                text-align: center; /* Center-align all header columns */
                padding: 10px 8px; /* Reduced padding for better spacing */
                border: 1px solid #ddd;
                background-color: #757575; /* Changed header color to grey */
                color: white;
                z-index: 1;
                font-weight: 700;
                position: sticky;
                top: 0;
            }
            td {
                text-align: left; /* Left-align all data cells by default */
                padding: 10px 8px; /* Reduced padding for better spacing */
                border: 1px solid #ddd;
                margin: 0;
                overflow: hidden;
                white-space: normal; /* Allow text to wrap */
                word-wrap: break-word; /* Break long words */
                font-size: 14px;
            }
            tr {
                height: 3em; /* Adjust as needed for desired row height */
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f1f1f1; /* Hover effect */
            }
            /* Column Widths */
            th:nth-child(1), td:nth-child(1) {
                width: 8%; 
            }
            th:nth-child(2), td:nth-child(2) {
                width: 9%; 
            }
            th:nth-child(3), td:nth-child(3) {
                width: 6%; 
            }
            th:nth-child(4), td:nth-child(4) {
                width: 20%; 
            }
            th:nth-child(5), td:nth-child(5) {
                width: 12%; 
            }
            th:nth-child(6), td:nth-child(6) {
                width: 7%; 
            }
            th:nth-child(7), td:nth-child(7) {
                width: 16%; 
            }
            th:nth-child(8), td:nth-child(8) {
                width: 8%; 
            }
            th:nth-child(9), td:nth-child(9) {
                width: 9%; 
            }
            th:nth-child(10), td:nth-child(10) {
                width: 20%; 
            }

            /* Center Alignment for Specific Columns */
            td:nth-child(3){
                text-align: center !important;
            }

            /* Style for Disabled Buttons and Status Buttons */
            button[disabled], span.status-button {
                opacity: 0.9;
                border: none;
                border-radius: 5px;
                padding: 4px 8px;
                color: white;
                font-size: 14px;
                display: inline-block;
            }

            /* Prevent last button from having extra margin */
            span.status-button:last-child {
                margin-right: 0;
            }

            /* Footer Styling */
            footer {
                visibility: hidden;
            }
        </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# ============================
# Function Definitions
# ============================

@st.cache_data
def load_data(file_path):
    """Load data from the specified Excel file and fill NaN values."""
    return pd.read_excel(file_path).fillna('')

def preprocess_data(df):
    """Preprocess the DataFrame by converting columns and checking for required columns."""
    required_columns = ['Stock Number', 'Date Into Stock', 'Make', 'Model', 'VIN', 'LAMS?',
                        'Rego Number', 'Rego Expiry', 'Listed Price', 'Date Listed', 'Status']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"⚠️ Missing columns in the dataset: {', '.join(missing_columns)}")
        st.stop()
    else:
        # Convert date columns
        date_columns = ['Date Into Stock', 'Rego Expiry', 'Date Listed']
        for col in date_columns:
            df[col + '_dt'] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
        # Convert price to numeric
        df['Listed Price_num'] = pd.to_numeric(df['Listed Price'], errors='coerce')
        return df

def create_inactive_make_button(make):
    """Create smaller inactive buttons for the 'Make' column."""
    colors = {
        "BMW": "#0166B1",
        "KAW": "#6BBF23",
        "KTM": "#FF6600",
    }
    background_color = colors.get(make.upper(), "lightgrey")
    return f'<button disabled style="background-color:{background_color}; border:none; border-radius:5px; padding:4px 8px; color:white; font-size: 14px;">{make}</button>'

def create_lams_button(lams_value):
    """Create an inactive button for LAMS status if applicable."""
    if lams_value.strip().lower() == 'yes':
        return '<button disabled style="background-color:#A9A9A9; border:none; border-radius:5px; padding:2px 6px; color:white; font-size: 12px; margin-left: 4px;">LAMS</button>'
    else:
        return ''

def create_status_buttons(status):
    """Create a composite status button combining Status values."""
    buttons = []
    # Rego Status Button
    if 'transfer rego' in status.lower():
        buttons.append(
            '<span class="status-button" style="background-color:#A9A9A9; margin-right: 4px;">❓ Transfer rego</span>'
        )
    # Create Listing Button
    if 'create listing' in status.lower():
        buttons.append(
            '<span class="status-button" style="background-color:#A9A9A9; margin-right: 4px;">❗ Create listing</span>'
        )
    # Combine all buttons into a single string separated by spaces
    return ' '.join(buttons) if buttons else ''

def create_rego_expiry_button(expiry_date):
    """Create an inactive button indicating 'Expired' or 'Expires soon' based on the expiry date."""
    # Convert the expiry date to a datetime object
    expiry_datetime = pd.to_datetime(expiry_date, errors='coerce', dayfirst=True)

    # Determine status
    if expiry_datetime < DATE:
        return '<span class="status-button" style="background-color:#FF6347; margin-left: 4px;">Expired</span>'
    elif expiry_datetime < DATE + timedelta(days=30):
        return '<span class="status-button" style="background-color:#FFA500; margin-left: 4px;">Expires soon</span>'
    else:
        return ''  # No button if status is 'Valid' or 'Unknown'
    

def filter_data(df, selected_make, lams_only, create_listing_only, transfer_rego_only, stock_number, rego_number, sort_by, sort_order):
    """Apply filters, search, and sorting to the DataFrame and return a copy."""
    df_filtered = df.copy()
    
    # ----------------------------
    # Apply Filtering
    # ----------------------------
    
    # Filter by Make
    if selected_make != "ALL":
        if selected_make == "OTHER":
            df_filtered = df_filtered[~df_filtered['Make'].str.contains('BMW|KAW|KTM', case=False, na=False)].copy()
        else:
            df_filtered = df_filtered[df_filtered['Make'].str.contains(selected_make, case=False, na=False)].copy()
    
    # Filter by LAMS Approved
    if lams_only:
        df_filtered = df_filtered[df_filtered['LAMS?'].str.strip().str.lower() == 'yes'].copy()
    
    # Filter for Create Listing Only
    if create_listing_only:
        df_filtered = df_filtered[df_filtered['Status'].str.contains('Create listing', case=False, na=False)].copy()
    
    # Filter for Transfer Rego Only
    if transfer_rego_only:
        df_filtered = df_filtered[df_filtered['Status'].str.contains('Transfer rego', case=False, na=False)].copy()
    
    # ----------------------------
    # Apply Search
    # ----------------------------
    
    if stock_number:
        df_filtered = df_filtered[
            df_filtered['Stock Number'].astype(str).str.contains(stock_number, case=False, na=False)
        ].copy()
    
    if rego_number:
        df_filtered = df_filtered[
            df_filtered['Rego Number'].astype(str).str.contains(rego_number, case=False, na=False)
        ].copy()
    
    # ----------------------------
    # Apply Sorting
    # ----------------------------
    
    if sort_by:
        sort_col = sort_by
        # Use datetime and numeric columns for sorting if applicable
        if sort_by == 'Date Into Stock':
            sort_col = 'Date Into Stock_dt'
        elif sort_by == 'Rego Expiry':
            sort_col = 'Rego Expiry_dt'
        elif sort_by == 'Date Listed':
            sort_col = 'Date Listed_dt'
        
        ascending = True if sort_order == "Oldest first" else False
        df_filtered = df_filtered.sort_values(by=sort_col, ascending=ascending)
    
    return df_filtered

def display_dataframe(df_filtered):
    """Convert the DataFrame to HTML and display it with custom styling."""
    # Reset index to ensure unique indices
    df_filtered = df_filtered.reset_index(drop=True)

    # ----------------------------
    # Format 'Listed Price' as currency
    # ----------------------------
    df_filtered['Listed Price'] = df_filtered['Listed Price_num'].apply(
        lambda x: f"${x:,.2f}" if pd.notnull(x) else ""
    )
    
    # ----------------------------
    # Apply the inactive button for the 'Make' column
    # ----------------------------
    df_filtered['Make'] = df_filtered['Make'].fillna('').astype(str).apply(create_inactive_make_button)
    
    # ----------------------------
    # Integrate 'LAMS?' into 'Model' column using vectorized operations
    # ----------------------------
    df_filtered['Model'] = df_filtered['Model'].fillna('').astype(str) + ' ' + df_filtered['LAMS?'].fillna('').astype(str).apply(create_lams_button)
    
    
    # ----------------------------
    # Process 'Rego Expiry' column: keep date as text and add status button
    # ----------------------------
    df_filtered['Rego Expiry'] = df_filtered['Rego Expiry'].fillna('').astype(str).apply(
        lambda x: f"{x} {create_rego_expiry_button(x)}"
    )
    
    # ----------------------------
    # Create 'Status' column by combining 'Rego Status', 'Rego Number', and 'Date Listed'
    # ----------------------------
    df_filtered['Status'] = df_filtered['Status'].fillna('').astype(str).apply(create_status_buttons)
    
    # ----------------------------
    # Define columns to display
    # ----------------------------
    columns_to_display = ['Stock Number', 'Date Into Stock', 'Make', 'Model', 'VIN',
                          'Rego Number', 'Rego Expiry', 'Listed Price', 'Date Listed', 'Status']
    df_filtered = df_filtered[columns_to_display]
    
    # ----------------------------
    # Drop unnecessary columns
    # ----------------------------
    columns_to_drop = ['Date Into Stock_dt', 'Rego Expiry_dt', 'Date Listed_dt', 'Listed Price_num', 'LAMS?']
    df_filtered = df_filtered.drop(columns=columns_to_drop, errors='ignore')
    
    # ----------------------------
    # Convert the DataFrame to HTML for rendering buttons, hiding the index
    # ----------------------------
    html_table = df_filtered.to_html(escape=False, index=False)
    
    # ----------------------------
    # Render the table inside a scrollable div
    # ----------------------------
    st.markdown(f'<div class="scrollable-table">{html_table}</div>', unsafe_allow_html=True)



# ============================
# Main Application
# ============================

def main():
    # Add custom CSS
    add_custom_css()

    # ============================
    # Load and Preprocess Data
    # ============================
    RESULT_FILE = 'used_stock_data.xlsx'

    if os.path.exists(RESULT_FILE):
        try:
            df_all = load_data(RESULT_FILE)
        except Exception as e:
            st.error(f"⚠️ Error reading the Excel file: {e}")
            st.stop()
    else:
        st.error(f"⚠️ File {RESULT_FILE} does not exist.")
        st.stop()
    
    # Preprocess Data
    df_all = preprocess_data(df_all)

    st.title("🏍️ Used Stock Dashboard")
    st.markdown(f"Last Updated: {DATE.strftime('%d-%m-%Y')}")

    # ============================
    # Sidebar for Additional Filters
    # ============================
    with st.sidebar:
        # ============================
        # Filter Section
        # ============================
        st.header("🔍 Filter")
        
        # Make Selection using streamlit_pills
        make_options = ["ALL", "BMW", "KAW", "KTM", "OTHER"]
        selected_make = pills("Filter by Make", make_options)
        
        # LAMS Approved Only Checkbox
        lams_only = st.checkbox("Show LAMS approved only")
        
        # Show stock to create listings for
        create_listing_only = st.checkbox("Show stock to create listings for")
        
        # Show stock that needs rego transferred
        transfer_rego_only = st.checkbox("Show stock that needs rego transferred")
        
        st.markdown("---")
        
        # ============================
        # Sort Section
        # ============================
        st.header("📈 Sort")
        
        # Sort By Dropdown
        sort_options = ["Date Into Stock", "Rego Expiry", "Date Listed"]
        sort_by = st.selectbox("Sort By", sort_options, index=0)
        
        # Sort Order Radio Buttons
        sort_order = st.radio("Sort Order", ["Newest first", "Oldest first"], index=0)
        
        st.markdown("---")
        
        # ============================
        # Search Section
        # ============================
        st.header("🔎 Search")

        # Search by Stock Number
        stock_number = st.text_input("Search by Stock Number", placeholder="U12345")
        
        # Search by Rego Number
        rego_number = st.text_input("Search by Rego Number", placeholder="ABC12")
    
    # ============================
    # Apply Filters, Sorting, and Search
    # ============================
    df_filtered = filter_data(
        df_all,
        selected_make,
        lams_only,
        create_listing_only,
        transfer_rego_only,
        stock_number,
        rego_number,
        sort_by,
        sort_order
    )
    
    # ============================
    # Display the filtered DataFrame
    # ============================
    st.markdown("<br>", unsafe_allow_html=True)  # Add some space
    display_dataframe(df_filtered)

    # ============================
    # Footer (Optional)
    # ============================
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888888;'>© 2024 NAOJOH. All rights reserved.</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()






























