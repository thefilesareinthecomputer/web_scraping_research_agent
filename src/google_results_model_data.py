import json
import os 
import pandas as pd
from dotenv import load_dotenv

# Define folders
reports_folder = 'reports'
processed_reports_folder = 'reports_processed'

# List all files in the reports folder
all_files = os.listdir(reports_folder)
all_csv_files = [file for file in all_files if file.endswith('.csv')]
all_json_files = [file for file in all_files if file.endswith('.json')]

# create the processed reports folder if ti doesn't exist
if not os.path.exists(processed_reports_folder):
    os.makedirs(processed_reports_folder)

# Print the names of all CSV and JSON files
print("CSV Files:", all_csv_files)
print("JSON Files:", all_json_files)

# Combine CSV files
combined_csv_files = pd.concat([pd.read_csv(f'{reports_folder}/{file}').assign(source_address_file=file) for file in all_csv_files])
combined_csv_files.to_csv(f'{processed_reports_folder}/restaurant_data_all_combined.csv', index=False)
print('All files combined and saved to restaurant_data_all_combined.csv\n\n')
print(combined_csv_files.head())
print(combined_csv_files.tail())
print(combined_csv_files.info())

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

