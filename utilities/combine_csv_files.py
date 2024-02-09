import pandas as pd
import os 
from dotenv import load_dotenv

# load all csv files from the reports folder dynamically in a loop
reports_folder = 'reports'
processed_reports_folder = 'reports_processed'
all_files = os.listdir(reports_folder)
all_csv_files = [file for file in all_files if file.endswith('.csv')]

# create the processed reports folder if ti doesn't exist
if not os.path.exists(processed_reports_folder):
    os.makedirs(processed_reports_folder)

# print the name of all cav files in the all_csv_files list
print(all_csv_files)

# combine them all into one file, add a new column called source_address_file, fill that column with each row's respective source file name, and save it to a new file called restaurant_data_all_combined.csv and save it to the processed reports folder
combined_data = pd.concat([pd.read_csv(f'{reports_folder}/{file}').assign(source_address_file=file) for file in all_csv_files])
combined_data.to_csv(f'{processed_reports_folder}/restaurant_data_all_combined.csv', index=False)
print('All files combined and saved to restaurant_data_all_combined.csv\n\n')
print(combined_data.head())
print(combined_data.tail())
print(combined_data.info())