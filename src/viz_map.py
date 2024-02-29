
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
        if key not in ['latitude', 'longitude', 'street_number', 'street', 'place_details']:
            stat_card_content += f"<p><b>{key.capitalize()}:</b> {value}</p>"
    
    iframe = IFrame(html=stat_card_content, width=320, height=220)
    popup = folium.Popup(iframe, max_width=320)

    icon = CustomIcon(logo_icon_path, icon_size=(20, 20))
    folium.Marker([lat, lng], icon=icon, popup=popup).add_to(m)

# Function to map price level to grey scale color
def price_to_color(price_level):
    colors = ['#d4d4d4', '#a9a9a9', '#7e7e7e', '#535353']  # Example grey scale colors
    return colors[price_level-1] if price_level <= len(colors) else colors[-1]

# Define filters
min_rating = 4.2  # Minimum acceptable rating
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
        Address: {details.get('formatted_address', 'N/A')}<br>
        Phone: {details.get('formatted_phone_number', 'N/A')}<br>
        Rating: {rating}<br>
        Price Level: {price_level}<br>
        Editorial Summary: {details.get('editorial_summary', 'N/A')}<br>
        <a href='{details.get('website', '#')}' target='_blank'>Website</a><br>
        <a href='{details.get('url', '#')}' target='_blank'>Maps URL</a><br>
    </div>
    """
    iframe = IFrame(html=popup_content, width=300, height=150)
    popup = folium.Popup(iframe, max_width=300)

    # Only proceed if lat and lng are available
    if lat is not None and lng is not None:
        folium.CircleMarker(
            location=[lat, lng],
            radius=3.5,
            color=price_to_color(price_level),
            fill=True,
            fill_color=price_to_color(price_level),
            fill_opacity=0.5
        ).add_to(m).add_child(popup)

# Print the number of locations included after filtering
print(f"Included locations after filtering: {included_locations_count}")

# Save the map to an HTML file
m.save(f'{map_file_drop_folder}/restaurant_map.html')
print(f"Map saved to {map_file_drop_folder}")
