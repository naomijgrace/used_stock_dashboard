import pandas as pd

# Load the dataset
file_path = 'autogate_data.xlsx'
data = pd.read_excel(file_path, header=0)

# Function to handle appending invalid rows based on the presence of '|' in the first column
def append_invalid_rows_with_pipe(valid_row, invalid_rows):
    for i, invalid_row in enumerate(invalid_rows):
        if '|' in str(invalid_row.iloc[0]):  # Check if the first column contains '|'
            for j, val in enumerate(invalid_row[:3]):  # Process up to 3 columns from each invalid row
                if pd.notna(val):  # Only consider non-NaN values
                    valid_row["Details"] = val
    return valid_row

# Re-initialize the cleaned data process
cleaned_data = []
current_row = None
invalid_rows = []

# Iterate through each row of the dataset
for idx, row in data.iterrows():
    # If the row has multiple columns with values, it's a new valid row
    if pd.notna(row.iloc[1:]).any():
        # Process any collected invalid rows that contain '|'
        if current_row is not None:
            if invalid_rows:
                current_row = append_invalid_rows_with_pipe(current_row, invalid_rows)
                invalid_rows = []
            cleaned_data.append(current_row)
        current_row = row.copy()
    # If the row only has the first column with a value, store it for later checking
    else:
        invalid_rows.append(row.copy())

# Process the last valid row and any associated invalid rows
if current_row is not None:
    if invalid_rows:
        current_row = append_invalid_rows_with_pipe(current_row, invalid_rows)
    cleaned_data.append(current_row)

# Create a new DataFrame from the cleaned data
cleaned_df = pd.DataFrame(cleaned_data)

# Optionally, save the cleaned DataFrame to a new Excel file
cleaned_df.to_excel('cleaned_autogate_data_with_pipe.xlsx', index=False)


