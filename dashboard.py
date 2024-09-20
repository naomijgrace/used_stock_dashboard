# -*- coding: utf-8 -*-
#cd C:\Users\naojoh\Desktop\projects_v3\PROJECT_BETA
#python -m streamlit run dashboard.py
"""
Created on Fri Sep 20 10:14:55 2024

@author: NAOJOH

"""
import streamlit as st
import pandas as pd
from datetime import datetime

# Set the page configuration to use wide mode
st.set_page_config(layout="wide")

# Load your cleaned data from the Excel file
DATE = datetime.now()
RESULT_FILE = f'Stock Status {DATE.strftime("%d-%m-%Y")}.xlsx'
df_all = pd.read_excel(RESULT_FILE)

# Replace NaN values with empty strings
df_all = df_all.fillna('')

# Replace "Yes" and "No" in the "LAMS?" column with check and cross symbols
df_all['LAMS?'] = df_all['LAMS?'].replace({'Yes': '✔', 'No': '✘'})

# Remove the 'Rego Certificate' column from the DataFrame
df_all = df_all.drop(columns=['Rego Certificate'])

# Create a new 'Rego Details' column with buttons where values are separated by semicolons
def create_rego_buttons(details):
    if details:
        buttons = []
        for detail in details.split('; '):  # Separate values by semicolon
            if detail == 'Rego expired':
                buttons.append(f'<button disabled style="background-color:lightcoral; border:none; border-radius:10px; padding:2px 8px;">{detail}</button>')
            elif detail == 'Rego expires soon':
                buttons.append(f'<button disabled style="background-color:lightyellow; border:none; border-radius:10px; padding:2px 8px;">{detail}</button>')
            else:
                buttons.append(f'<button disabled style="background-color:lightgray; border:none; border-radius:10px; padding:2px 8px;">{detail}</button>')
        return ' '.join(buttons)
    else:
        return ''

df_all['Rego Details'] = [create_rego_buttons(row['Rego Details']) for idx, row in df_all.iterrows()]

# Set the title for the app
st.title("Used Stock Dashboard")

# Add the 'Last Updated' subheading below the main title
st.subheader(f"Last Updated: {DATE.strftime('%d-%m-%Y')}")

# Sidebar filters for columns
with st.sidebar:
    st.header("Filter Options")
    
    # Replace dropdown with radio buttons for 'Make'
    make_filter = st.radio('Select Make:', options=['ALL', 'BMW', 'KAW', 'KTM'], horizontal=True)
    
    # LAMS Approved Toggle
    lams_filter = st.checkbox('Show LAMS Approved Only')

# Apply Make filter based on the selection
if make_filter == 'BMW':
    df_filtered = df_all[df_all['Make'].str.contains('BMW', case=False, na=False)]
elif make_filter == 'KAW':
    df_filtered = df_all[df_all['Make'].str.contains('KAW', case=False, na=False)]
elif make_filter == 'KTM':
    df_filtered = df_all[df_all['Make'].str.contains('KTM', case=False, na=False)]
else:
    df_filtered = df_all

# Filter for LAMS Approved if the toggle is selected
if lams_filter:
    df_filtered = df_filtered[df_filtered['LAMS?'] == '✔']

# Convert the DataFrame to HTML for rendering buttons in the 'Rego Details' column, hiding the index, and centering LAMS values
html_table = df_filtered.to_html(escape=False, index=False)

# Apply custom CSS to center the LAMS? column values and improve button appearance
custom_css = """
    <style>
        table {
            width: 100%;
        }
        th, td {
            text-align: center;
        }
        td:nth-child(3) {  /* Adjust nth-child value based on the position of the LAMS? column */
            text-align: center !important;
        }
    </style>
"""

# Render the table with custom CSS, without the table title
st.write(custom_css + html_table, unsafe_allow_html=True)
















