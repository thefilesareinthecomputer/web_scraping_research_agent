'''

# APP

There is new code around line 550 - monitor that on the next run

```
## App description: 

a search automation, analysis, and visualization tool designed to create a comprehensive report about all relevant restaurant, business, economic, and weather data about a 
predefined set of addresses. 
the application pulls in data from nultiple sources, aggregates and normalizes it, converts it to files that can be used for visualizations, and then stages them for use 
in a Python / plotly / dash interactive dashboard web application to visualize and interact with the data.

## App data sources:

DATA CURRENTLY IN USE: 
Google Maps (geocode API + text search API + search nearby API + place details API + distance matrix API)

DATA TO BE ADDED / IMPLEMENTED: 
OpenWeather (historical weather data API)
Wikipedia (demographic and economic data)
Census (demographic data)
Data.gov (demographic and economic data, business data, etc.)
Social Media (restaurant data)
Restaurants' websites (menu data)
Restaurant booking sites (restaurant detail and sentiment data)
Restaurant review / award / blog sites (restaurant detail and sentiment data, articles, etc.)
URLs currently listed in the .env URLS variable (we likely need a custom scraper for each website):
https://www.opentable.com/
https://resy.com/
https://www.exploretock.com/
https://www.yelp.com/
https://www.tripadvisor.com/
https://www.eater.com/
https://guide.michelin.com/en
https://www.kayak.com/
https://foursquare.com/
https://data.gov/
```

# THIS MODULE 

```
## Module functional summary: 

This module is the first step in the data pipeline. It pulls all of the initial data from the Google Maps API and saves it to a JSON file and a CSV file. 
This module is a restaurant dataset engine that uses the Google Maps API to find restaurants that meet certain search criteria based on a provided list of addresses and then scrapes the web for data about each restaurant's menu and other relevant data and news. The data is then saved to a JSON file and a CSV file for use in the next stage of the data pipeline. 

## Module execution:

input: Address string 
(working) the class is initialized and the data is loaded from the json file if it exists.
(working) the file paths for the json and csv files are constructed based on the source address string and the file drop path environment variable.
(working) the address is geocoded and the address components are parsed for use in the text search api search phrase templates.
(working) the search phrase templates are created based on the address components.
(working) the search distances in meters are set.
(working) the self.all_place_ids set is initialized.
(working) the text search and nearby search functions are called and the results are added to the self.all_place_ids set.
(working) for all results in self.all_place_ids, if the place_id is not already in the self.data dictionary or if the place_id is in the self.data dictionary and the last_updated timestamp is more than 2 days old, the place details api will be called. the api is only called when necessary to avoid rate limiting and make efficient use of cached data.
(working) the place details are fetched for each place_id in the self.all_place_ids set, but only if the place_id is not already in the self.data dictionary or if the place_id is in the self.data dictionary and the last_updated timestamp is more than 2 days old.
(working) output_1: the updated self.data dictionary is saved to the json file and the csv file.
(not yet implemented) for all results that returned a valid website, the SpiderCrawlerMenuScraper class will visit each website and navigate itself to the menu page and gather the menu links. the menu links are then added to the self.data dictionary and the updated self.data dictionary is saved to the json file and the csv file.
(not yet implemented) the menu data is parsed and saved to the json file and the csv file after normalizing it. the menu data can also be augmented / stitched / aggregated if it is found in other data sources such as the restaurant booking sites, the restaurant review / award / blog sites, or the social media sites.

## Module planned updates (roadmap):

QUEUE: add a new class called SpiderCrawlerMenuScraper that crawls the websites of the restaurants found in the AddressResearcher and gathers the menu links and saves them. the menu links are then added to the self.data dictionary and the updated self.data dictionary is saved to the json file and the csv file.
QUEUE: add some type of knowledge context and semantic parameters into the system so that the web scraping spider crawler bots can have a better sense of what they are looking for and what they are looking at and when their tasks are complete and which actions to take in any situation. 
QUEUE: scrape and parse the menu data (the body text of the menu page or the menu pdf) and save it to the json file and the csv file after normalizing it.
QUEUE: add menu price summary statistics to each object containing averages of the menu data pricing in a standard format such as: "average appetizer price, average salad price, average entree price, average side price, average dessert price, average cocktail price, average wine glass price, average beer price," etc.
QUEUE: scrape additional data points for each business such as: michelin stars, articke links, yelp links, tripadvisor links, social media, overall sentiment, etc. 
QUEUE: add a new class called CityResearcher that renders an additional report about general city demographic and economic data for the city in which the address is located. the report will include historical weather trends from the OpenWeather API, and demographic information from all other available sources like wikipedia, yfinance, census, etc.
QUEUE: add new functions to save the data to KML and geojson files based on the main json file after additional data has been scraped.
QUEUE: label the baseline dataset with classification labels for the type of cuisine (american, japanese, barbecue, italian, mexican, vegan, pan asian, indian, spanish, carribean, etc.), style of service (counter service, fast casual, full service, fine dining, tasting menu, etc.), operating hours by day period (early only, early to mid day, early to late, mid day to late, late only), tiers of proximity to the address (neighbors, within 1km, within 5km, within 10km, etc.), and other relevant labels.
QUEUE: use feature discovery to determine which features are most important for the classification model, and then train a classification model to predict the labels for future results.
QUEUE: once base classifications are determined, then classify all entities as "relevant" or "non-relevant" to our needs, begin keeping record of business names / types that are not relevant, and then modify the code to filter out those non-relevant records before calling the google place details api to avoid unnecessary api calls and charges.


## NEXT STEP AFTER THIS MODULE

After this module, the data is normalized and then saved to consolidated and formatted files for use in the Plotly / Dash interactive dashboard web application.
After that, the data is loaded into the Plotly / Dash interactive dashboard web application and visualized and interacted with by the user. 
```

'''
# IMPORTS ###################################################################################################################################

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fake_useragent import UserAgent
from functools import wraps
from math import radians, cos, sin, asin, sqrt
from pandas import json_normalize
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, ChunkedEncodingError, HTTPError, Timeout
from urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from tqdm import tqdm
from urllib.parse import urlparse, urljoin
import asyncio
import certifi
import difflib
import functools
import json
import logging
import math
import numpy as np
import os
import pandas as pd
import queue
import random
import re
import requests
import ssl
import subprocess
import threading
import time
import traceback
import webbrowser

