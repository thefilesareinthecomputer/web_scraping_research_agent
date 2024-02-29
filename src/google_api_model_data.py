'''

This module concatenates the CSV files and JSON files from the reports folder and saves the combined data to the reports_processed folder. 
It saves the base combined data to restaurant_data_all_combined.csv and restaurant_data_all_combined.json files. 
It also saves the formatted data to restaurant_data_formatted.csv and restaurant_data_trimmed.csv (manageable file size for excel, etc.) for analysis. 

'''

import json
import os 
import pandas as pd
import requests
from math import radians, cos, sin, asin, sqrt
from pandas import json_normalize
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Remove all pandas display limits for the terminal
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 50)
pd.set_option('display.width', 2000)
pd.set_option('display.max_colwidth', 150)  
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_seq_items', None)
pd.set_option('display.precision', 1)

# Define folders
reports_folder = 'reports'
processed_reports_folder = 'reports_processed'
script_directory = os.path.dirname(os.path.abspath(__file__))

# create the processed reports folder if it doesn't exist
if not os.path.exists(processed_reports_folder):
    os.makedirs(processed_reports_folder)
    
# List all files in the reports folder
all_files = os.listdir(reports_folder)
all_csv_files = [file for file in all_files if file.endswith('.csv')]
all_json_files = [file for file in all_files if file.endswith('.json')]

# Print the names of all CSV and JSON files
print(f"\n\nCSV Files:", all_csv_files)
print(f"\n\nJSON Files:", all_json_files)

print(f"\n\n#-------------------------------------------------- COMBINING CSV FILES --------------------------------------------------#\n\n")

# Combine CSV files
combined_csv_files = pd.concat([pd.read_csv(f'{reports_folder}/{file}').assign(source_address_file=file) for file in all_csv_files])
combined_csv_files.to_csv(f'{processed_reports_folder}/restaurant_data_all_combined.csv', index=False)
print('All source csv files combined and saved to restaurant_data_all_combined.csv\n\n')
print(combined_csv_files.info())

print(f"\n\n#-------------------------------------------------- COMBINING CSV FILES --------------------------------------------------#\n\n")

print(f"\n\n#-------------------------------------------------- COMBINING JSON FILES --------------------------------------------------#\n\n")

# Function to fetch coordinates
def fetch_coordinates(address):
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {'address': address, 'key': api_key}
    print(f"Fetching coordinates for {address}...")
    response = requests.get(base_url, params=params).json()

    if response['status'] == 'OK':
        location = response['results'][0]['geometry']['location']
        print(f"Coordinates: {location}")
        return location
    else:
        print(f"Failed to fetch coordinates for {address}.")
        return None

