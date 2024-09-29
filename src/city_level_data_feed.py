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
import mwparserfromhell
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
import wikipedia
import wikipediaapi

# GLOBALS ##############################################################################################################################

# Load environment variables
load_dotenv()
ROOT = os.getenv('ROOT')
FILE_DROP_PATH = os.getenv('FILE_DROP_PATH')
if not os.path.exists(FILE_DROP_PATH):
    os.makedirs(FILE_DROP_PATH)

# define script directory
script_directory = os.path.dirname(os.path.abspath(__file__))

# CLASSES ###################################################################################################################################

class WikiCityDataResearcher:
    def __init__(self):
        self.session = requests.Session()

    def fetch_wikipedia_data(self, search_phrase):
        print(f"Fetching Wikipedia data for: {search_phrase}")
        
        # Define the URL and parameters for the API request to get the raw wikitext
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "page": search_phrase,
            "format": "json",
            "prop": "wikitext",
            "redirects": True,
        }

        response = self.session.get(url=url, params=params)
        if response.status_code == 200:
            data = response.json()
            wikitext = data["parse"]["wikitext"]["*"]
            return self.parse_infobox(wikitext)
        else:
            print(f"Failed to fetch data for {search_phrase}")
            return None

    def parse_infobox(self, wikitext):
        print("Parsing wikitext to find the infobox...")
        parsed_wikitext = mwparserfromhell.parse(wikitext)

        for template in parsed_wikitext.filter_templates():
            template_name = str(template.name).strip()
            if "infobox" in template_name.lower():
                print("Infobox template found. Extracting data...")
                infobox_data = {str(param.name).strip(): str(param.value).strip() for param in template.params}
                return infobox_data

        print("No infobox found.")
        return None

# MAIN EXECUTION ###################################################################################################################################

# open the address_secrets_restaurants.json file
with open(f'{script_directory}/address_secrets_restaurants.json', 'r') as file:
    restaurant_data_objects = json.load(file)

# Initialize an empty list to hold the cities
cities = []

# Iterate through the restaurant_data_objects and extract the "city" field for each location
for location, details in restaurant_data_objects.items():
    city = details.get("city")  # Extract the city from the details
    if city and city not in cities:  # Check if city is not empty and not already in the list
        cities.append(city)

# initialize a list of cities that did not return results
failed_search_cities = []

# cities now contains all the unique city names from the data objects
for city in cities:
    print(city)
    
# Usage
researcher = WikiCityDataResearcher()

# Loop through each city and fetch Wikipedia infobox data
for city in cities:
    print(f"\nFetching data for: {city}")
    wikipedia_infobox_data = researcher.fetch_wikipedia_data(city)
    
    # Check if infobox data was found and print it
    if wikipedia_infobox_data:
        print(f"Infobox data for {city}:")
        for key, value in wikipedia_infobox_data.items():
            print(f"  {key}: {value}")
    else:
        print(f"No infobox data found for {city}.")
        # add the failed city to the failed_search_cities list
        failed_search_cities.append(city)
        
# print a log of the failed city searches
print(f"Failed to fetch data for the following cities: {', '.join(failed_search_cities)}")

# this code failed on 11/30 of the results due to disambiguation errors i believe.

# we need to add an automated decision OR allow the developer to steer the course after any error, especially disambiguation error, in the console after each failed search attempt to get it back on track without missing results or crashing.

# if the program returns a wiki disambiguation error, the alternate search term options should be presented to the user in the command line for them to choose with alternate result to search instead of the original.

# then, once the code has finished running, we should save everything as a json file in the current directory called address_city_level_data.json
