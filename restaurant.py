import streamlit as st
import requests
from requests.structures import CaseInsensitiveDict
import pandas as pd
import gdown
import folium
from streamlit.components.v1 import html

# Function to download the CSV from Google Drive
@st.cache_data
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
            },
            (error) => {
                document.getElementById("geo-data").innerHTML = "Error: Unable to fetch location.";
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

# Input for the user to copy the geolocation data
coords = st.text_input("Enter your coordinates (latitude,longitude):")

if coords:
    try:
        lat, lon = map(float, coords.split(","))
        st.success(f"Detected Location: (Latitude: {lat}, Longitude: {lon})")
        
        # Use Geoapify Places API to fetch restaurant recommendations
        @st.cache_data
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
                        "lat": place["properties"]["lat"],
                        "lon": place["properties"]["lon"]
                    }
                    for place in restaurants
                ]
                return restaurant_list
            else:
                st.error("Failed to retrieve restaurant data.")
                return []

        # Get restaurant recommendations based on the exact location
        st.header("Nearby Restaurant Recommendations:")
        with st.spinner('Fetching recommendations...'):
            restaurants = get_restaurant_recommendations(lat, lon)

        # Show recommendations on map
        if restaurants:
            m = folium.Map(location=[lat, lon], zoom_start=13)
            for restaurant in restaurants:
                folium.Marker(
                    [restaurant['lat'], restaurant['lon']],
                    popup=f"{restaurant['name']} - {restaurant['address']}"
                ).add_to(m)
            # Display the map directly with _repr_html_()
            folium_map = m._repr_html_()
            html(folium_map, height=500)
            
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
    except ValueError:
        st.error("Invalid coordinates format. Please enter in 'latitude,longitude' format.")
else:
    st.info("Waiting for coordinates...")

