import streamlit as st
import requests
import pandas as pd
import gdown
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

# Function to download the CSV from Google Drive
@st.cache_data
def download_data_from_drive():
    url = 'https://drive.google.com/uc?id=1Tc3Hequ5jVjamAfuPhpBv8JvsOp7LSJY'
    output = 'restaurant_reviews.csv'
    gdown.download(url, output, quiet=True)
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
                    "category": place["properties"]["categories"][0],
                    "latitude": place["geometry"]["coordinates"][1],
                    "longitude": place["geometry"]["coordinates"][0]
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

    # Create a Folium map centered around the user's location
    m = folium.Map(location=[lat, lon], zoom_start=15)

    # Add marker for the user's location
    folium.Marker(
        location=[lat, lon],
        popup="Your Location",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

    if restaurants:
        # Add markers for recommended restaurants
        for restaurant in restaurants:
            folium.Marker(
                location=[restaurant["latitude"], restaurant["longitude"]],
                popup=(
                    f"<b>{restaurant['name']}</b><br>"
                    f"Address: {restaurant['address']}<br>"
                    f"Category: {restaurant['category']}"
                ),
                icon=folium.Icon(color="blue", icon="cloud")
            ).add_to(m)

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
    
    # Display the map in Streamlit using streamlit_folium
    try:
        st_folium(m, width=725)
    except Exception as e:
        st.error(f"Error displaying map: {e}")
        # Fallback method if st_folium fails
        map_html = m._repr_html_()
        components.html(map_html, height=500)
else:
    st.write("Waiting for coordinates...")
