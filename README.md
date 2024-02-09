# Initial Setup

## terminal commands to create a virtual environment, git repo, github repo, and install dependencies
```
python3.11 -m venv {"your venv name here"}
source {"your venv name here"}/bin/activate
deactivate
git init
git add .
git commit -m "init"
git remote add origin https://github.com/{"your github name here"}/{"your venv name here"}
git branch -M main
git push -u origin main
source {"your venv name here"}/bin/activate
pip install --upgrade pip certifi
pip install beautifulsoup4 selenium python-dotenv requests webdriver-manager pandas fake_useragent tqdm Pyarrow simplekml pyopenssl ndg-httpsclient pyasn1 google-generativeai google-api-python-client howdoi wikipedia ipython jupyter
```

## download the correct version of the google chrome driver from this link, unzip it, and place it in your project directory:
https://googlechromelabs.github.io/chrome-for-testing/#stable

## module description: 
A search automation tool designed to gather all available public data about restaurants within proximity of a given list of addresses. 

## module functional summary: 
This module is a web scraping research agent that uses the Google Maps API to find nearby restaurants based on a provided address and then scrapes their websites for menu links. The data is then saved to a JSON file and a CSV file. 

## Data sources:
```
Google Maps (geocode API + text search API + search nearby API + place details API + distance matrix API)
OpenWeather (historical weather data API)
Wikipedia (demographic and economic data)
Census (demographic data)
```

## Execution:
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