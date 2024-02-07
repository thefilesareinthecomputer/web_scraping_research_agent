### Initial Setup
## Create a virtual environment, git repo, github repo, and install dependencies
# terminal commands in root directory
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
pip install beautifulsoup4 selenium python-dotenv requests webdriver-manager pandas fake_useragent tqdm Pyarrow simplekml

# download and unzip this:
https://googlechromelabs.github.io/chrome-for-testing/#stable

## Step-by-step Explanation:
Execution:
input: Address string 
the class is initialized and the data is loaded from the json file if it exists.
the file paths for the json and csv files are constructed based on the source address string and the file drop path environment variable.
the address is geocoded and the address components are parsed for use in the text search api search phrase templates.
the search phrase templates are created based on the address components.
the search distances in meters are set.
the self.all_place_ids set is initialized.
the text search and nearby search functions are called and the results are added to the self.all_place_ids set.
for all results in self.all_place_ids, if the place_id is not already in the self.data dictionary or if the place_id is in the self.data dictionary and the last_updated timestamp is more than 2 days old, the place details api will be called. the api is only called when necessary to avoid rate limiting and make efficient use of cached data.
the place details are fetched for each place_id in the self.all_place_ids set, but only if the place_id is not already in the self.data dictionary or if the place_id is in the self.data dictionary and the last_updated timestamp is more than 2 days old.
output: the updated self.data dictionary is saved to the json file and the csv file.