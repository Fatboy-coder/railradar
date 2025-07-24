# === IMPORTS DES MODULES ===
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.distance import geodesic
import time
import json

# === CHARGEMENT DES FICHIERS GEOJSON IDFM ===
with open("traces-des-lignes-de-transport-en-commun-idfm.geojson", "r", encoding="utf-8") as f:
    lignes_geojson = json.load(f)

with open("emplacement-des-gares-idf.geojson", "r", encoding="utf-8") as f:
    gares_geojson = json.load(f)

# === ORGANISATION DES DONNÉES DES GARES ===
gares_par_mode = {}
gares_coords = {}

for feature in gares_geojson["features"]:
    nom = feature["properties"].get("nom_long")
    mode = feature["properties"].get("mode_")
    lignes = feature["properties"].get("code_ligne")
    coords = feature["geometry"]["coordinates"][::-1]
    if nom and mode:
        gares_par_mode.setdefault(mode.upper(), []).append(nom)
        gares_coords[nom] = {
            "mode": mode.upper(),
            "lignes": lignes,
            "coords": coords
        }

# === FONCTION DE STYLISATION DES LIGNES ===
def style_ligne(feature):
    mode = feature["properties"].get("mode")
    couleur = {
        "metro": "#FFCD00",
        "rer": "#0055A4",
        "tram": "#82C91E",
        "bus": "#E03C31"
    }.get(mode, "#666666")
    return {"color": couleur, "weight": 3, "opacity": 0.8}

# === AUTHENTIFICATION GOOGLE SHEETS ===
service_account_info = st.secrets["google_service_account"]
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key("1uzo113iwwEPQcv3SNSP4e0MvubpPItQANdU0k9zeW6s")
sheet = spreadsheet.sheet1

try:
    cache_sheet = spreadsheet.worksheet("cache_geoloc")
except:
    cache_sheet = spreadsheet.add_worksheet(title="cache_geoloc", rows="100", cols="3")
    cache_sheet.append_row(["lieu", "lat", "lon"])

# === GÉOCODAGE AVEC MÉMORISATION DES COORDONNÉES ===
def geocode_with_cache(lieu):
    cache = {row[0]: (row[1], row[2]) for row in cache_sheet.get_all_values()[1:]}
    if lieu in cache:
        try:
            return float(cache[lieu][0]), float(cache[lieu][1])
        except ValueError:
            st.warning(f"⚠️ Coordonnées invalides pour le lieu '{lieu}' dans le cache.")
            return None, None
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

# === DÉTECTION DE LA GARE LA PLUS PROCHE ===
def plus_proche(lat, lon):
    min_gare, min_dist = None, float("inf")
    for nom, info in gares_coords.items():
        dist = geodesic((lat, lon), info["coords"]).km
        if dist < min_dist:
            min_gare, min_dist = nom, dist
    return min_gare, round(min_dist, 2)

# === INTERFACE STREAMLIT ===
st.set_page_config(page_title="RailRadar", layout="wide")
st.title("🚆 RailRadar – Signalements collaboratifs")
menu = st.sidebar.radio("Navigation", ["📩 Signaler", "🗺️ Carte des incidents"])

# === FORMULAIRE DE SIGNALEMENT ===
if menu == "📩 Signaler":
    st.subheader("Signale un incident ou une anomalie")

    use_gps = st.checkbox("📡 Détecter ma gare la plus proche")
    if use_gps:
        user_lat = st.number_input("Latitude", value=48.8566)
        user_lon = st.number_input("Longitude", value=2.3522)
        gare_proche, distance = plus_proche(user_lat, user_lon)
        st.success(f"La gare la plus proche est **{gare_proche}** ({distance} km)")

    with st.form("incident_form"):
        selected_mode = st.selectbox("🚇 Mode de transport", sorted(gares_par_mode.keys()))
        gare_options = sorted(gares_par_mode[selected_mode])
        lieu = st.selectbox("📍 Gare ou station concernée", gare_options)

        if lieu in gares_coords:
            lignes = gares_coords[lieu]["lignes"]
            st.markdown(f"**Correspondance(s)** : {lignes}")

        type_incident = st.selectbox("🚧 Type d'incident", ["Retard", "Suppression", "Grève", "Travaux", "Fermeture", "Autre"])
        commentaire = st.text_area("✏️ Commentaire")
        envoyer = st.form_submit_button("Envoyer")

        if envoyer and lieu:
            now = datetime.datetime.now(pytz.timezone("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([now, lieu, type_incident, commentaire])
            st.success("✅ Signalement transmis ! Merci 🙌")

# === CARTE DES INCIDENTS ===
elif menu == "🗺️ Carte des incidents":
    st.subheader("📍 Visualisation géographique des incidents")
    mapbox_token = st.secrets["MAPBOX_TOKEN"]
    data = sheet.get_all_records()

    m = folium.Map(location=[48.8566, 2.3522], zoom_start=11, tiles=None)

    folium.TileLayer(
        tiles=f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{{z}}/{{x}}/{{y}}?access_token={mapbox_token}",
        attr='Mapbox',
        name='Mapbox Streets'
    ).add_to(m)

    # Ajout des champs requis au GeoJSON
    def get_geojson_fields(geojson):
        if not geojson.get("features"):
            return []
        feature_props = geojson["features"][0].get("properties", {})
        valid_keys = ["code_ligne", "nom", "mode"]
        return [key for key in valid_keys if key in feature_props]

    for feat in lignes_geojson["features"]:
        props = feat.get("properties", {})
        for field in ["code_ligne", "nom", "mode"]:
            if field not in props:
                props[field] = "N/A"

    folium.GeoJson(
        lignes_geojson,
        name="Lignes IDFM",
        style_function=style_ligne,
        tooltip=folium.GeoJsonTooltip(
            fields=["code_ligne", "nom", "mode"],
            aliases=["Ligne", "Nom", "Mode"],
            sticky=True
        )
    ).add_to(m)

    # Ajout des incidents sur la carte
    for row in data:
        lieu = row.get("lieu")
        if lieu:
            lat, lon = geocode_with_cache(lieu)
            if lat and lon:
                popup = f"<b>{lieu}</b><br>{row.get('type_incident','')}<br>{row.get('commentaire','')}"
                folium.Marker(location=[lat, lon], popup=popup).add_to(m)

    # Légende personnalisée
    legend_html = """
    <div style='position: fixed; bottom: 50px; left: 50
    
