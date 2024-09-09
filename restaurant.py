import folium
import streamlit as st
import requests
from requests.structures import CaseInsensitiveDict
import pandas as pd
import gdown

from streamlit_folium import st_folium

# Function to download the CSV from Google Drive
@st.cache
def download_data_from_drive():
    # Google Drive link for the dataset (convert to direct download link)
    url = 'https://drive.google.com/uc?id=1Tc3Hequ5jVjamAfuPhpBv8JvsOp7LSJY'
    output = 'restaurant_reviews.csv'
    
    # Download the file without printing progress (quiet=True)
    gdown.download(url, output, quiet=True)
    
    # Load the dataset
    return pd.read_csv(output)

# Load the dataset of restaurant reviews
reviews_df = download_data_from_drive()

# Geoapify API keys
GEOAPIFY_API_KEY = "1b8f2a07690b4cde9b94e68770914821"

# JavaScript code to get browser's geolocation
def get_geolocation():
    geolocation_code = """
        <script>
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                document.getElementById("geo-data").innerHTML = latitude + "," + longitude;
            }
        );
        </script>
        <p id="geo-data">Waiting for geolocation...</p>
    """
    return geolocation_code

# Display JavaScript code in Streamlit
st.title("Restaurant Recommendation System")

# Show geolocation script
st.markdown(get_geolocation(), unsafe_allow_html=True)

# Input for the user to copy the geolocation data (or you can handle it via JavaScript events)
coords = st.text_input("Enter your coordinates (latitude,longitude):")
# center on Liberty Bell, add marker
m = folium.Map(location=[39.949610, -75.150282], zoom_start=16)
folium.Marker(
    [39.949610, -75.150282], popup="Liberty Bell", tooltip="Liberty Bell"
).add_to(m)

# call to render Folium map in Streamlit
st_data = st_folium(m, width=725)

if coords:
    lat, lon = map(float, coords.split(","))
    st.write(f"Detected Location: (Latitude: {lat}, Longitude: {lon})")
    
    # Use Geoapify Places API to fetch restaurant recommendations
    def get_restaurant_recommendations(lat, lon):
        url = f"https://api.geoapify.com/v2/places?categories=catering.restaurant&filter=circle:{lon},{lat},5000&limit=10&apiKey={GEOAPIFY_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            restaurants = data["features"]
            restaurant_list = [
                {
                    "name": place["properties"].get("name", "Unknown name"),
                    "address": place["properties"].get("formatted", "No address available"),
                    "category": place["properties"]["categories"][0]
                }
                for place in restaurants
            ]
            return restaurant_list
        else:
            st.error("Failed to retrieve restaurant data.")
            return []

    # Get restaurant recommendations based on the exact location
    st.header("Nearby Restaurant Recommendations:")
    restaurants = get_restaurant_recommendations(lat, lon)

    if restaurants:
        for restaurant in restaurants:
            st.write(f"**{restaurant['name']}**")
            st.write(f"Address: {restaurant['address']}")
            st.write(f"Category: {restaurant['category']}")
            st.write("---")

            # Extract reviews for the recommended restaurant
            restaurant_reviews = reviews_df[reviews_df["Restaurant"].str.contains(restaurant['name'], case=False, na=False)]
            
            if not restaurant_reviews.empty:
                st.write("**Reviews:**")
                for _, review_row in restaurant_reviews.iterrows():
                    st.write(f"- {review_row['Review']} (Rating: {review_row['Rating']})")
            else:
                st.write("No reviews found.")
            st.write("---")
    else:
        st.write("No restaurants found nearby.")
else:
    st.write("Waiting for coordinates...")

