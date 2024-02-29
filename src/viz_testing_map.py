
import folium
from folium import IFrame, CustomIcon
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ROOT = os.getenv('ROOT')
script_directory = os.path.dirname(os.path.abspath(__file__))

# Create the map files drop folder if it doesn't exist
map_file_drop_folder = os.path.join(ROOT, 'src', 'map_files')
if not os.path.exists(map_file_drop_folder):
    os.makedirs(map_file_drop_folder)

# Load the json data for restaurant locations
with open(f'{script_directory}/address_secrets_restaurants.json', 'r') as file:
    data = json.load(file)

# Load the json data for comparison locations
with open(f'{ROOT}/reports_processed/restaurant_data_all_combined.json', 'r') as file:
    comp_data = json.load(file)

# Initialize a map object with a dark theme
m = folium.Map(location=[41.881832, -87.623177], tiles='CartoDB dark_matter', zoom_start=5)

# Path to the logo for restaurant locations
logo_icon_path = f'{map_file_drop_folder}/_logo.png'  # Update to your logo file path

# Loop through each restaurant in data and add to the map
for restaurant, details in data.items():
    lat, lng = details['latitude'], details['longitude']
    stat_card_content = f"<h4>{restaurant}</h4>"
    for key, value in details.items():
        
        if isinstance(value, list):
            value = ', '.join(value)
        elif isinstance(value, float):
            value = f"{value:.2f}"  # Format float to 2 decimal places
        if key not in ['latitude', 'longitude', 'street_number', 'street', 'place_details']:
            stat_card_content += f"<p><b>{key.capitalize()}:</b> {value}</p>"
        if key == 'place_details':  # Handle place_details specifically
            place_details = value  # Assuming value is a dictionary
            # Format specific fields from place_details
            website = place_details.get('website', 'N/A')
            url = place_details.get('url', 'N/A')
            phone_number = place_details.get('formatted_phone_number', 'N/A')
            reviews = '<br>'.join(review.get('text', 'N/A') for review in place_details.get('reviews', [])[:5])
            rating = place_details.get('rating', 'N/A')
            
            stat_card_content += f"<p><b>Website:</b> <a href='{website}' target='_blank'>{website}</a></p>"
            stat_card_content += f"<p><b>Maps URL:</b> <a href='{url}' target='_blank'>{url}</a></p>"
            stat_card_content += f"<p><b>Phone Number:</b> {phone_number}</p>"
            stat_card_content += f"<p><b>Average Review Score:</b> {rating}</p>"
    
    iframe = IFrame(html=stat_card_content, width=300, height=900)
    popup = folium.Popup(iframe, max_width=300)

    icon = CustomIcon(logo_icon_path, icon_size=(20, 20))
    folium.Marker([lat, lng], icon=icon, popup=popup).add_to(m)

# Function to map price level to grey scale color
def price_to_color(price_level):
    colors = ['#d4d4d4', '#a9a9a9', '#7e7e7e', '#535353']  # Example grey scale colors
    return colors[price_level-1] if price_level <= len(colors) else colors[-1]

# Define filters
min_rating = 4.0  # Minimum acceptable rating
allowed_price_levels = [3, 4]  # Only include these price levels

# Initialize a counter for the number of locations included
included_locations_count = 0

# Loop through comparison data and add grey dots with popups to the map
for comp_id, details in comp_data.items():
    geometry = details.get('geometry', {})
    location = geometry.get('location', {})
    lat = location.get('lat')
    lng = location.get('lng')
    price_level = details.get('price_level', None)
    rating = details.get('rating', 0)

    # Skip locations that don't meet the criteria
    if price_level not in allowed_price_levels or rating < min_rating:
        continue
    
    # Increment the counter for included locations
    included_locations_count += 1
    
    # Construct the popup content with a more angular aesthetic
    popup_content = f"""
    <div style="font-family: 'Arial', sans-serif; font-size: 14px;">
        <strong>{details.get('name')}</strong><br>
        <a href='{details.get('website', '#')}' target='_blank'>Website</a><br>
        <a href='{details.get('url', '#')}' target='_blank'>Maps URL</a><br><br>
        Address: {details.get('formatted_address', 'N/A')}<br>
        Phone: {details.get('formatted_phone_number', 'N/A')}<br><br>
        Rating: {rating}<br>
        Total Ratings: {details.get('user_ratings_total', 'N/A')}<br>
        Price Level: {price_level}<br><br>
        Types: {', '.join(details.get('types', []))}<br><br>
        Editorial Summary: {details.get('editorial_summary', {}).get('overview', 'N/A')}<br><br>
        Operating Hours: <br>{'<br>'.join(details.get('opening_hours', {}).get('weekday_text', ['N/A']))}<br><br>
        Reservations: {details.get('reservable', 'N/A')}<br>
        Dine In: {details.get('dine_in', 'N/A')}<br>
        Serves Wine: {details.get('serves_wine', 'N/A')}<br>
        Serves Breakfast: {details.get('serves_breakfast', 'N/A')}<br>
        Serves Brunch: {details.get('serves_brunch', 'N/A')}<br>
        Serves Lunch: {details.get('serves_lunch', 'N/A')}<br>
        Serves Dinner: {details.get('serves_dinner', 'N/A')}<br><br>
        Review Text: <br>{'<br><br>'.join(review.get('text', 'N/A') for review in details.get('reviews', [])[:5])}<br><br>
    </div>
    """
    iframe = IFrame(html=popup_content, width=300, height=900)
    popup = folium.Popup(iframe, max_width=300)

    # Only proceed if lat and lng are available
    if lat is not None and lng is not None:
        folium.CircleMarker(
            location=[lat, lng],
            radius=3.5,
            color='#d4d4d4',
            fill=True,
            fill_color='#d4d4d4',
            fill_opacity=0.5
        ).add_to(m).add_child(popup)

# Print the number of locations included after filtering
print(f"Included locations after filtering: {included_locations_count}")

# Save the map to an HTML file
m.save(f'{map_file_drop_folder}/restaurant_map_new.html')
print(f"Map saved to {map_file_drop_folder}")



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
