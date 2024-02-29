from collections import OrderedDict
import json




dictionary = {
        "datagov": "https://data.gov/",
        "census": "https://www.census.gov/",
        "eurostat": "https://ec.europa.eu/eurostat",
        "worldbank": "https://data.worldbank.org/",
        "oecd": "https://data.oecd.org/",
        "unData": "http://data.un.org/",
        "nomis": "https://www.nomisweb.co.uk/",
        "openweathermap": "https://openweathermap.org/api",
        "quandl": "https://www.quandl.com/",
        "tradingeconomics": "https://tradingeconomics.com/",
        "politico": "https://www.politico.com/",
        "financialtimes": "https://www.ft.com/",
        "bloomberg": "https://www.bloomberg.com/",
        "reuters": "https://www.reuters.com/",
        "geonames": "http://www.geonames.org/",
        "openstreetmap": "https://www.openstreetmap.org/",
        "geofabrik": "http://www.geofabrik.de/",
        "openflights": "https://openflights.org/data.html",
        "enjoytravel": "https://www.enjoytravel.com/"
    }

def sort_dict_by_keys(d):
    # Sort the dictionary by its keys and use OrderedDict to maintain the order
    return OrderedDict(sorted(d.items()))

# def print_formatted_sorted_dict(d):
#     # Print each key-value pair on a new line
#     for key, value in d.items():
#         print(f"{key}: {value}")

# sorted_dict = sort_dict_by_keys(dictionary)
# print_formatted_sorted_dict(sorted_dict)

sorted_dict = sort_dict_by_keys(dictionary)
print(json.dumps(sorted_dict, indent=4))
