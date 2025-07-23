# railradar_app_clean.py

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import json

with open("traces-des-lignes-de-transport-en-commun-idfm.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# -------------------------------
# 🔐 AUTHENTIFICATION GOOGLE SHEETS
# -------------------------------
service_account_info = st.secrets["google_service_account"]
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)

# 📄 Connexion aux feuilles
spreadsheet = client.open_by_key("1uzo113iwwEPQcv3SNSP4e0MvubpPItQANdU0k9zeW6s")
sheet = spreadsheet.sheet1

# 🗂️ Feuille cache géolocalisation
try:
    cache_sheet = spreadsheet.worksheet("cache_geoloc")
except:
    cache_sheet = spreadsheet.add_worksheet(title="cache_geoloc", rows="100", cols="3")
    cache_sheet.append_row(["lieu", "lat", "lon"])

# -------------------------------------
# 📍 GEOCODING AVEC CACHE LOCAL EN SHEETS
# -------------------------------------
def geocode_with_cache(lieu):
    cache = {row[0]: (row[1], row[2]) for row in cache_sheet.get_all_values()[1:]}
    if lieu in cache:
        try:
            lat = float(cache[lieu][0])
            lon = float(cache[lieu][1])
            return lat, lon
        except ValueError:
            st.warning(f"⚠️ Coordonnées invalides pour le lieu '{lieu}' dans le cache.")
            return None, None

    # Géocodage si pas dans le cache
    geolocator = Nominatim(user_agent="railradar")
    try:
        location = geolocator.geocode(lieu)
        if location:
            cache_sheet.append_row([lieu, location.latitude, location.longitude])
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        time.sleep(1)
        return geocode_with_cache(lieu)

    return None, None

# -------------------------------
# 🎨 INTERFACE STREAMLIT
# -------------------------------
st.set_page_config(page_title="RailRadar", layout="wide")
st.title("🚆 RailRadar – Signalements collaboratifs")
menu = st.sidebar.radio("Navigation", ["📩 Signaler", "🗺️ Carte des incidents"])

if menu == "📩 Signaler":
    st.subheader("Signale un incident ou une anomalie")
    with st.form("incident_form"):
        lieu = st.text_input("📍 Gare ou station concernée")
        type_incident = st.selectbox(
            "🚧 Type d'incident",
            ["Retard", "Suppression", "Grève", "Travaux", "Fermeture", "Autre"]
        )
        commentaire = st.text_area("✏️ Commentaire")
        envoyer = st.form_submit_button("Envoyer")

        if envoyer and lieu:
            now = datetime.datetime.now(pytz.timezone("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([now, lieu, type_incident, commentaire])
            st.success("✅ Signalement transmis ! Merci 🙌")

elif menu == "🗺️ Carte des incidents":
    st.subheader("📍 Visualisation géographique des incidents")
    mapbox_token = st.secrets["MAPBOX_TOKEN"]
    data = sheet.get_all_records()

    m = folium.Map(location=[48.8566, 2.3522], zoom_start=11, tiles=None)

    folium.TileLayer(
        tiles=f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{{z}}/{{x}}/{{y}}?access_token={mapbox_token}",
        attr='Mapbox',
        name='Mapbox Streets',
        overlay=True,
        control=True
    ).add_to(m)

    for row in data:
        lieu = row["lieu"]
        lat, lon = geocode_with_cache(lieu)
        if lat and lon:
            popup = f"<b>{lieu}</b><br>{row['type_incident']}<br>{row['commentaire']}"
            folium.Marker(location=[lat, lon], popup=popup).add_to(m)

    st_folium(m, width=1000, height=600)
