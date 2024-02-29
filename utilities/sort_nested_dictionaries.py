import json
from collections import OrderedDict

# Your original dictionaries
data = {
    "restaurantDataSources": {
        "yelp": "https://www.yelp.com/",
        "opentable": "https://www.opentable.com/",
        "resy": "https://resy.com/",
        # Add the rest of your restaurant data sources...
    },
    "generalDataSources": {
        "datagov": "https://data.gov/",
        "census": "https://www.census.gov/",
        # Add the rest of your general data sources...
    }
}

# Function to sort dictionaries
def sort_dict(d):
    return OrderedDict(sorted(d.items()))

# Sorting the dictionaries
sorted_data = {key: sort_dict(value) for key, value in data.items()}

# Convert the sorted dictionary to a JSON string for pretty printing
sorted_json = json.dumps(sorted_data, indent=4)

# Print the sorted JSON string
print(sorted_json)

# Optionally, you can write the sorted JSON to a file
with open('sorted_data_sources.json', 'w') as f:
    f.write(sorted_json)
