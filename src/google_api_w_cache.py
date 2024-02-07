'''

module description: 
a search automation tool designed to gather all available public data about restaurants within proximity of a given address. 

module functional summary: 
This module is a web scraping research agent that uses the Google Maps API to find nearby restaurants based on a provided address and then scrapes their websites for menu links. The data is then saved to a JSON file and a CSV file. 

Data sources:
Google Maps (geocode API + text search API + search nearby API + place details API + distance matrix API)
OpenWeather (historical weather data API)
Wikipedia (demographic and economic data)
Census (demographic data)

Execution:
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

module required enhancements:
ACTIVE NOW IN THIS SPRINT: add a new class called SpiderCrawlerMenuScraper that crawls the websites of the restaurants found in the AddressResearcher and gathers the menu links and saves them. the menu links are then added to the self.data dictionary and the updated self.data dictionary is saved to the json file and the csv file.
QUEUE: add a new class called CityResearcher that renders an additional report about general city demographic and economic data for the city in which the address is located. the report will include historical weather trends from the OpenWeather API, and demographic information from all other available sources like wikipedia, yfinance, census, etc.
QUEUE: add new functions to save the data to KML and geojson files based on the main json file after additional data has been scraped.

'''
# IMPORTS ###################################################################################################################################

logging.info(f"Importing modules...")
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fake_useragent import UserAgent
from functools import wraps
from math import radians, cos, sin, asin, sqrt
from pandas import json_normalize
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

logging.info(f"Importing addresses from custom search_parameters module...")
from address_secrets.search_parameters import addresses
addresses_list = list(addresses.values())
logging.info(f"Addresses: {addresses_list}")

# CONSTANTS ###################################################################################################################################

'''Note: If this runs once daily and stores the changes in a database and monitors state, it will be a market monitoring system instead of a one-off market 
comparison report generator.'''

# call_depth = threading.local()
# call_depth.counter = 0  # Initialize the counter

# class CallDepthFilter(logging.Filter):
#     def filter(self, record):
#         depth = getattr(call_depth, 'counter', 0)
#         record.call_depth = depth
#         return True

# def track_call_depth(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         if not hasattr(call_depth, 'counter'):
#             call_depth.counter = 0
#         call_depth.counter += 1
#         try:
#             result = func(*args, **kwargs)
#         finally:
#             call_depth.counter -= 1
#         return result
#     return wrapper

# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - [Depth: %(call_depth)s] - %(message)s'
# )
# logger = logging.getLogger(__name__)
# logger.addFilter(CallDepthFilter())

# logging.info(f"Logging activated for {__name__} module")