def haversine_distance(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    distance = c * r
    # return distance
    return round(distance, 2)

with open(f'{script_directory}/address_secrets.json', 'r') as file:
    address_dict = json.load(file)

control_points = []
for address in address_dict.values():
    location = fetch_coordinates(address)
    if location:
        control_points.append((location['lat'], location['lng']))

# Function to find the closest control point and calculate the distance
def find_closest_control_point_and_distance(destination):
    closest_distance = None
    for control_point in control_points:
        distance = haversine_distance(control_point, destination)
        if closest_distance is None or distance < closest_distance:
            closest_distance = distance
    print(f"Closest distance to {destination}: {closest_distance} km")
    return closest_distance

# Update the add_crow_fly_distances function
def add_crow_fly_distances(combined_json_data):
    print("Adding crow fly distances...")
    updated_count = 0
    for place_id, details in combined_json_data.items():
        if 'geometry' in details and 'location' in details['geometry'] and 'lat' in details['geometry']['location'] and 'lng' in details['geometry']['location']:
            destination = (details['geometry']['location']['lat'], details['geometry']['location']['lng'])
            print(f"Destination: {destination}")
            closest_distance = find_closest_control_point_and_distance(destination)
            if closest_distance is not None:
                details['crow_fly_distance_km'] = closest_distance
                updated_count += 1
    print(f"Updated crow fly distances for {updated_count} records.")
    # Print the 10 largest distances
    largest_distances = sorted([(place_id, details['crow_fly_distance_km']) for place_id, details in combined_json_data.items() if 'crow_fly_distance_km' in details], key=lambda x: x[1], reverse=True)[:10]
    print(f"10 largest distances: {largest_distances}")

# Initialize the dictionary for combined JSON data
combined_json_data = {}

# Initialize sets for validation checks
original_place_ids = set()
combined_place_ids = set()

# Initialize a counter for fixed records
fixed_records_count = 0
failed_records_count = 0

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

# Ensure all place_ids have valid location data
for place_id, details in combined_json_data.items():
    if 'geometry' not in details or 'location' not in details['geometry'] or 'lat' not in details['geometry']['location'] or 'lng' not in details['geometry']['location']:
        address = details.get('formatted_address', '')
        new_location = fetch_coordinates(address)
        if new_location:
            details.setdefault('geometry', {}).setdefault('location', {}).update(new_location)
            fixed_records_count += 1
        else:
            failed_records_count += 1

# Add crow fly distances
add_crow_fly_distances(combined_json_data)

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

# Print the summary of fixed records
print(f'Summary: Updated location data for {fixed_records_count} records.')
print(f'Summary: Failed to gather location data for {failed_records_count} records.')

print('All source JSON files combined and saved to restaurant_data_all_combined.json')

def explore_structure(obj, path=''):
    if isinstance(obj, dict):
        for key in obj.keys():
            new_path = f"{path}.{key}" if path else key
            # Split the new_path by the first dot and take the part after it, if any
            field_name = new_path.split('.', 1)[-1] if '.' in new_path else new_path
            fields.add(field_name)  # Add the field name after the first dot
            explore_structure(obj[key], new_path)  # Explore nested structures
    elif isinstance(obj, list) and obj:  # Ensure the list is not empty
        explore_structure(obj[0], path)  # Explore the first item structure
            
# Load the JSON data
with open(os.path.join(processed_reports_folder, 'restaurant_data_all_combined.json'), 'r') as f:
    data = json.load(f)

# Set to store unique field names
fields = set()

# Explore the structure of the JSON data
explore_structure(data)

# Print all unique field names after the first dot
print("Fields structure:")
for field in sorted(fields):
    print(field)

'''
# FIELDS:

place_id  # MAIN IDENTIFIER / MASTER KEY FOR THE ARRAY OF OBJECTS

# ALL OTHER FIELDS ARE NESTED UNDER THE place_id KEY

address_components
address_components.long_name                                                # DROP
address_components.short_name                                               # DROP
address_components.types                                                        # DROP
business_status
crow_fly_distance_km
curbside_pickup                                                                 # DROP
delivery                                                                            # DROP
dine_in
editorial_summary
editorial_summary.language                                                          # DROP
editorial_summary.overview
formatted_address
formatted_phone_number                                                          # DROP
geometry
geometry.location
geometry.location.lat
geometry.location.lng
geometry.viewport                                                                   # DROP
geometry.viewport.northeast                                                         # DROP
geometry.viewport.northeast.lat                                             # DROP
geometry.viewport.northeast.lng                                                         # DROP
geometry.viewport.southwest                                                         # DROP
geometry.viewport.southwest.lat                                             # DROP
geometry.viewport.southwest.lng                                             # DROP
icon                                                                            # DROP
international_phone_number
last_updated
name
opening_hours
opening_hours.open_now                                                          # DROP
opening_hours.periods                                                       # DROP
opening_hours.periods.close                                                         # DROP
opening_hours.periods.close.day                                                         # DROP
opening_hours.periods.close.time                                                        # DROP
opening_hours.periods.open                                                          # DROP
opening_hours.periods.open.day                                              # DROP
opening_hours.periods.open.time                                             # DROP
opening_hours.weekday_text
plus_code                                                                   # DROP
plus_code.compound_code                                                         # DROP
plus_code.global_code                                                       # DROP
price_level
rating
reservable
reviews
reviews.author_name                                                         # DROP
reviews.author_url                                                          # DROP
reviews.language                                                                    # DROP
reviews.original_language                                                       # DROP
reviews.profile_photo_url                                                       # DROP
reviews.rating
reviews.relative_time_description                                                  # DROP
reviews.text
reviews.time                                                                    # DROP
reviews.translated                                                                  # DROP
serves_beer                                                                             # DROP
serves_breakfast
serves_brunch
serves_dinner
serves_lunch
serves_vegetarian_food                                                                  # DROP
serves_wine
source_address_file                                                                 # DROP
takeout                                                                             # DROP
types
url
user_ratings_total
utc_offset
vicinity                                                                            # DROP
website
wheelchair_accessible_entrance                                                          # DROP
'''

print(f"\n\n#-------------------------------------------------- COMBINING JSON FILES --------------------------------------------------#\n\n")

print(f"\n\n#-------------------------------------------------- FORMATTING JSON FOR MAP --------------------------------------------------#\n\n")

def format_for_map(obj):
    if not isinstance(obj, dict):  # Check if the object is a dictionary
        return None  # Skip this object if it's not a dictionary

    # Proceed with formatting if obj is a dictionary
    formatted_data = {
        "name": obj.get("name"),
        "types": ", ".join(obj.get("types", [])),
        "summary": obj.get("editorial_summary", {}).get("overview", ""),
        "website": obj.get("website"),
        "url": obj.get("url"),
        "price_level": obj.get("price_level"),
        "rating_average": obj.get("rating"),
        "ratings_total": obj.get("user_ratings_total"),
        "reviews_text": [review.get("text") for review in obj.get("reviews", []) if isinstance(review, dict)],
        "direct_distance_km": obj.get("crow_fly_distance_km"),
        "address": obj.get("formatted_address"),
        "opening_hours_weekday_text": "\n".join(obj.get("opening_hours", {}).get("weekday_text", [])),
        "time_zone_utc_offset": obj.get("utc_offset"),
        "business_status": obj.get("business_status"),
        "dine_in": obj.get("dine_in"),
        "reservable": obj.get("reservable"),
        "serves_breakfast": obj.get("serves_breakfast"),
        "serves_brunch": obj.get("serves_brunch"),
        "serves_lunch": obj.get("serves_lunch"),
        "serves_dinner": obj.get("serves_dinner"),
        "serves_wine": obj.get("serves_wine"),
        "last_updated": obj.get("last_updated"),
        "geometry": obj.get("geometry", {}).get("location", {}),
    }
    return formatted_data

# Dictionary to hold all formatted data with place_id as keys
formatted_data_dict = {}

# Iterate through each place's data in the JSON dictionary
for place_id, place_data in data.items():
    if isinstance(place_data, dict):
        formatted_obj = format_for_map(place_data)
        if formatted_obj:
            formatted_data_dict[place_id] = formatted_obj  # Use place_id as the key
    else:
        print(f"Warning: Data for place_id {place_id} is not a dictionary.")

# Save the formatted data to a new JSON file
output_filename = os.path.join(processed_reports_folder, 'restaurant_data_map_file.json')
with open(output_filename, 'w') as outfile:
    json.dump(formatted_data_dict, outfile, indent=4)

print(f"Data successfully saved to {output_filename}")

print(f"\n\n#-------------------------------------------------- FORMATTING JSON FOR MAP --------------------------------------------------#\n\n")





































































# print(f"\n\n#-------------------------------------------------- MAIN VISUALIZATION CSV --------------------------------------------------#\n\n")

# # load the saved restaurant_data_all_combined.json file
# with open(f'{processed_reports_folder}/restaurant_data_all_combined.json', 'r') as f:
#     combined_json_data = json.load(f)
    
# # Convert the combined JSON data to a DataFrame and use the unique keys as the index
# combined_json_data_df = pd.DataFrame.from_dict(combined_json_data, orient='index')

# # Function to flatten and join a specific nested column
# def flatten_column(dataframe, column_name):
#     # Create a temporary DataFrame from the column to be flattened
#     temp_df = pd.json_normalize(dataframe[column_name].dropna().tolist())
#     temp_df.index = dataframe[column_name].dropna().index
    
#     # Generate new column names to avoid conflicts
#     temp_df.columns = [f"{column_name}_{subcolumn}" for subcolumn in temp_df.columns]
    
#     # Drop the original nested column and join the flattened data
#     dataframe = dataframe.drop(column_name, axis=1)
#     dataframe = dataframe.join(temp_df)
#     return dataframe

# def reformat_weekday_text(df, column_name='opening_hours_weekday_text'):
#     if column_name in df.columns:
#         # Join the list of strings into a single string with a semicolon and space as separators
#         df[column_name] = df[column_name].apply(lambda x: f'; \n'.join(x) if isinstance(x, list) else x)
#     return df

# def reformat_types(df, column_name='types'):
#     if column_name in df.columns:
#         # Join the list of strings into a single string with a semicolon and space as separators
#         df[column_name] = df[column_name].apply(lambda x: f', '.join(x) if isinstance(x, list) else x)
#     return df

# '''
# # the function below is essentially the same thing as above but more generalized, should be able to be applied to all columns if needed, but it hasn't beemn thoroughly tested yet

# def reformat_list_to_string(df, column_name, separator='; '):
#     if column_name in df.columns:
#         # Define a lambda function to handle various cases: list, None, NaN, etc.
#         join_func = lambda x: separator.join(x) if isinstance(x, list) else x
        
#         # Apply the function to the column
#         df[column_name] = df[column_name].apply(join_func)
#     return df

# # Apply the reformatting function to both 'opening_hours_weekday_text' and 'types' columns
# combined_json_data_df = reformat_list_to_string(combined_json_data_df, 'opening_hours_weekday_text')
# combined_json_data_df = reformat_list_to_string(combined_json_data_df, 'types')
# '''

# print("\n\n#---------- FLATTENED DATAFRAME ----------#\n\n")

# # List of nested columns to flatten
# nested_columns = ['geometry', 'opening_hours', 'reviews', 'plus_code', 'editorial_summary']

# # Flatten each nested column
# for column in nested_columns:
#     combined_json_data_df = flatten_column(combined_json_data_df, column)
    
# deep_nested_columns = []

# # Flatten each nested column
# for column in deep_nested_columns:
#     combined_json_data_df = flatten_column(combined_json_data_df, column)
    
# # Preview the DataFrame
# print(combined_json_data_df.info())

# print("\n\n#---------- CLEANED DATAFRAME ----------#\n\n")

# # Apply the reformatting function to your DataFrame
# combined_json_data_df = reformat_weekday_text(combined_json_data_df)
# combined_json_data_df = reformat_types(combined_json_data_df)

# # Clean and format the DataFrame more as needed, e.g., convert data types, handle missing values, etc.

# # Preview the DataFrame
# print(combined_json_data_df.info())

# # Export the cleaned and formatted DataFrame to a CSV file
# csv_filename = f'{processed_reports_folder}/restaurant_data_formatted.csv'
# combined_json_data_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # 'utf-8-sig' is often a good choice for Excel compatibility

# print(f'Data exported to {csv_filename} successfully.')

# trimmed_df = combined_json_data_df.copy()

# # 'address_components_0', 'address_components_1', 'address_components_2', 'address_components_3', 'address_components_4', 'address_components_5', 'address_components_6', 'address_components_7', 'address_components_8', 'address_components_9', 'address_components_10', 'address_components_11', 
# columns_to_drop = ['business_status', 'icon', 'formatted_phone_number', 'place_id', 'utc_offset', 'curbside_pickup', 'takeout', 'delivery', 'geometry_viewport.northeast.lat', 'geometry_viewport.northeast.lng', 'geometry_viewport.southwest.lat', 'geometry_viewport.southwest.lng', 'opening_hours_open_now', 'opening_hours_periods', 'plus_code_compound_code', 'plus_code_global_code', 'vicinity', 'reviews_0', 'reviews_1', 'reviews_2', 'reviews_3', 'reviews_4', 'editorial_summary_language']

# # drop the listed columns from the dataframe
# trimmed_df = trimmed_df.drop(columns=columns_to_drop)

# # drop all columns where price_level == 1
# trimmed_df = trimmed_df[trimmed_df['price_level'] != 1]

# priority_column_sort_order = ['name', 'editorial_summary_overview', 'price_level', 'rating', 'user_ratings_total', 'crow_fly_distance_km', 'formatted_address', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ]

# print(trimmed_df.head())
# print(trimmed_df.info())

# # # save the trimmed data to a new CSV file
# # trimmed_csv_filename = f'{processed_reports_folder}/restaurant_data_trimmed_tuesday.csv'
# # trimmed_df.to_csv(trimmed_csv_filename, index=False, encoding='utf-8-sig')  # 'utf-8-sig' is often a good choice for Excel compatibility
# # print(f'Trimmed data exported to {trimmed_csv_filename} successfully.')

# print(f"\n\n#-------------------------------------------------- MAIN VISUALIZATION CSV --------------------------------------------------#\n\n")

# # take a random sample of 100 rows from the dataframe
# trimmed_df_sample = trimmed_df.sample(n=100, random_state=1)

# # save the trimmed data to a new CSV file
# trimmed_csv_sample_filename = f'{processed_reports_folder}/restaurant_data_trimmed_sample.csv'
# trimmed_df_sample.to_csv(trimmed_csv_sample_filename, index=False, encoding='utf-8-sig')  # 'utf-8-sig' is often a good choice for Excel compatibility














































































# print(f"\n\n#-------------------------------------------------- TRIMMED DASHBOARD CSV --------------------------------------------------#\n\n")

# # load the restaurant_data_all_combined.json file
# with open(f'{processed_reports_folder}/restaurant_data_all_combined.json', 'r') as f:
#     combined_json_data = json.load(f)
    
# # Convert the combined JSON data to a DataFrame and use the unique keys as the index
# combined_json_data_df = pd.DataFrame.from_dict(combined_json_data, orient='index')

# # Function to flatten and join a specific nested column
# def flatten_column(dataframe, column_name):
#     # Create a temporary DataFrame from the column to be flattened
#     temp_df = pd.json_normalize(dataframe[column_name].dropna().tolist())
#     temp_df.index = dataframe[column_name].dropna().index
    
#     # Generate new column names to avoid conflicts
#     temp_df.columns = [f"{column_name}_{subcolumn}" for subcolumn in temp_df.columns]
    
#     # Drop the original nested column and join the flattened data
#     dataframe = dataframe.drop(column_name, axis=1)
#     dataframe = dataframe.join(temp_df)
#     return dataframe

# # List of nested columns to flatten
# nested_columns = ['address_components', 'geometry', 'opening_hours', 'reviews', 'plus_code']

# # Flatten each nested column
# for column in nested_columns:
#     combined_json_data_df = flatten_column(combined_json_data_df, column)

# # Clean and format the DataFrame as needed, e.g., convert data types, handle missing values, etc.

# # Preview the DataFrame
# print(combined_json_data_df.head())
# print(combined_json_data_df.info())

# # Export the cleaned and formatted DataFrame to a CSV file
# csv_filename = f'{processed_reports_folder}/restaurant_data_formatted.csv'
# combined_json_data_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # 'utf-8-sig' is often a good choice for Excel compatibility

# print(f'Data exported to {csv_filename} successfully.')

# trimmed_df = combined_json_data_df.copy()

# columns_to_drop = ['business_status', 'icon', 'formatted_phone_number', 'place_id', 'utc_offset', 'curbside_pickup', 'takeout', 'delivery', 'address_components_0', 'address_components_1', 'address_components_2', 'address_components_3', 'address_components_4', 'address_components_5', 'address_components_6', 'address_components_7', 'address_components_8', 'address_components_9', 'address_components_10', 'address_components_11', 'geometry_viewport.northeast.lat', 'geometry_viewport.northeast.lng', 'geometry_viewport.southwest.lat', 'geometry_viewport.southwest.lng', 'opening_hours_open_now', 'opening_hours_periods', 'plus_code_compound_code', 'plus_code_global_code', 'vicinity', 'reviews_0', 'reviews_1', 'reviews_2', 'reviews_3', 'reviews_4']

# # drop the columns
# trimmed_df = trimmed_df.drop(columns=columns_to_drop)

# # drop all columns where price_level == 1
# trimmed_df = trimmed_df[trimmed_df['price_level'] != 1]

# print(trimmed_df.head())
# print(trimmed_df.info())

# # save the trimmed data to a new CSV file
# trimmed_csv_filename = f'{processed_reports_folder}/restaurant_data_trimmed.csv'
# trimmed_df.to_csv(trimmed_csv_filename, index=False, encoding='utf-8-sig')  # 'utf-8-sig' is often a good choice for Excel compatibility

# print(f'Trimmed data exported to {trimmed_csv_filename} successfully.')

# print(f"\n\n#-------------------------------------------------- TRIMMED DASHBOARD CSV --------------------------------------------------#\n\n")

# print(f"\n\n#-------------------------------------------------- MAIN VISUALIZATION CSV --------------------------------------------------#\n\n")

# # load the saved restaurant_data_all_combined.json file
# with open(f'{processed_reports_folder}/restaurant_data_all_combined.json', 'r') as f:
#     combined_json_data = json.load(f)
    
# # Convert the combined JSON data to a DataFrame and use the unique keys as the index
# combined_json_data_df = pd.DataFrame.from_dict(combined_json_data, orient='index')

# # Function to flatten and join a specific nested column
# def flatten_column(dataframe, column_name):
#     # Create a temporary DataFrame from the column to be flattened
#     temp_df = pd.json_normalize(dataframe[column_name].dropna().tolist())
#     temp_df.index = dataframe[column_name].dropna().index
    
#     # Generate new column names to avoid conflicts
#     temp_df.columns = [f"{column_name}_{subcolumn}" for subcolumn in temp_df.columns]
    
#     # Drop the original nested column and join the flattened data
#     dataframe = dataframe.drop(column_name, axis=1)
#     dataframe = dataframe.join(temp_df)
#     return dataframe

# # Function to clean and re-format 'opening_hours_weekday_text' column
# def clean_weekday_text(dataframe, column_name):
#     # Check if the column exists in the DataFrame
#     if column_name in dataframe.columns:
#         # Reformat each entry in the column
#         dataframe[column_name] = dataframe[column_name].apply(lambda x: "\n".join([day.replace('\u2009', ' ').replace('\u202f', ' ') for day in x]) if isinstance(x, list) else x)
#     return dataframe

# print("\n\n#---------- FLATTENED DATAFRAME ----------#\n\n")

# # List of nested columns to flatten
# nested_columns = ['address_components', 'geometry', 'opening_hours', 'reviews', 'plus_code']

# # Flatten each nested column
# for column in nested_columns:
#     combined_json_data_df = flatten_column(combined_json_data_df, column)

# # Preview the DataFrame
# print(combined_json_data_df.info())

# print("\n\n#---------- CLEANED DATAFRAME ----------#\n\n")

# # # Clean and re-format the 'opening_hours_weekday_text' column after flattening
# # combined_json_data_df = clean_weekday_text(combined_json_data_df, 'opening_hours_weekday_text')

# def reformat_weekday_text(df, column_name='opening_hours_weekday_text'):
#     if column_name in df.columns:
#         # Join the list of strings into a single string with a semicolon and space as separators
#         df[column_name] = df[column_name].apply(lambda x: f'; \n'.join(x) if isinstance(x, list) else x)
#     return df

# def reformat_types(df, column_name='types'):
#     if column_name in df.columns:
#         # Join the list of strings into a single string with a semicolon and space as separators
#         df[column_name] = df[column_name].apply(lambda x: f'; \n'.join(x) if isinstance(x, list) else x)
#     return df

# # Apply the reformatting function to your DataFrame
# combined_json_data_df = reformat_weekday_text(combined_json_data_df)
# combined_json_data_df = reformat_types(combined_json_data_df)

# '''
# # the function below is essentially the same thing as above but more generalized, should be able to be applied to all columns if needed, but it hasn't beemn thoroughly tested yet

# def reformat_list_to_string(df, column_name, separator='; '):
#     if column_name in df.columns:
#         # Define a lambda function to handle various cases: list, None, NaN, etc.
#         join_func = lambda x: separator.join(x) if isinstance(x, list) else x
        
#         # Apply the function to the column
#         df[column_name] = df[column_name].apply(join_func)
#     return df

# # Apply the reformatting function to both 'opening_hours_weekday_text' and 'types' columns
# combined_json_data_df = reformat_list_to_string(combined_json_data_df, 'opening_hours_weekday_text')
# combined_json_data_df = reformat_list_to_string(combined_json_data_df, 'types')



# '''
# # Clean and format the DataFrame as needed, e.g., convert data types, handle missing values, etc.

# # Preview the DataFrame
# print(combined_json_data_df.info())

# # Export the cleaned and formatted DataFrame to a CSV file
# csv_filename = f'{processed_reports_folder}/restaurant_data_formatted.csv'
# combined_json_data_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # 'utf-8-sig' is often a good choice for Excel compatibility

# print(f'Data exported to {csv_filename} successfully.')

# trimmed_df = combined_json_data_df.copy()

# columns_to_drop = ['business_status', 'icon', 'formatted_phone_number', 'place_id', 'utc_offset', 'curbside_pickup', 'takeout', 'delivery', 'address_components_0', 'address_components_1', 'address_components_2', 'address_components_3', 'address_components_4', 'address_components_5', 'address_components_6', 'address_components_7', 'address_components_8', 'address_components_9', 'address_components_10', 'address_components_11', 'geometry_viewport.northeast.lat', 'geometry_viewport.northeast.lng', 'geometry_viewport.southwest.lat', 'geometry_viewport.southwest.lng', 'opening_hours_open_now', 'opening_hours_periods', 'plus_code_compound_code', 'plus_code_global_code', 'vicinity', 'reviews_0', 'reviews_1', 'reviews_2', 'reviews_3', 'reviews_4']

# # drop the columns
# trimmed_df = trimmed_df.drop(columns=columns_to_drop)

# # drop all columns where price_level == 1
# trimmed_df = trimmed_df[trimmed_df['price_level'] != 1]

# print(trimmed_df.head())
# print(trimmed_df.info())

# # save the trimmed data to a new CSV file
# trimmed_csv_filename = f'{processed_reports_folder}/restaurant_data_trimmed.csv'
# trimmed_df.to_csv(trimmed_csv_filename, index=False, encoding='utf-8-sig')  # 'utf-8-sig' is often a good choice for Excel compatibility

# print(f'Trimmed data exported to {trimmed_csv_filename} successfully.')

# print(f"\n\n#-------------------------------------------------- MAIN VISUALIZATION CSV --------------------------------------------------#\n\n")