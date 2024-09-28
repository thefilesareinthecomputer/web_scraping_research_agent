# Description

## Module description: 
- A search automation tool designed to gather all available public data about restaurants located within proximity of a list of addresses. 
- Can easily be adapted to search for other types of businesses or points of interest.

## Module functional summary: 
This app is a data aggregation tool for market analysis research that uses the Google Places API, web scraping, and a few other web services (listed in detail below). The main script begins by pulling in the user's provided address list in the form of a JSON file, calls the Google Places API to find as many nearby restaurants that match the search criteria, pulls in all revevant attributes from the places API, and then scrapes listed websites for publicly available menu data. The data is then saved to a JSON file and a CSV file as a checkpoint. The place ids are the primary key in the data table and the keys in the JSON file. The script is designed to be run on a schedule to keep the data fresh and up to date. There's a mechanism for time-stamping retrieved data for each record. If records exist and have data that's more recent than the specified "shelf life" for data, those records are skipped on the API call to prevent over-spending on the places API which can get expensive if not monitored closely. This script typically gathers between 300-1000 records per source address. For a list of about 20 addresses, the script gathered about 10,000 records on the first run. 
- The script first calls the Google Geolocation API to geocode each address like this:
```bash
# renders the latitude / longitude and also the parsed address components for use in the text search api search phrase templates. 
# renders the data this format:
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
```
- Then the script parses the address components like this:
```bash
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
```
The search parameters are then templated and sent to the Google places API in various combinations of searches based on the parsed components of the original addresses - combinations such as:
```bash
# converts address components into search phrases
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
```

# Initial Setup

## Terminal commands to clone the git repo, create a virtual environment, install dependencies, and optionally add a new remote github repo
```
# clone the repo
git clone https://github.com/thefilesareinthecomputer/web_scraping_research_agent.git

# go to the repo folder
cd {REPO_FOLDER}

# make a virtual environment
python3.11 -m venv {VENV_NAME}

# activate the virtual environment
source {VENV_NAME}/bin/activate

# make sure pip, etc. are up to date
pip install --upgrade pip pip-check-reqs wheel python-dotenv

# install packages from the requirements file
pip install -r requirements.txt

# verify your .gitignore file is correct, and if not, make one:
cat .gitignore

# set up your local git repo
git init

# add the remote repo
make a new repo on github and then add your new remote repo:
git remote add origin https://github.com/{YOUR_USERNAME}/{YOUR_REPO_NAME}.git

# verify correct remote:
git remote -v

# add files to git for the initial commit
git add .

# commit changes
git commit -m "initial commit"

# push to remote repo:
git push -u origin main

Download the correct version of the google chrome driver from this link, unzip it, and place it in your project directory:
- https://googlechromelabs.github.io/chrome-for-testing/#stable
```

# Roadmap & Future Updates

## Output features:
```
Outputs:
[complete] - a json file containing the data
[complete] - a csv file containing the data
[complete] - a static html file containing all the data on a map with nice formatting
- a kml file containing the multiple layers of data on a map
- a geojson file containing the data
- a formatted report of slides containing the data as a presentation
- an interactive dashboard web app containing the data with dropdown filters for all categorical data
```

# Details

