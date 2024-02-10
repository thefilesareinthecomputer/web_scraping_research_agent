'''

This module concatenates the CSV files and JSON files from the reports folder and saves the combined data to the reports_processed folder. 
It saves the base combined data to restaurant_data_all_combined.csv and restaurant_data_all_combined.json files. 
It also saves the formatted data to restaurant_data_formatted.csv and restaurant_data_trimmed.csv (manageable file size for excel, etc.) for analysis. 

'''

import json
import os 
import pandas as pd
from pandas import json_normalize
from dotenv import load_dotenv

# Define folders
reports_folder = 'reports'
processed_reports_folder = 'reports_processed'

# List all files in the reports folder
all_files = os.listdir(reports_folder)
all_csv_files = [file for file in all_files if file.endswith('.csv')]
all_json_files = [file for file in all_files if file.endswith('.json')]

# create the processed reports folder if it doesn't exist
if not os.path.exists(processed_reports_folder):
    os.makedirs(processed_reports_folder)

# Print the names of all CSV and JSON files
print(f"\n\nCSV Files:", all_csv_files)
print(f"\n\nJSON Files:", all_json_files)

print(f"\n\n#-------------------------------------------------- COMBINING CSV FILES --------------------------------------------------#\n\n")

# Combine CSV files
combined_csv_files = pd.concat([pd.read_csv(f'{reports_folder}/{file}').assign(source_address_file=file) for file in all_csv_files])
combined_csv_files.to_csv(f'{processed_reports_folder}/restaurant_data_all_combined.csv', index=False)
print('All files combined and saved to restaurant_data_all_combined.csv\n\n')
print(combined_csv_files.head())
print(combined_csv_files.tail())
print(combined_csv_files.info())

print(f"\n\n#-------------------------------------------------- COMBINING CSV FILES --------------------------------------------------#\n\n")

print(f"\n\n#-------------------------------------------------- COMBINING JSON FILES --------------------------------------------------#\n\n")

# Initialize the dictionary for combined JSON data
combined_json_data = {}

# Initialize sets for validation checks
original_place_ids = set()
combined_place_ids = set()

# Process each JSON file
for file in all_json_files:
    with open(os.path.join(reports_folder, file), 'r') as f:
        data = json.load(f)  # Assuming data is a dictionary

        # Update the set of original place IDs
        original_place_ids.update(data.keys())

        # Combine data and update combined_place_ids set
        for place_id, details in data.items():
            if isinstance(details, dict):
                details['source_address_file'] = file  # Add source file info
                combined_json_data[place_id] = details  # Combine data
                combined_place_ids.add(place_id)  # Update combined_place_ids set
            else:
                print(f"Warning: Expected a dictionary for place ID {place_id}, got {type(details)} in file {file}")

# Save the combined JSON data
with open(os.path.join(processed_reports_folder, 'restaurant_data_all_combined.json'), 'w') as f:
    json.dump(combined_json_data, f, indent=4)

# Perform new validation checks using sets
missing_ids = original_place_ids - combined_place_ids
extra_ids = combined_place_ids - original_place_ids

if missing_ids or extra_ids:
    print(f'Warning: Discrepancies found. Missing IDs: {len(missing_ids)}, Extra IDs: {len(extra_ids)}')
else:
    print(f'Success: All records matched. Total unique records: {len(combined_place_ids)}')

print('JSON files combined and saved to restaurant_data_all_combined.json')

print(f"\n\n#-------------------------------------------------- COMBINING JSON FILES --------------------------------------------------#\n\n")

print(f"\n\n#-------------------------------------------------- TRIMMED DASHBOARD CSV --------------------------------------------------#\n\n")

# load the restaurant_data_all_combined.json file
with open(f'{processed_reports_folder}/restaurant_data_all_combined.json', 'r') as f:
    combined_json_data = json.load(f)
    
# Convert the combined JSON data to a DataFrame and use the unique keys as the index
combined_json_data_df = pd.DataFrame.from_dict(combined_json_data, orient='index')

# Function to flatten and join a specific nested column
def flatten_column(dataframe, column_name):
    # Create a temporary DataFrame from the column to be flattened
    temp_df = pd.json_normalize(dataframe[column_name].dropna().tolist())
    temp_df.index = dataframe[column_name].dropna().index
    
    # Generate new column names to avoid conflicts
    temp_df.columns = [f"{column_name}_{subcolumn}" for subcolumn in temp_df.columns]
    
    # Drop the original nested column and join the flattened data
    dataframe = dataframe.drop(column_name, axis=1)
    dataframe = dataframe.join(temp_df)
    return dataframe

# List of nested columns to flatten
nested_columns = ['address_components', 'geometry', 'opening_hours', 'reviews', 'plus_code']

# Flatten each nested column
for column in nested_columns:
    combined_json_data_df = flatten_column(combined_json_data_df, column)

# Clean and format the DataFrame as needed, e.g., convert data types, handle missing values, etc.

# Remove all pandas display limits for the terminal
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)  # Changed from 50 to None for full visibility
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_seq_items', None)
pd.set_option('display.precision', 2)

# Preview the DataFrame
print(combined_json_data_df.head())
print(combined_json_data_df.info())

# Export the cleaned and formatted DataFrame to a CSV file
csv_filename = f'{processed_reports_folder}/restaurant_data_formatted.csv'
combined_json_data_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # 'utf-8-sig' is often a good choice for Excel compatibility

print(f'Data exported to {csv_filename} successfully.')

trimmed_df = combined_json_data_df.copy()

columns_to_drop = ['business_status', 'icon', 'formatted_phone_number', 'place_id', 'utc_offset', 'curbside_pickup', 'takeout', 'delivery', 'address_components_0', 'address_components_1', 'address_components_2', 'address_components_3', 'address_components_4', 'address_components_5', 'address_components_6', 'address_components_7', 'address_components_8', 'address_components_9', 'address_components_10', 'address_components_11', 'geometry_viewport.northeast.lat', 'geometry_viewport.northeast.lng', 'geometry_viewport.southwest.lat', 'geometry_viewport.southwest.lng', 'opening_hours_open_now', 'opening_hours_periods', 'plus_code_compound_code', 'plus_code_global_code', 'vicinity', 'reviews_0', 'reviews_1', 'reviews_2', 'reviews_3', 'reviews_4']

# drop the columns
trimmed_df = trimmed_df.drop(columns=columns_to_drop)

# drop all columns where price_level == 1
trimmed_df = trimmed_df[trimmed_df['price_level'] != 1]

print(trimmed_df.head())
print(trimmed_df.info())

# save the trimmed data to a new CSV file
trimmed_csv_filename = f'{processed_reports_folder}/restaurant_data_trimmed.csv'
trimmed_df.to_csv(trimmed_csv_filename, index=False, encoding='utf-8-sig')  # 'utf-8-sig' is often a good choice for Excel compatibility

print(f'Trimmed data exported to {trimmed_csv_filename} successfully.')

print(f"\n\n#-------------------------------------------------- TRIMMED DASHBOARD CSV --------------------------------------------------#\n\n")