# CUSTOM IMPORTS ##############################################################################################################################

# Load environment variables
load_dotenv()
ROOT = os.getenv('ROOT')
FILE_DROP_PATH = os.getenv('FILE_DROP_PATH')
if not os.path.exists(FILE_DROP_PATH):
    os.makedirs(FILE_DROP_PATH)
    
script_directory = os.path.dirname(os.path.abspath(__file__))

with open(f'{script_directory}/address_secrets.json', 'r') as file:
    restaurant_address_dictionary = json.load(file)
    
# extract the values from each key and add them to a list of values as strings
restaurant_addresses = {key: str(value) for key, value in restaurant_address_dictionary.items()}

addresses_list = list(restaurant_addresses.values())

# CONSTANTS ###################################################################################################################################

# Configure logging
logging.basicConfig(filename='address_researcher.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_ssl_context():
    return ssl.create_default_context(cafile=certifi.where())

ssl._create_default_https_context = create_ssl_context
context = create_ssl_context()
print(f"""SSL Context Details: 
    CA Certs File: {context.cert_store_stats()} 
    Protocol: {context.protocol} 
    Options: {context.options} 
    Verify Mode: {context.verify_mode}
    Verify Flags: {context.verify_flags}
    Check Hostname: {context.check_hostname}
    CA Certs Path: {certifi.where()}
    """)

# Set API keys and other information from environment variables
# the open weather api key is not currently being used but will be used in the CityResearcher when we add the weather data to the report
# open_weather_api_key = os.getenv('OPEN_WEATHER_API_KEY')

# FUNCTIONS ###################################################################################################################################

def requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# # Adjust the safe_request decorator to include ChunkedEncodingError in the handled_exceptions
# def safe_request(max_retries=3, backoff_factor=1, handled_exceptions=(ChunkedEncodingError,)):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             retries = 0
#             while retries < max_retries:
#                 try:
#                     response = func(*args, **kwargs)
#                     if response.status_code == 200:
#                         return response
#                     else:
#                         args[0].logger.error(f"HTTP Error: {response.status_code} for {func.__name__}")
#                 except handled_exceptions as e:
#                     args[0].logger.error(f"Request failed due to {e.__class__.__name__}: {e}, retrying...")
#                     time.sleep(backoff_factor * (2 ** retries))
#                     retries += 1
#                 except Exception as e:
#                     args[0].logger.error(f"Unhandled exception in {func.__name__}: {e}")
#                     break

#             # After all retries have been exhausted, log and return None
#             args[0].logger.error(f"All retries exhausted for {func.__name__}. Skipping to next.")
#             return None
#         return wrapper
#     return decorator

# This includes common requests exceptions and any specific exceptions you've encountered or expect from the Google APIs
GLOBAL_HANDLED_EXCEPTIONS = (
    RequestException,  # Base class for all requests exceptions
    HTTPError,  # HTTP error occurred
    ConnectionError,  # Problems with the network connection
    Timeout,  # Request timed out
    ChunkedEncodingError,  # Incomplete read error
    # Add any other specific exceptions you want to handle globally
)

def safe_request(max_retries=3, backoff_factor=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    response = func(*args, **kwargs)
                    if response.status_code == 200:
                        return response
                    else:
                        args[0].logger.error(f"HTTP Error: {response.status_code} for {func.__name__}")
                except GLOBAL_HANDLED_EXCEPTIONS as e:
                    args[0].logger.error(f"Request failed due to {e.__class__.__name__}: {e}, retrying...")
                    time.sleep(backoff_factor * (2 ** retries))
                    retries += 1
                except Exception as e:
                    args[0].logger.error(f"Unhandled exception in {func.__name__}: {e}")
                    break

            # After all retries have been exhausted, log and return None
            args[0].logger.error(f"All retries exhausted for {func.__name__}. Skipping to next.")
            return None
        return wrapper
    return decorator

# CLASSES ###################################################################################################################################

class AddressResearcher:
    def __init__(self, address):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests_retry_session()
        self.address = address
        self.logger.info(f"Initializing AddressResearcher __init__ method within the AddressResearcher class for the address: {self.address}")
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.open_weather_api_key = os.getenv('OPEN_WEATHER_API_KEY')
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self.place_text_search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.place_nearby_search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        self.place_details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        self.data = self.load_cached_data()
        self.types_to_allow_in_search = {'restaurant': ['restaurant'],}
        self.location, self.address_components, self.country, self.state, self.county, self.city, self.neighborhood, self.postal_code, self.street_name, self.street_number = self.geocode_address(self.address)
        self.text_search_phrase_templates = self.create_text_search_phrase_templates()
        self.search_distances_in_meters = [500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000, 12500, 15000, 17500, 20000, 25000, 30000, 35000]
        self.all_place_ids = set()
        self.data_shelf_life = 30  # Days

    def load_cached_data(self):
        self.logger.info(f"{self.load_cached_data.__name__} - Loading cached data for address {self.address}")
        json_file_path = self.get_json_file_path()
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                cached_data = json.load(file)
                self.logger.info(f"{self.load_cached_data.__name__} - Cached data loaded from {json_file_path}")
                return cached_data
        return {}

    def get_json_file_path(self):
        self.logger.info(f"{self.get_json_file_path.__name__} - Getting JSON file path")
        formatted_address = self.format_address_for_filename()
        self.logger.info(f"{self.get_json_file_path.__name__} - JSON file path: {os.path.join(FILE_DROP_PATH, f'restaurant_data_{formatted_address}.json')}")
        return os.path.join(FILE_DROP_PATH, f'restaurant_data_{formatted_address}.json')

    def format_address_for_filename(self):
        self.logger.info(f"{self.format_address_for_filename.__name__} - Formatting address for filename")
        return self.address.replace(',', '').replace(' ', '_')

    def geocode_address(self, address):
        self.logger.info(f"{self.geocode_address.__name__} - Geocoding address: {address}")
        '''renders the latitude / longitude and also the parsed address components for use in the text search api search phrase templates. 
            renders the data this format:
                Geocode API latitude and longitude: 
                    {'lat': 37.78886869999999, 'lng': -122.4013963}
                Geocode API address components: 
                    [{'long_name': '609', 'short_name': '609', 'types': ['street_number']}, 
                    {'long_name': 'Market Street', 'short_name': 'Market St', 'types': ['route']}, 
                    {'long_name': 'Yerba Buena', 'short_name': 'Yerba Buena', 'types': ['neighborhood', 'political']}, 
                    {'long_name': 'San Francisco', 'short_name': 'SF', 'types': ['locality', 'political']}, 
                    {'long_name': 'San Francisco County', 'short_name': 'San Francisco County', 'types': ['administrative_area_level_2', 'political']}, 
                    {'long_name': 'California', 'short_name': 'CA', 'types': ['administrative_area_level_1', 'political']}, 
                    {'long_name': 'United States', 'short_name': 'US', 'types': ['country', 'political']}, 
                    {'long_name': '94105', 'short_name': '94105', 'types': ['postal_code']}, 
                    {'long_name': '3301', 'short_name': '3301', 'types': ['postal_code_suffix']}]
        '''
        params = {'address': address, 'key': self.google_api_key}
        # response = requests.get(self.geocode_url, params=params)
        response = self.session.get(self.geocode_url, params=params)
        if response.status_code != 200:
            print(f"Geocode API request failed with status code: {response.status_code}")
            return None, None
        geocode_data = response.json()
        if geocode_data['status'] != 'OK':
            print(f"Geocode API response error: {geocode_data['status']}")
            return None, None
        location = geocode_data['results'][0]['geometry']['location']
        address_components = geocode_data['results'][0]['address_components']
        # Initialize empty variables
        country = None
        state = None
        county = None
        city = None
        neighborhood = None
        postal_code = None
        street_name = None
        street_number = None

        # Extract components
        for component in address_components:
            if 'country' in component['types']:
                country = component['long_name']
            elif 'administrative_area_level_1' in component['types']:
                state = component['long_name']
            elif 'administrative_area_level_2' in component['types']:
                county = component['long_name']
            elif 'locality' in component['types']:
                city = component['long_name']
            elif 'neighborhood' in component['types']:
                neighborhood = component['long_name']
            elif 'postal_code' in component['types']:
                postal_code = component['long_name']
            elif 'route' in component['types']:
                street_name = component['long_name']
            elif 'street_number' in component['types']:
                street_number = component['long_name']

        print(f"\n\nGeocoded address parts: {location}\n\n{address_components}\n\n{country}\n\n{state}\n\n{county}\n\n{city}\n\n{neighborhood}\n\n{postal_code}\n\n{street_name}\n\n{street_number}\n\n")
        self.logger.info(f"{self.geocode_address.__name__} - Geocode API latitude and longitude: {location}, Geocode API address components: {address_components}")

        return location, address_components, country, state, county, city, neighborhood, postal_code, street_name, street_number

    def create_text_search_phrase_templates(self):
        self.logger.info(f"{self.create_text_search_phrase_templates.__name__} - Creating text search phrase templates for address {self.address}")
        base_phrases = [
            'best restaurants {}',
            'top rated restaurants {}',
            'michelin star restaurants {}',
            'american fine dining restaurants {}',
            'luxury restaurants {}',
            'award winning restaurants {}',
            'most popular restaurants {}',
            'most expensive restaurants {}',
            'most exclusive restaurants {}',
            'elevated dining experiences {}',
            'james beard award winning restaurants {}',
            'zagat guide top restaurants {}',
            'most famous restaurants {}',
            'best places to eat {}',
            'best celebration restaurants {}',
            'hottest restaurants {}',
            'best new restaurants {}',
            'best restaurants for a date {}',
        ]

        phrases = []
        for phrase in base_phrases:
            phrases.append(phrase.format(f"near {self.address}"))  # Applying to address
            if self.street_name and self.city:
                phrases.append(phrase.format(f"on {self.street_name}, in {self.neighborhood}, {self.city}"))  # Applying to street name + neighborhood + city
            if self.neighborhood and self.city:
                phrases.append(phrase.format(f"in {self.neighborhood}, {self.city}, {self.state}"))  # Applying to neighborhood + city + state
            if self.postal_code and self.state and self.country:
                phrases.append(phrase.format(f"in {self.postal_code}, {self.city}, {self.state}"))  # Applying to postal code + city + state
            if self.county and self.state:
                phrases.append(phrase.format(f"in {self.county}, {self.city}, {self.state}"))  # Applying to county + city + state
            if self.city and self.state:
                phrases.append(phrase.format(f"in {self.city}, {self.state}"))  # Applying to city + state

        template_count = len(phrases)  # Count the number of templates generated
        print(f"Text search phrase templates: {phrases}")
        self.logger.info(f"{self.create_text_search_phrase_templates.__name__} - {template_count} text search phrase templates were created.")
        return phrases
    
    # def create_location_restriction_paramater_for_google_text_search_based_on_address(self, address):
    #     # set the location restriction parameter for the google text search based on the city in the provided address
    #     pass

    # query the google text search api with each of the search phrase templates
    # @safe_request(max_retries=3, backoff_factor=1, handled_exceptions=(ChunkedEncodingError,))
    @safe_request()
    def query_google_text_search(self, phrase):
        self.logger.info(f"{self.query_google_text_search.__name__} - Querying Google Text Search with phrase: {phrase}")
        print(f"Querying phrase: {phrase}")
        all_places = []
        next_page_token = None

        while True:
            params = {
                'query': phrase,
                'key': self.google_api_key,
                'type': 'restaurant',
                'pagetoken': next_page_token  # This will be None for the first request
            }
            print(f'Query & pagetoken: {phrase}, {next_page_token}')
            # response = requests.get(self.place_text_search_url, params=params)
            response = self.session.get(self.place_text_search_url, params=params)
            print(f"Response status code: {response.status_code}")

            if response.status_code == 200:
                search_data = response.json()
                print(f"Search data status: {search_data['status']}")

                if search_data['status'] == 'OK':
                    for result in search_data['results']:
                        place_id = result.get('place_id')
                        if place_id:  # Ensure place_id exists
                            self.all_place_ids.add(place_id)  # Add the place ID to all_place_ids
                    all_places.extend(search_data['results'])  # Collect all places

                    # Fetch next page token and wait for it to become valid
                    next_page_token = search_data.get('next_page_token')
                    print(f"Next page token: {next_page_token}")
                    if not next_page_token:
                        break  # Exit the loop if there is no next page token
                    time.sleep(2)  # Delay to ensure the next_page_token is valid
                else:
                    print(f"Search Error: {search_data['status']}")
                    break
            else:
                print(f"HTTP Error: {response.status_code}")
                break

        number_of_results = len(all_places)
        self.logger.info(f"{self.query_google_text_search.__name__} - {number_of_results} results were found for the phrase: {phrase}")
        return all_places

    # query the google nearby search api with each of the search distances
    # @safe_request(max_retries=3, backoff_factor=1, handled_exceptions=(ChunkedEncodingError,))
    @safe_request()
    def query_google_nearby_search(self, distance):
        self.logger.info(f"{self.query_google_nearby_search.__name__} - Starting nearby search with radius {distance} meters")
        print(f"Starting nearby search with radius {distance} meters")
        all_places = []
        next_page_token = None

        while True:
            params = {
                'location': f"{self.location['lat']},{self.location['lng']}",
                'radius': distance,
                'type': 'restaurant',
                'key': self.google_api_key,
                'pagetoken': next_page_token  # This will be None for the first request
            }

            # response = requests.get(self.place_nearby_search_url, params=params)
            response = self.session.get(self.place_nearby_search_url, params=params)
            if response.status_code == 200:
                search_data = response.json()

                if search_data['status'] == 'OK':
                    for result in search_data['results']:
                        place_id = result.get('place_id')
                        if place_id:  # Ensure place_id exists
                            self.all_place_ids.add(place_id)  # Add the place ID to all_place_ids
                    all_places.extend(search_data['results'])  # Collect all places

                    # Fetch next page token and wait for it to become valid
                    next_page_token = search_data.get('next_page_token')
                    if not next_page_token:
                        break  # Exit the loop if there is no next page token
                    time.sleep(2)  # Delay to ensure the next_page_token is valid
                else:
                    print(f"Nearby Search Error: {search_data['status']}")
                    break
            else:
                print(f"HTTP Error: {response.status_code}")
                break

        number_of_results = len(all_places)
        self.logger.info(f"{self.query_google_nearby_search.__name__} - {number_of_results} results were found for the nearby search with radius {distance} meters")
        return all_places
    
    # @safe_request(max_retries=3, backoff_factor=1, handled_exceptions=(ChunkedEncodingError,))
    @safe_request()
    def get_place_details(self, place_id):
        # to optimize the place details api call, we only want to request fields that are not already present in the data. this will require a dynamic list creation for the fields parameter in the place details api call.
        fields_to_search = 'place_id,name,editorial_summary,website,url,types,rating,price_level,opening_hours,utc_offset,review,user_ratings_total,international_phone_number,formatted_address,address_components,geometry,plus_code,business_status,reservable,dine_in,wheelchair_accessible_entrance,serves_breakfast,serves_brunch,serves_dinner,serves_lunch,serves_wine,serves_beer,serves_vegetarian_food'
        # Check if data exists and is fresh
        self.logger.info(f"{self.get_place_details.__name__} - Checking if data for place ID {place_id} is present")
        if place_id in self.data:
            self.logger.info(f"{self.get_place_details.__name__} - Data for {place_id} is present. Checking if it's fresh.")
            # Use .get() to safely access 'last_updated', with a fallback to a very old date if it doesn't exist
            last_updated_str = self.data[place_id].get('last_updated', '1970-01-01T00:00:00')
            try:
                last_updated = datetime.fromisoformat(last_updated_str)
            except ValueError:
                # If the date string is invalid, default to the Unix epoch start time or altenately could be expressed as datetime.min
                last_updated = datetime(1970, 1, 1)
                
            if datetime.now() - last_updated < timedelta(days=self.data_shelf_life):  # Only fetch details if data is older than the shelf life
            # if datetime.now() - last_updated < timedelta(days=14):  # This implementation uses a 14 day threshold for data freshness
                print(f"Data for {place_id} is fresh. Skipping API call.")
                self.logger.info(f"{self.get_place_details.__name__} - Data for {place_id} is fresh. Skipping API call.")
                return None  # Skip fetching details and return None to indicate no new data was fetched
        
        print(f"Fetching details for place ID: {place_id}")
        self.logger.info(f"{self.get_place_details.__name__} - No fresh data found. Fetching details for place ID: {place_id} from the place details API")
        url = self.place_details_url
        params = {
            'place_id': place_id,
            'key': self.google_api_key,
            'fields': fields_to_search,
        }
        time.sleep(1)  # Add a small delay before each call within this program's loop to avoid rate limiting
        # response = requests.get(url, params=params).json()
        response = self.session.get(url, params=params).json()
        print(f"Place details response status: {response.get('status')}")

        # if response.get('status') == 'OK':
        #     # return response.get('result', {})
        #     details = response.get('result', {})
        #     details['last_updated'] = datetime.now().isoformat()  # Add last updated timestamp
        #     print(f"\nPlace details fetched for place ID: {place_id}")
        #     self.logger.info(f"{self.get_place_details.__name__} - Place details fetched for place ID: {place_id}")
        #     # AT THIS POINT IN THE CODE, WE NEED TO FIND WHICH RESULTS ARE MISSING THE 'geometry' NESTED DICTIONARY AND/OR THE 'location' NESTED DICTIONARY CONTAINING THE 'lat' AND 'lng' FIELDS
        #     # THEN WE NEED TO GATHER THIS DATA AND ADD IT TO EACH PLACE ID RECORD IN THE JSON FILE UNDER THE 'geometry' NESTED DICTIONARY AND THE 'location' NESTED DICTIONARY CONTAINING THE 'lat' AND 'lng' FIELDS
        #     # WE WILL GET THIS FROM THE GOOGLE GEOLOCATION API
        #     return details
        # else:
        #     print(f"Error querying Place Details: {response.get('status')}")
        #     self.logger.info(f"{self.get_place_details.__name__} - Error querying Place Details: {response.get('status')}")
        #     return {}
        
        # NEW UNTESTED VERSION OF THE FUNCTION COMMENTED OUT ABOVE
        if response.get('status') == 'OK':
            details = response.get('result', {})
            details['last_updated'] = datetime.now().isoformat()  # Add last updated timestamp
            print(f"\nPlace details fetched for place ID: {place_id}")
            self.logger.info(f"{self.get_place_details.__name__} - Place details fetched for place ID: {place_id}")

            # Check if 'geometry' or 'location' data is missing
            if 'geometry' not in details or 'location' not in details['geometry']:
                # Use the self.location attribute to fill in the missing geometry data
                # Ensure self.location is up-to-date by calling self.geocode_address if needed
                if not self.location:
                    self.location, _, _, _, _, _, _, _, _, _ = self.geocode_address(details.get('formatted_address', ''))
                
                # Check again after attempting to update self.location
                if self.location:
                    details['geometry'] = {'location': self.location}
                    print(f"Updated geometry data for place ID: {place_id} with self.location")
                    self.logger.info(f"{self.get_place_details.__name__} - Updated geometry data for place ID: {place_id} with self.location")
                else:
                    print(f"Failed to update geometry data for place ID: {place_id}.")
                    self.logger.error(f"{self.get_place_details.__name__} - Failed to update geometry data for place ID: {place_id}.")

            return details
        else:
            print(f"Error querying Place Details: {response.get('status')}")
            self.logger.info(f"{self.get_place_details.__name__} - Error querying Place Details: {response.get('status')}")
            return {}


    def haversine_distance(self, coord1, coord2):
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

    # def add_crow_fly_distances(self):
    #     self.logger.info(f"{self.add_crow_fly_distances.__name__} - Adding crow fly distances...")
    #     print("Adding crow fly distances...")
    #     for place_id in self.all_place_ids:
    #         if place_id in self.data and 'geometry' in self.data[place_id]:
    #             origin = (self.location['lat'], self.location['lng'])
    #             destination = (self.data[place_id]['geometry']['location']['lat'], self.data[place_id]['geometry']['location']['lng'])
    #             distance = self.haversine_distance(origin, destination)
    #             self.data[place_id]['crow_fly_distance_km'] = distance
    #             print(f"Added crow fly distance for {place_id}: {distance} km between {origin} and {destination}")
    #             self.logger.info(f"{self.add_crow_fly_distances.__name__} - Added crow fly distance for {place_id}: {distance} km between {origin} and {destination}")
    #         else:
    #             print(f"Skipping {place_id}, missing geometry data")
    #     self.logger.info(f"{self.add_crow_fly_distances.__name__} - Crow fly distances added for {len(self.all_place_ids)} places")

    # this updated version checks if the crow fly distance already exists and ensures the new distance is not greater than the old value
    def add_crow_fly_distances(self):
        self.logger.info(f"{self.add_crow_fly_distances.__name__} - Adding crow fly distances...")
        print("Adding crow fly distances...")
        for place_id in self.all_place_ids:
            if place_id in self.data and 'geometry' in self.data[place_id]:
                origin = (self.location['lat'], self.location['lng'])
                destination = (self.data[place_id]['geometry']['location']['lat'], self.data[place_id]['geometry']['location']['lng'])
                distance = self.haversine_distance(origin, destination)
                # Check if crow_fly_distance_km already exists and if new distance is not greater than the old value
                if 'crow_fly_distance_km' not in self.data[place_id] or distance < self.data[place_id]['crow_fly_distance_km']:
                    self.data[place_id]['crow_fly_distance_km'] = distance
                    print(f"Added/Updated crow fly distance for {place_id}: {distance} km between {origin} and {destination}")
                    self.logger.info(f"{self.add_crow_fly_distances.__name__} - Added/Updated crow fly distance for {place_id}: {distance} km between {origin} and {destination}")
                else:
                    print(f"Retained existing crow fly distance for {place_id}: {self.data[place_id]['crow_fly_distance_km']} km")
            else:
                print(f"Skipping {place_id}, missing geometry data")
        self.logger.info(f"{self.add_crow_fly_distances.__name__} - Crow fly distances added/updated for {len(self.all_place_ids)} places")

    def format_weekday_text(self, opening_hours):
        '''not working'''
        # Extract 'weekday_text' and join with newline characters if it exists
        return '\n'.join(opening_hours['weekday_text']) if 'weekday_text' in opening_hours else 'N/A'

    def format_reviews(self, reviews):
        formatted_reviews = []
        for review in sorted(reviews, key=lambda x: x.get('time', 0), reverse=True)[:5]:  # Sorting by time and getting top 5
            date_time = datetime.fromtimestamp(review.get('time', 0)).strftime('%Y-%m-%d %H:%M:%S')
            review_text = (f"Date: {date_time}, Author: {review.get('author_name', 'Anonymous')}, "
                           f"Rating: {review.get('rating', 'N/A')}, "
                           f"Review: {review.get('text', 'No review text provided')}")
            formatted_reviews.append(review_text)
        return '\n\n'.join(formatted_reviews) if formatted_reviews else 'N/A'

    def save_report_as_csv(self, data, csv_file_path):
        '''opening_hours not being formatted correctly in the csv file'''
        self.logger.info(f"{self.save_report_as_csv.__name__} - Saving report as CSV file at {csv_file_path}")
        columns_order = ['place_id', 
                        'name', 
                        'rating', 
                        'user_ratings_total', 
                        'price_level', 
                        'types', 
                        'editorial_summary', 
                        'website', 
                        'url', 
                        'opening_hours', 
                        'review', 
                        'crow_fly_distance_km', 
                        'formatted_phone_number', 
                        'international_phone_number', 
                        'utc_offset', 
                        'formatted_address', 
                        'address_components', 
                        'geometry',  
                        'plus_code',
                        'business_status', 
                        'reservable', 
                        'dine_in', 
                        'wheelchair_accessible_entrance',
                        'serves_breakfast', 
                        'serves_brunch', 
                        'serves_lunch', 
                        'serves_dinner', 
                        'serves_wine', 
                        'serves_beer',
                        'serves_vegetarian_food', 
                        ]

        data_for_df = []
        for place_id, place_info in data.items():
            place_data = {column: '' for column in columns_order}  # Initialize with empty strings for all columns
            place_data['place_id'] = place_id
            place_data['opening_hours'] = self.format_weekday_text(place_info.get('opening_hours', {}))
            place_data['review'] = self.format_reviews(place_info.get('reviews', []))
            
            for key, value in place_info.items():
                if key in columns_order:  # Only add if the key is in the columns_order list
                    if isinstance(value, list):
                        place_data[key] = '; '.join([json.dumps(item) if isinstance(item, dict) else str(item) for item in value])
                    elif isinstance(value, dict):
                        place_data[key] = json.dumps(value)
                    else:
                        place_data[key] = value

            data_for_df.append(place_data)

        df = pd.DataFrame(data_for_df, columns=columns_order)  # Ensure the DataFrame follows the specified column order
        df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
        self.logger.info(f"{self.save_report_as_csv.__name__} - Report saved as CSV file at {csv_file_path}")

    def run_searches_and_save(self):
        self.logger.info(f"{self.run_searches_and_save.__name__} - Starting search and save process")
        print("Starting search and save process")
        formatted_address = self.address.replace(',', '').replace(' ', '_')
        json_file_path = os.path.join(FILE_DROP_PATH, f'restaurant_data_{formatted_address}.json')
        csv_file_path = os.path.join(FILE_DROP_PATH, f'restaurant_data_{formatted_address}.csv')
        self.logger.info(f"{self.run_searches_and_save.__name__} - JSON file path: {json_file_path}, CSV file path: {csv_file_path}")

        # Perform text and nearby searches
        for phrase in self.text_search_phrase_templates:
            self.query_google_text_search(phrase)
            time.sleep(1)  # Delay to avoid rate limiting

        for distance in self.search_distances_in_meters:
            self.query_google_nearby_search(distance)
            time.sleep(1)  # Delay to avoid rate limiting

        # Fetch place details for unique place IDs
        for place_id in tqdm(self.all_place_ids, desc="Fetching place details"):
            detailed_info = self.get_place_details(place_id)
            if detailed_info:  # Ensure valid data is received
                self.data[place_id] = detailed_info  # Update self.data

        self.add_crow_fly_distances()
        self.logger.info(f"{self.run_searches_and_save.__name__} - Crow fly distances added")

        # Save data to JSON and CSV files
        with open(json_file_path, 'w') as file:
            json.dump(self.data, file, indent=4)
        print(f"Data saved to JSON file at {json_file_path}")
        self.logger.info(f"{self.run_searches_and_save.__name__} - Data saved to JSON file at {json_file_path}")

        self.save_report_as_csv(self.data, csv_file_path)
        print(f"Data saved to CSV file at {csv_file_path}")
        self.logger.info(f"{self.run_searches_and_save.__name__} - Data saved to CSV file at {csv_file_path}")

# # Main execution
# if __name__ == "__main__":
#     for address in addresses_list:
#         logging.info(f"Processing address: {address}")
#         address_researcher = AddressResearcher(address)
#         address_researcher.run_searches_and_save()   
        
# Define a list of names to skip
names_to_skip = []

# # Main execution with skip list
# if __name__ == "__main__":
#     for address in addresses_list:
#         # Extract the name (key) from the restaurant_addresses dictionary using the address
#         name = [key for key, value in restaurant_addresses.items() if value == address][0]
        
#         # Check if the name is in the list of names to skip
#         if name in names_to_skip:
#             continue  

#         logging.info(f"Processing address: {address}")
#         address_researcher = AddressResearcher(address)
#         address_researcher.run_searches_and_save()
        
# Streamlined version of the above main execution block
if __name__ == "__main__":
    for name, address in restaurant_addresses.items():  # Iterate directly over dictionary items
        if name in names_to_skip:
            continue  # Skip the addresses whose names are in the names_to_skip list

        logging.info(f"Processing address for {name}: {address}")
        address_researcher = AddressResearcher(address)
        address_researcher.run_searches_and_save()    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
# example of the place details data structure (all restaurants in the data dictionary will have this type of structure, but some fields may be missing from some of the records)
    
'''

{
    "ChIJrXva_oJYwokROtv_EdGJgH0": {
        "address_components": [
            {
                "long_name": "2450",
                "short_name": "2450",
                "types": [
                    "street_number"
                ]
            },
            {
                "long_name": "Broadway",
                "short_name": "Broadway",
                "types": [
                    "route"
                ]
            },
            {
                "long_name": "Manhattan",
                "short_name": "Manhattan",
                "types": [
                    "sublocality_level_1",
                    "sublocality",
                    "political"
                ]
            },
            {
                "long_name": "New York",
                "short_name": "New York",
                "types": [
                    "locality",
                    "political"
                ]
            },
            {
                "long_name": "New York County",
                "short_name": "New York County",
                "types": [
                    "administrative_area_level_2",
                    "political"
                ]
            },
            {
                "long_name": "New York",
                "short_name": "NY",
                "types": [
                    "administrative_area_level_1",
                    "political"
                ]
            },
            {
                "long_name": "United States",
                "short_name": "US",
                "types": [
                    "country",
                    "political"
                ]
            },
            {
                "long_name": "10024",
                "short_name": "10024",
                "types": [
                    "postal_code"
                ]
            }
        ],
        "business_status": "OPERATIONAL",
        "curbside_pickup": true,
        "delivery": true,
        "dine_in": true,
        "editorial_summary": {
            "language": "en",
            "overview": "Low-key eatery offering a big menu of pizza & Italian classics, plus a full bar."
        },
        "formatted_address": "2450 Broadway, New York, NY 10024, USA",
        "formatted_phone_number": "(212) 362-2200",
        "geometry": {
            "location": {
                "lat": 40.7911087,
                "lng": -73.9739812
            },
            "viewport": {
                "northeast": {
                    "lat": 40.7925026802915,
                    "lng": -73.97274681970849
                },
                "southwest": {
                    "lat": 40.78980471970851,
                    "lng": -73.9754447802915
                }
            }
        },
        "international_phone_number": "+1 212-362-2200",
        "name": "Carmine's Italian Restaurant - Upper West Side",
        "opening_hours": {
            "open_now": true,
            "periods": [
                {
                    "close": {
                        "day": 0,
                        "time": "2300"
                    },
                    "open": {
                        "day": 0,
                        "time": "1130"
                    }
                },
                {
                    "close": {
                        "day": 1,
                        "time": "2200"
                    },
                    "open": {
                        "day": 1,
                        "time": "1130"
                    }
                },
                {
                    "close": {
                        "day": 2,
                        "time": "2200"
                    },
                    "open": {
                        "day": 2,
                        "time": "1130"
                    }
                },
                {
                    "close": {
                        "day": 3,
                        "time": "2200"
                    },
                    "open": {
                        "day": 3,
                        "time": "1130"
                    }
                },
                {
                    "close": {
                        "day": 4,
                        "time": "2200"
                    },
                    "open": {
                        "day": 4,
                        "time": "1130"
                    }
                },
                {
                    "close": {
                        "day": 5,
                        "time": "2200"
                    },
                    "open": {
                        "day": 5,
                        "time": "1130"
                    }
                },
                {
                    "close": {
                        "day": 6,
                        "time": "2300"
                    },
                    "open": {
                        "day": 6,
                        "time": "1130"
                    }
                }
            ],
            "weekday_text": [
                "Monday: 11:30\u202fAM\u2009\u2013\u200910:00\u202fPM",
                "Tuesday: 11:30\u202fAM\u2009\u2013\u200910:00\u202fPM",
                "Wednesday: 11:30\u202fAM\u2009\u2013\u200910:00\u202fPM",
                "Thursday: 11:30\u202fAM\u2009\u2013\u200910:00\u202fPM",
                "Friday: 11:30\u202fAM\u2009\u2013\u200910:00\u202fPM",
                "Saturday: 11:30\u202fAM\u2009\u2013\u200911:00\u202fPM",
                "Sunday: 11:30\u202fAM\u2009\u2013\u200911:00\u202fPM"
            ]
        },
        "place_id": "ChIJrXva_oJYwokROtv_EdGJgH0",
        "plus_code": {
            "compound_code": "Q2RG+CC New York, NY, USA",
            "global_code": "87G8Q2RG+CC"
        },
        "price_level": 2,
        "rating": 4.4,
        "reservable": true,
        "reviews": [
            {
                "author_name": "Mark LoGiurato",
                "author_url": "https://www.google.com/maps/contrib/116823789556768102113/reviews",
                "language": "en",
                "original_language": "en",
                "profile_photo_url": "https://lh3.googleusercontent.com/a-/ALV-UjWAUPbPFy9AkWSAVczziInarNUd1P7JOEkK6PoMNiw__Z-6=s128-c0x00000000-cc-rp-mo-ba8",
                "rating": 4,
                "relative_time_description": "a week ago",
                "text": "Famous for its generous family-style portions.  All the food is cooked to order and delicious.  The salads, antipasto, and pastas are all made fresh.  The restaurant caters to large parties with plenty of space in the main dining room. The bar is also a good place for dining.",
                "time": 1706480981,
                "translated": false
            },
            {
                "author_name": "Richard Rally",
                "author_url": "https://www.google.com/maps/contrib/101568032549845470446/reviews",
                "language": "en",
                "original_language": "en",
                "profile_photo_url": "https://lh3.googleusercontent.com/a/ACg8ocIgxVP0wgb1_t8mCws-4B1Nt3RrQfcmRHOoVe-n3Y9d=s128-c0x00000000-cc-rp-mo",
                "rating": 5,
                "relative_time_description": "2 months ago",
                "text": "This was one of the best Italian food places I've ever dined at. The portions are amazingly big! The Vodka Sauce Pasta dish was delicious! The salad was tasty and fresh! The variety of included bread was mouth watering. The service was pretty good. I enjoyed my dining experience here and the location was perfect before seeing our Broadway show.",
                "time": 1699727805,
                "translated": false
            },
            {
                "author_name": "Yvonne Cook",
                "author_url": "https://www.google.com/maps/contrib/104549369468898236668/reviews",
                "language": "en",
                "original_language": "en",
                "profile_photo_url": "https://lh3.googleusercontent.com/a/ACg8ocLwD1E7V9Q7sk0T4WwbTHXsLmgI77641Y0xq0920J3W=s128-c0x00000000-cc-rp-mo-ba2",
                "rating": 5,
                "relative_time_description": "a month ago",
                "text": "One of the highlights of our trip! We throughly enjoyed every bite of salad, calamari and the seafood special with rigatoni. Their portion sizes are no joke and a great value in my opinion. Boisterous, loud place but in a good way! The only weird thing is they asked us to pay the bill right after we ordered our food due to a shift change, which I\u2019ve never experienced before. Otherwise service was solid.",
                "time": 1704492135,
                "translated": false
            },
            {
                "author_name": "irene rivera rodriguez",
                "author_url": "https://www.google.com/maps/contrib/114220288187891547532/reviews",
                "language": "en",
                "original_language": "en",
                "profile_photo_url": "https://lh3.googleusercontent.com/a-/ALV-UjXDu8CXUE83abcSbTQy_pK7Brv18OXRf4gmoaOrt7q6IIgo=s128-c0x00000000-cc-rp-mo-ba5",
                "rating": 4,
                "relative_time_description": "a month ago",
                "text": "We made reservations & were still seated 15 after our reservations. The crowd was lively & out right loud.\nThe service was excellent. The wait staff was attentive & friendly.\nThe food is served family style, so we had food to take home. The food was delicious as always.",
                "time": 1702965933,
                "translated": false
            },
            {
                "author_name": "Salim Mohammad",
                "author_url": "https://www.google.com/maps/contrib/103656961797046682090/reviews",
                "language": "en",
                "original_language": "en",
                "profile_photo_url": "https://lh3.googleusercontent.com/a-/ALV-UjVUHfOhlYd-5-9Y-AI2zwQOhdz8kxB1HzxeC7oZpLrAj1j_=s128-c0x00000000-cc-rp-mo-ba3",
                "rating": 5,
                "relative_time_description": "in the last week",
                "text": "Carmine's Italian restaurant offers a delightful dining experience with a mix of classic flavors and hearty portions. The calamari appetizer is a standout, boasting a crispy exterior and tender inside that makes it a perfect start to your meal. The penne la vodka with shrimp is a must-try, combining perfectly cooked pasta with a rich and creamy vodka sauce that complements the succulent shrimp. As for the three-wheel lasagna, it's a cheesy delight with layers of pasta, meat, and sauce that melt in your mouth. The overall atmosphere is cozy and inviting, making Carmine's a great spot for those craving authentic Italian comfort food.",
                "time": 1706666587,
                "translated": false
            }
        ],
        "serves_breakfast": false,
        "serves_brunch": true,
        "serves_dinner": true,
        "serves_lunch": true,
        "serves_vegetarian_food": true,
        "serves_wine": true,
        "takeout": true,
        "types": [
            "meal_takeaway",
            "restaurant",
            "food",
            "point_of_interest",
            "establishment"
        ],
        "url": "https://maps.google.com/?cid=9043379582803106618",
        "user_ratings_total": 6005,
        "utc_offset": -300,
        "vicinity": "2450 Broadway, New York",
        "website": "https://www.carminesnyc.com/locations/upper-west-side",
        "wheelchair_accessible_entrance": true,
        "last_updated": "2024-02-06T19:17:13.901102",
        "crow_fly_distance_km": 10.474141195976312
    }
}

'''
        
        
        
        
        
        
        
        
        
        
        
    
        
#     def process_missing_coordinate_places(self, missing_places, origin_lat, origin_lng):
#         # Google Maps Distance Matrix API endpoint
#         # distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

#         for place in missing_places:
#             # Building the address from the place details
#             destination_address = place.get('vicinity', 'Unknown Location')
#             params = {
#                 'origins': f"{origin_lat},{origin_lng}",
#                 'destinations': destination_address,
#                 'key': self.google_api_key
#             }
#             response = requests.get(self.distance_matrix_url, params=params)
#             if response.status_code == 200:
#                 matrix_data = response.json()
#                 if matrix_data['status'] == 'OK':
#                     # Extracting distance information
#                     result = matrix_data['rows'][0]['elements'][0]
#                     if result['status'] == 'OK':
#                         distance_value = result['distance']['value'] / 1000  # Convert meters to kilometers
#                         place['distance_from_target_address'] = distance_value
#                     else:
#                         print(f"Distance calculation failed for {destination_address}: {result['status']}")
#                 else:
#                     print(f"Distance Matrix API error: {matrix_data['status']}")
#             else:
#                 print(f"Distance Matrix API request failed with status code: {response.status_code}")
    
#     def calculate_weighted_score(self, place):
#         rating = place.get('rating', 0)
#         price_level = place.get('price_level', 0)
#         distance = place.get('distance_from_target_address', float('inf'))
#         distance_factor = 1 / (distance + 1)  # Add 1 to avoid division by zero
#         return (rating * 0.4 + price_level * 0.6) * distance_factor


    