## Data sources:
```
CURRENTLY IN USE: 
API: Google Maps (geocode API + text search API + search nearby API + place details API + distance matrix API)

UPCOMING:

Python libraries specifically for data feeds or datasets:
- foursquare places API
- wikipedia
- pandas-datareader
- yfinance
- overpy
- pyowm
- tweepy
- eurostat

API data sources:
- Google Maps API
- Google Places API
- Google Distance Matrix API
- Google Geocoding API
- OpenWeather API
- OpenStreetMap API
- Census API
- Eurostat API

Dataset download sites:
- Kaggle
- UCI Machine Learning Repository
- Data.gov
- Data.world
- Google Dataset Search
- Wikipedia
- AWS Public Datasets
- Stanford Large Network Dataset Collection
- GitHub Awesome Public Datasets

Websites to scrape:
"restaurant": {
    "bonappetit": "https://www.bonappetit.com/",
    "booking": "https://www.booking.com/",
    "chowhound": "https://www.chowhound.com/",
    "cntraveler": "https://www.cntraveler.com/",
    "culturetrip": "https://theculturetrip.com/",
    "dinersclub": "https://www.dinersclub.com/",
    "eater": "https://www.eater.com/",
    "eatertravel": "https://www.eater.com/travel",
    "exploretock": "https://www.exploretock.com/",
    "foodandwine": "https://www.foodandwine.com/",
    "foursquare": "https://foursquare.com/",
    "happycow": "https://www.happycow.net/",
    "jamesbeard": "https://www.jamesbeard.org/",
    "laliste": "https://www.laliste.com/",
    "localeats": "https://www.localeats.com/",
    "luxuryrestaurantguide": "https://www.luxuryrestaurantguide.com/",
    "michelinguide": "https://guide.michelin.com/en/",
    "michelintravel": "https://travelguide.michelin.com/",
    "nrn": "https://www.nrn.com/",
    "opentable": "https://www.opentable.com/",
    "relaischateaux": "https://www.relaischateaux.com/us/",
    "restaurantbusinessonline": "https://www.restaurantbusinessonline.com/",
    "resy": "https://resy.com/",
    "saveur": "https://www.saveur.com/",
    "theinfatuation": "https://www.theinfatuation.com/",
    "thrillist": "https://www.thrillist.com/",
    "toasttab": "https://pos.toasttab.com/",
    "travelandleisure": "https://www.travelandleisure.com/",
    "tripadvisor": "https://www.tripadvisor.com/",
    "viator": "https://www.viator.com/",
    "wineenthusiast": "https://www.wineenthusiast.com/",
    "worlds50best": "https://www.theworlds50best.com/",
    "yelp": "https://www.yelp.com/",
    "yelpreservations": "https://restaurants.yelp.com/products/waitlist-table-management/",
    "zagat": "https://www.zagat.com/"
},
"general": {
    "bloomberg": "https://www.bloomberg.com/",
    "census": "https://www.census.gov/",
    "citydata": "https://www.city-data.com/",
    "enjoytravel": "https://www.enjoytravel.com/",
    "eurostat": "https://ec.europa.eu/eurostat/",
    "financialtimes": "https://www.ft.com/",
    "geofabrik": "http://www.geofabrik.de/",
    "geonames": "http://www.geonames.org/",
    "nomis": "https://www.nomisweb.co.uk/",
    "oecd": "https://data.oecd.org/",
    "openflights": "https://openflights.org/data.html",
    "openstreetmap": "https://www.openstreetmap.org/",
    "openweathermap": "https://openweathermap.org/",
    "politico": "https://www.politico.com/",
    "quandl": "https://www.quandl.com/",
    "reuters": "https://www.reuters.com/",
    "statista": "https://www.statista.com/",
    "tradingeconomics": "https://tradingeconomics.com/",
    "unData": "http://data.un.org/",
    "worldbank": "https://data.worldbank.org/"
}
```

## Search & Data Aggregation Execution:
```
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

## module planned updates (roadmap):
ACTIVE NOW IN THIS SPRINT: add a new class called SpiderCrawlerMenuScraper that crawls the websites of the restaurants found in the AddressResearcher and gathers the menu links and saves them. the menu links are then added to the self.data dictionary and the updated self.data dictionary is saved to the json file and the csv file.
QUEUE: scrape and parse the menu data (the body text of the menu page or the menu pdf) and save it to the json file and the csv file after normalizing it.
QUEUE: add menu price summary statistics to each object containing averages of the menu data pricing in a standard format such as: "average appetizer price, average salad price, average entree price, average side price, average dessert price, average cocktail price, average wine glass price, average beer price," etc.
QUEUE: scrape additional data points for each business such as: michelin stars, articke links, yelp links, tripadvisor links, social media, overall sentiment, etc. 
QUEUE: add a new class called CityResearcher that renders an additional report about general city demographic and economic data for the city in which the address is located. the report will include historical weather trends from the OpenWeather API, and demographic information from all other available sources like wikipedia, yfinance, census, etc.
QUEUE: add new functions to save the data to KML and geojson files based on the main json file after additional data has been scraped.
QUEUE: label the baseline dataset with classification labels for the type of cuisine (american, japanese, barbecue, italian, mexican, vegan, pan asian, indian, spanish, carribean, etc.), style of service (counter service, fast casual, full service, fine dining, tasting menu, etc.), operating hours by day period (early only, early to mid day, early to late, mid day to late, late only), tiers of proximity to the address (neighbors, within 1km, within 5km, within 10km, etc.), and other relevant labels.
QUEUE: use feature discovery to determine which features are most important for the classification model, and then train a classification model to predict the labels for future results.
QUEUE: once base classifications are determined, then classify all entities as "relevant" or "non-relevant" to our needs, begin keeping record of business names / types that are not relevant, and then modify the code to filter out those non-relevant records before calling the google place details api to avoid unnecessary api calls and charges.
```

