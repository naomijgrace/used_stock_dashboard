# -*- coding: utf-8 -*-
# cd C:\Users\naojoh\Desktop\projects_v3\PROJECT_BETA
# python -m streamlit run dashboard.py
"""
Created on Fri Sep 20 10:14:55 2024

@author: NAOJOH
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from st_tabs import TabBar  # Importing st_tabs

# Set the page configuration at the very top
st.set_page_config(
    page_title="🏍️ Used Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",  # Initially collapsed since we're removing the sidebar
)

# ============================
# Add Custom CSS for Enhanced Aesthetics and Layout Adjustments
# ============================
def add_custom_css():
    """Add custom CSS to the Streamlit app for enhanced aesthetics and layout."""
    custom_css = """
        <style>
            /* Import Google Font */
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

            /* Apply font to the entire app */
            body, .css-1d391kg, .css-1adrfps {
                font-family: 'Roboto', sans-serif;
            }

            /* Style the title */
            .css-1aumxhk {
                color: #333333;
                text-align: center;
                margin-bottom: 5px; /* Reduced margin */
            }

            /* Style the subtitle */
            .css-18e3th9 {
                color: #555555;
                text-align: center;
                margin-top: 0;
                margin-bottom: 10px; /* Reduced margin */
            }

            /* Scrollable Table Container */
            .scrollable-table {
                max-height: calc(100vh - 250px); /* Adjusted height */
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
            th, td {
                text-align: center;
                padding: 10px 8px; /* Reduced padding for better spacing */
                border: 1px solid #ddd;
                margin: 0;
                overflow: hidden;
                white-space: normal; /* Allow text to wrap */
                word-wrap: break-word; /* Break long words */
                font-size: 14px;
            }
            th {
                position: sticky;
                top: 0;
                background-color: #757575; /* Changed header color to grey */
                color: white;
                z-index: 1;
                font-weight: 700;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f1f1f1; /* Hover effect */
            }

            /* Column Widths */
            th:nth-child(1), td:nth-child(1) {
                width: 8%; /* 'Make' column */
            }
            th:nth-child(2), td:nth-child(2) {
                width: 10%; /* 'Stock Number' */
            }
            th:nth-child(3), td:nth-child(3) {
                width: 6%; /* 'Rego Number' */
            }
            th:nth-child(4), td:nth-child(4) {
                width: 20%; /* 'Rego Expiry' or other column */
            }
            th:nth-child(5), td:nth-child(5) {
                width: 6%; /* 'Date into Stock' */
            }
            th:nth-child(6), td:nth-child(6) {
                width: 13%; /* 'Model' */
            }
            th:nth-child(7), td:nth-child(7) {
                width: 8%; /* Another column */
            }
            th:nth-child(8), td:nth-child(8) {
                width: 10%; /* Adjust percentage as needed */
            }

            /* Text Alignment for Specific Columns */
            td:nth-child(1), td:nth-child(4), td:nth-child(6), td:nth-child(7){
                text-align: left !important;
            }

            /* Style for Disabled Buttons */
            button[disabled] {
                cursor: not-allowed;
                opacity: 0.7;
            }

            /* Footer Styling */
            footer {
                visibility: hidden;
            }

            /* TabBar Custom Styling */
            .tab-bar-container {
                margin-bottom: 10px; /* Reduced margin to bring table closer */
            }
            .tab-bar {
                display: flex;
                justify-content: center;
                gap: 10px;
            }
            .tab-bar button {
                background-color: #757575; /* Changed tab background to grey */
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s;
            }
            .tab-bar button.active {
                background-color: #A9A9A9; /* Light grey for active tab */
            }
            .tab-bar button:hover {
                background-color: #6E6E6E; /* Darker grey on hover */
            }

            /* Alignment for Filter Checkbox (Removed since filter is removed) */
            .filter-checkbox {
                display: flex;
                align-items: center;
                justify-content: center;
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

def create_inactive_make_button(make):
    """Create inactive buttons for the 'Make' column, wrapping the actual value inside the button."""
    colors = {
        "BMW": "#0166B1",
        "KAW": "#6BBF23",
        "KTM": "#FF6600",
    }
    background_color = colors.get(make, "lightgrey")
    return f'<button disabled style="background-color:{background_color}; border:none; border-radius:10px; padding:2px 8px; color:white;">{make}</button>'

def create_rego_expiry_button(expiry_date):
    """Create inactive buttons for the 'Rego Expiry' column."""
    try:
        # Convert the expiry date to a datetime object
        expiry_datetime = pd.to_datetime(expiry_date, errors='coerce', dayfirst=True)

        # Check today's date and one month from today
        today = datetime.now()
        one_month_from_today = today + timedelta(days=30)

        # Check if the expiry date is before today (red) or less than a month from today (yellow)
        if expiry_datetime and expiry_datetime < today:
            color = "#F05858"
        elif expiry_datetime and expiry_datetime < one_month_from_today:
            color = "#FFDB58"
        else:
            return expiry_date
        return f'<button disabled style="background-color:{color}; border:none; border-radius:10px; padding:2px 8px;">{expiry_date}</button>'
    except Exception:
        return expiry_date  # If conversion fails, return the original expiry date

def filter_data(df, selected_make):
    """Apply Make filters to the DataFrame and return a copy."""
    if selected_make != "ALL":
        if selected_make == "OTHER":
            df_filtered = df[~df['Make'].str.contains('BMW|KAW|KTM', case=False, na=False)].copy()
        else:
            df_filtered = df[df['Make'].str.contains(selected_make, case=False, na=False)].copy()
    else:
        df_filtered = df.copy()

    return df_filtered

def add_custom_css_table():
    """Add custom CSS specifically for the table."""
    custom_css_table = """
        <style>
            /* Additional Table Styling if needed */
        </style>
    """
    st.markdown(custom_css_table, unsafe_allow_html=True)

def display_dataframe(df_filtered):
    """Convert the DataFrame to HTML and display it with custom styling."""

    # Drop 'Rego Certificate' and 'Rego Details' columns if they exist
    columns_to_drop = ['Rego Certificate', 'Rego Details']
    df_filtered = df_filtered.drop(columns=[col for col in columns_to_drop if col in df_filtered.columns])

    # Wrap the 'Make' column values in inactive buttons
    if 'Make' in df_filtered.columns:
        df_filtered['Make'] = df_filtered['Make'].apply(create_inactive_make_button)
    else:
        st.warning("📌 'Make' column not found in the dataset.")

    # Apply the inactive button for the 'Rego Expiry' column
    if 'Rego Expiry' in df_filtered.columns:
        df_filtered['Rego Expiry'] = df_filtered['Rego Expiry'].apply(create_rego_expiry_button)
    else:
        st.warning("📌 'Rego Expiry' column not found in the dataset.")

    # Apply custom CSS
    add_custom_css_table()

    # Convert the DataFrame to HTML for rendering buttons in the 'Make' and 'Rego Expiry' columns, hiding the index
    html_table = df_filtered.to_html(escape=False, index=False)

    # Render the table inside a scrollable div
    st.markdown(f'<div class="scrollable-table">{html_table}</div>', unsafe_allow_html=True)

# ============================
# TabBar Implementation with st_tabs
# ============================

def create_tab_bar(tab_options):
    """Create a styled TabBar using st_tabs."""
    component1 = TabBar(
        tabs=tab_options,
        default=0,
        background="#757575",   # Changed to grey
        color="white",           # White text
        activeColor="#A9A9A9",   # Light grey for active tab
        fontSize="16px"
        # Removed 'borderRadius' and 'padding' as they are unsupported
    )
    return component1

# ============================
# Main Application
# ============================

def main():
    # Add custom CSS
    add_custom_css()

    # Title and Subtitle
    st.title("🏍️ Used Stock Dashboard")
    st.markdown("### Monitor and Analyze Your Used Stock Inventory")

    # Define the available "Make" options
    tab_options = ["ALL", "BMW", "KAW", "KTM", "OTHER"]

    # Create TabBar with customized colors and styles
    component1 = create_tab_bar(tab_options)

    # Handle the tab selection
    selected_make = tab_options[component1]

    # ============================
    # Load Data with Error Handling
    # ============================
    DATE = datetime.now()
    RESULT_FILE = f'Stock Status {DATE.strftime("%d-%m-%Y")}.xlsx'

    if os.path.exists(RESULT_FILE):
        try:
            df_all = load_data(RESULT_FILE)
        except Exception as e:
            st.error(f"⚠️ Error reading the Excel file: {e}")
            st.stop()
    else:
        st.error(f"⚠️ File {RESULT_FILE} does not exist.")
        st.stop()

    # Replace "Yes" and "No" in the "LAMS?" column with check and cross symbols (Optional)
    if 'LAMS?' in df_all.columns:
        df_all['LAMS?'] = df_all['LAMS?'].replace({'Yes': '✔', 'No': '✘'})
    else:
        st.warning("📌 'LAMS?' column not found in the dataset.")

    # Apply filters
    df_filtered = filter_data(df_all, selected_make)

    # Display the filtered DataFrame
    display_dataframe(df_filtered)

    # Footer (Optional)
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #888888;'>© 2024 NAOJOH. All rights reserved.</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

