# Configure logging
logging.basicConfig(filename='address_researcher.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
# establish the path for saving data
FILE_DROP_PATH = os.getenv('FILE_DROP_PATH')
# make the file drop path if it doesn't exist
if not os.path.exists(FILE_DROP_PATH):
    os.makedirs(FILE_DROP_PATH)
# gather all 10 of the base URLs to be indexed and scraped
urls = [os.getenv(f'URL_{i}') for i in range(1, 11) if os.getenv(f'URL_{i}') is not None]
logging.info(f"URLs to be indexed and scraped: {urls}")

# Set API keys and other information from environment variables
# the open weather api key is not currently being used but will be used in the CityResearcher when we add the weather data to the report
# open_weather_api_key = os.getenv('OPEN_WEATHER_API_KEY')

address = "23 Avenue des Champs Elysées 75008 Paris, France"
logging.info(f"Address of current search: {address}")

# FUNCTION DEFINITIONS ###################################################################################################################################

class AddressResearcher:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # self.logger.addFilter(CallDepthFilter())
        self.logger.info("Initializing AddressResearcher __init__ method within the AddressResearcher class...")
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.open_weather_api_key = os.getenv('OPEN_WEATHER_API_KEY')
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self.place_text_search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.place_nearby_search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        self.place_details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        # self.new_place_details_url = "https://places.googleapis.com/v1/places/{PLACE_ID}"
        # self.data = {}
        self.data = self.load_cached_data()
        self.types_to_allow_in_search = {'restaurant': ['restaurant'],}
        self.location, self.address_components, self.country, self.state, self.county, self.city, self.neighborhood, self.postal_code, self.street_name, self.street_number = self.geocode_address(address)
        self.text_search_phrase_templates = self.create_text_search_phrase_templates()
        # self.search_distances_in_meters = [200, 400, 600, 800, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000, 9000, 10000, 12500, 15000, 17500, 20000, 22500, 25000]
        self.search_distances_in_meters = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 7500, 10000, 15000, 20000, 25000, 30000]
        self.all_place_ids = set()

    # @track_call_depth
    def load_cached_data(self):
        self.logger.info(f"{self.load_cached_data.__name__} - Loading cached data for address {address}")
        json_file_path = self.get_json_file_path()
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                cached_data = json.load(file)
                self.logger.info(f"{self.load_cached_data.__name__} - Cached data loaded from {json_file_path}")
                return cached_data
        return {}

    # @track_call_depth
    def get_json_file_path(self):
        self.logger.info(f"{self.get_json_file_path.__name__} - Getting JSON file path")
        formatted_address = self.format_address_for_filename()
        self.logger.info(f"{self.get_json_file_path.__name__} - JSON file path: {os.path.join(FILE_DROP_PATH, f'restaurant_data_{formatted_address}.json')}")
        return os.path.join(FILE_DROP_PATH, f'restaurant_data_{formatted_address}.json')

    # @track_call_depth
    def format_address_for_filename(self):
        self.logger.info(f"{self.format_address_for_filename.__name__} - Formatting address for filename")
        return address.replace(',', '').replace(' ', '_')

    # @track_call_depth
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
        response = requests.get(self.geocode_url, params=params)
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

    # @track_call_depth
    def create_text_search_phrase_templates(self):
        self.logger.info(f"{self.create_text_search_phrase_templates.__name__} - Creating text search phrase templates for address {address}")
        base_phrases = [
            'best restaurants near {}',
            'top rated restaurants near {}',
            'michelin star restaurants near {}',
            'american fine dining near {}',
            'fine dining restaurants near {}',
            # 'luxury restaurants near {}',
            'award winning restaurants near {}',
            'most popular restaurants near {}',
            # 'most expensive restaurants near {}',
            # 'most exclusive restaurants near {}',
            # 'new american fine dining near {}',
            'elevated dining experiences near {}',
            'james beard award winning restaurants near {}',
            'zagat top restaurants near {}',
            'most famous restaurants near {}',
            # 'best places to eat near {}',
            # 'best celebration restaurants near {}',
        ]

        phrases = []
        for phrase in base_phrases:
            phrases.append(phrase.format(address))  # Applying to address
            if self.street_name and self.city:
                phrases.append(phrase.format(f"{self.street_name}, {self.neighborhood}, {self.city}"))  # Applying to street name + neighborhood + city
            if self.neighborhood and self.city:
                phrases.append(phrase.format(f"{self.neighborhood}, {self.city}, {self.state}"))  # Applying to neighborhood + city + state
            if self.postal_code and self.state and self.country:
                phrases.append(phrase.format(f"{self.postal_code}, {self.city}, {self.state}"))  # Applying to postal code + city + state
            if self.county and self.state:
                phrases.append(phrase.format(f"{self.county}, {self.city}, {self.state}"))  # Applying to county + city + state
            if self.city and self.state:
                phrases.append(phrase.format(f"{self.city}, {self.state}"))  # Applying to city + state

        template_count = len(phrases)  # Count the number of templates generated
        print(f"Text search phrase templates: {phrases}")
        self.logger.info(f"{self.create_text_search_phrase_templates.__name__} - {template_count} text search phrase templates were created.")
        return phrases
    
    def create_location_restriction_paramater_for_google_text_search_based_on_address(self, address):
        # set the location restriction parameter for the google text search based on the city in the provided address
        pass
        
    # @track_call_depth
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
            response = requests.get(self.place_text_search_url, params=params)
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

    # @track_call_depth
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

            response = requests.get(self.place_nearby_search_url, params=params)
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
    
    # @track_call_depth
    def get_place_details(self, place_id):
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
                
            if datetime.now() - last_updated < timedelta(days=2):
                print(f"Data for {place_id} is fresh. Skipping API call.")
                self.logger.info(f"{self.get_place_details.__name__} - Data for {place_id} is fresh. Skipping API call.")
                return None  # Skip fetching details and return None to indicate no new data was fetched
        
        print(f"Fetching details for place ID: {place_id}")
        self.logger.info(f"{self.get_place_details.__name__} - No fresh data found. Fetching details for place ID: {place_id} from the place details API")
        url = self.place_details_url
        params = {
            'place_id': place_id,
            'key': self.google_api_key,
            'fields': 'place_id,name,editorial_summary,website,url,icon,types,rating,price_level,opening_hours,utc_offset,review,user_ratings_total,formatted_phone_number,international_phone_number,formatted_address,address_components,geometry,plus_code,business_status,reservable,dine_in,wheelchair_accessible_entrance,serves_breakfast,serves_brunch,serves_dinner,serves_lunch,serves_wine,serves_beer,serves_vegetarian_food',
        }
        time.sleep(1)  # Add a small delay before each call within this program's loop to avoid rate limiting
        response = requests.get(url, params=params).json()
        print(f"Place details response status: {response.get('status')}")

        if response.get('status') == 'OK':
            # return response.get('result', {})
            details = response.get('result', {})
            details['last_updated'] = datetime.now().isoformat()  # Add last updated timestamp
            print(f"\nPlace details fetched for place ID: {place_id}")
            self.logger.info(f"{self.get_place_details.__name__} - Place details fetched for place ID: {place_id}")
            return details
        else:
            print(f"Error querying Place Details: {response.get('status')}")
            self.logger.info(f"{self.get_place_details.__name__} - Error querying Place Details: {response.get('status')}")
            return {}

    # @track_call_depth
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
        print(f"Distance: {distance} km")
        self.logger.info(f"{self.haversine_distance.__name__} - Haversine distance between {coord1} and {coord2}: {distance} km")
        return distance

    # @track_call_depth
    def add_crow_fly_distances(self):
        self.logger.info(f"{self.add_crow_fly_distances.__name__} - Adding crow fly distances...")
        print("Adding crow fly distances...")
        for place_id in self.all_place_ids:
            if place_id in self.data and 'geometry' in self.data[place_id]:
                origin = (self.location['lat'], self.location['lng'])
                destination = (self.data[place_id]['geometry']['location']['lat'], self.data[place_id]['geometry']['location']['lng'])
                distance = self.haversine_distance(origin, destination)
                self.data[place_id]['crow_fly_distance_km'] = distance
                print(f"Added crow fly distance for {place_id}: {distance} km between {origin} and {destination}")
                self.logger.info(f"{self.add_crow_fly_distances.__name__} - Added crow fly distance for {place_id}: {distance} km")
            else:
                print(f"Skipping {place_id}, missing geometry data")
                self.logger.info(f"{self.add_crow_fly_distances.__name__} - Skipping {place_id}, missing geometry data")

    # @track_call_depth
    def format_weekday_text(self, opening_hours):
        '''not working'''
        # Extract 'weekday_text' and join with newline characters if it exists
        return '\n'.join(opening_hours['weekday_text']) if 'weekday_text' in opening_hours else 'N/A'

    # @track_call_depth
    def format_reviews(self, reviews):
        formatted_reviews = []
        for review in sorted(reviews, key=lambda x: x.get('time', 0), reverse=True)[:5]:  # Sorting by time and getting top 5
            date_time = datetime.fromtimestamp(review.get('time', 0)).strftime('%Y-%m-%d %H:%M:%S')
            review_text = (f"Date: {date_time}, Author: {review.get('author_name', 'Anonymous')}, "
                           f"Rating: {review.get('rating', 'N/A')}, "
                           f"Review: {review.get('text', 'No review text provided')}")
            formatted_reviews.append(review_text)
        return '\n\n'.join(formatted_reviews) if formatted_reviews else 'N/A'

    # @track_call_depth
    def save_report_as_csv(self, data, csv_file_path):
        '''opening_hours not being formatted correctly in the csv file'''
        self.logger.info(f"{self.save_report_as_csv.__name__} - Saving report as CSV file at {csv_file_path}")
        columns_order = ['place_id', 
                        'name', 
                        'types', 
                        'editorial_summary', 
                        'website', 
                        'url', 
                        'icon',
                        'rating', 
                        'user_ratings_total', 
                        'price_level', 
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

    # @track_call_depth
    def run_searches_and_save(self):
        self.logger.info(f"{self.run_searches_and_save.__name__} - Starting search and save process")
        print("Starting search and save process")
        formatted_address = address.replace(',', '').replace(' ', '_')
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

# initialize the AddressResearcher class
logging.info(f"Initializing AddressResearcher class")
address_researcher = AddressResearcher()
logging.info(f"AddressResearcher class initialized")
# run the searches and save the data
address_researcher.run_searches_and_save()
logging.info(f"Searches completed and data saved")

        
        
        
        
'''

imports and constants are all set up. omitted for brevity.

please help me get all these done and ensure i'm saving the files correctly and i need to add the mechanism for adding the "last updated" stamp to each search result and then checking for it when running against the cached data to ensure we aren't re-running api calls for objects that have place details data that's less than 2 days old.

notice the address variable is set to a string. this is the address that will be used to search for restaurants and then gather data about them.
this string is appended to the saved filenames after all commas are removed and all spaces are replaced with underscores.
the names of these saved files will be restaurant_data_9_9th_Ave_New_York_NY_10014.json and restaurant_data_9_9th_Ave_New_York_NY_10014.csv

make sure your approach handles the caching, loading, querying, cross-checking, flow, and re-updating of the data updating correctly in the code. 
make sure datetime stamps are correctly added and checked to prevent errors.

here's the desired functionality when the code executes:

the file paths for the saved json and csv files are constructed based on the source address string and the file drop path environment variable.

##------- CHATGPT INSTRUCTIONS HERE:

OK, so here are the main issues:
self.all_place_ids gets initialized with the class and used directly within the google api search nearby and text search methods to prevent duplicate records. 
But then, during the run searches and save main execution function, another all_place_ids gets created and used. 
the same thing kind of happens with self.data and cached_data, but the variable cached_data is not used in the code yet. 
it's intended purpose is to load the pre-existing json data into memory so that it can be compared against the new results to see if the new results are more up to date and if there are any place_ids that already have place details data so we can skip the api call for records that already have the enriched data from a prior run.

please tell me how to correctly route all these variables and ensure they are all "self. " versions rather than method specific versions, and let's make sure to combine them correctly if we need to do that or re-name them with unique names if they need to stay separate to maintain the cirrect flow and execution logic for what i described.
do not write many new functions and bloat the code. i'm only looking for a couple tweaks.
please tell me in detail where these should go and every change i need to make to my existing code to do all of this correctly. 
do not add too many new lines of code. we want to minimize the length of this script. as few functions and as few lines of code as possible to get the job done.
make sure all of your code is correct and then tell me all the new code again in the simplest way you can that conveys all the info.
please help me get all these done and ensure i'm saving the files correctly and i need to add the mechanism for adding the "last updated" stamp to each search result and then checking for it when running against the cached data to ensure we aren't re-running api calls for objects that have place details data that's less than 2 days old.
verify that a place will not be skipped for place details api call if only the place_id exists in the self.all_place_ids set and in the self.data cached data and/or overwritten recent search results. 
also verify that the search query functions themselves won't simply overwrite the cached data while they execute their searches during each run.;



To ensure that places are not skipped for Place Details API calls incorrectly and that search query functions do not overwrite cached data without due checks, follow these guidelines:

Check for Existing Data with Timestamp: Before deciding to skip fetching place details, check if the place ID exists in self.data. If it exists, verify that the last_updated timestamp is within the acceptable range (e.g., less than 2 days old). Only skip the API call if both conditions are met.

Prevent Overwriting of Fresh Data: When processing search results, before updating self.data with new information, check if the existing data for a place ID is still fresh (i.e., the last_updated timestamp is less than 2 days old). If it is, do not overwrite it with new search results. This ensures that detailed data that was recently fetched isn't lost.

Implementation Steps:
In query_google_text_search and query_google_nearby_search methods:
When adding place IDs to self.all_place_ids, do not immediately update self.data with the search result. Only update self.data after checking if detailed information needs to be fetched.
In get_place_details method:
Before fetching details, check if the place ID already exists in self.data with a recent last_updated timestamp. Fetch details only if necessary.
After fetching details, add or update the entry in self.data with the new details and the current timestamp.
In run_searches_and_save method:
When iterating over self.all_place_ids, first check if each place ID exists in self.data and whether the data is fresh.
Fetch and update details only for those place IDs that don't have fresh data in self.data.
we need to make sure there is robustness and error handling in the places where we check the last updated date anywhere we do that. 

'''
        
        
        
    
    
    
    
    
    
    
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


    


