
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import requests
import time
import folium
from streamlit_folium import st_folium

# -----------------------------
# CONFIGURATION & AUTH
# -----------------------------
st.set_page_config(page_title="RailRadar", page_icon="🚆", layout="wide")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
service_account_info = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)

# Feuilles Google Sheets
sheet = client.open_by_key("1uzo113iwwEPQcv3SNSP4e0MvubpPItQANdU0k9zeW6s").sheet1
cache_sheet = client.open_by_key("1uzo113iwwEPQcv3SNSP4e0MvubpPItQANdU0k9zeW6s").worksheet("cache_geoloc")

# -----------------------------
# FONCTIONS GÉOLOCALISATION
# -----------------------------
def read_cache():
    data = cache_sheet.get_all_records()
    return {row["nom_lieu"].strip().lower(): (row["latitude"], row["longitude"]) for row in data}

def append_to_cache(nom_lieu, lat, lon):
    cache_sheet.append_row([nom_lieu, lat, lon])

def get_coordinates(nom_lieu):
    cache = read_cache()
    nom_clean = nom_lieu.strip().lower()

    if nom_clean in cache:
        return cache[nom_clean]

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": nom_lieu, "format": "json", "limit": 1}
    headers = {"User-Agent": "railradar-bot"}
    response = requests.get(url, params=params, headers=headers)
    time.sleep(1)

    if response.status_code == 200 and response.json():
        lat = float(response.json()[0]["lat"])
        lon = float(response.json()[0]["lon"])
        append_to_cache(nom_lieu, lat, lon)
        return lat, lon
    else:
        return None, None

# -----------------------------
# INTERFACE PRINCIPALE
# -----------------------------
st.title("🚆 RailRadar")
st.markdown("Signale ou consulte les perturbations ferroviaires en temps réel.")

with st.form("incident_form"):
    nom = st.text_input("Ton prénom (optionnel)")
    ligne = st.text_input("Ligne ou train concerné (ex: RER A, TGV 8471)")
    lieu = st.text_input("Nom de la gare ou station")
    incident = st.selectbox("Type d'incident", ["Retard", "Suppression", "Accident", "Autre"])
    commentaire = st.text_area("Commentaire (facultatif)")
    submitted = st.form_submit_button("📤 Envoyer")

    if submitted and ligne and lieu and incident:
        now = datetime.datetime.now(pytz.timezone("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([nom, ligne, lieu, incident, commentaire, now])
        st.success("✅ Signalement transmis !")

# -----------------------------
# VISUALISATION DES DONNÉES
# -----------------------------
with st.expander("📄 Voir les signalements récents"):
    records = sheet.get_all_records()
    st.write(records)

# -----------------------------
# CARTE DES INCIDENTS
# -----------------------------
if st.sidebar.checkbox("🗺️ Carte des incidents"):
    st.subheader("📍 Visualisation géographique des incidents")
    data = sheet.get_all_records()
    m = folium.Map(
    location=[48.8566, 2.3522],
    zoom_start=11,
    tiles=None
)

folium.TileLayer(
    tiles="https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiMTNkZXZsYWIiLCJhIjoiY21kZzQ4Zmp3MGwxOTJscTNiZnIzc2lldyJ9.7P8rf94P_eDORWkrgp_Ftw",
    attr='Mapbox',
    name='Mapbox Streets',
    overlay=True,
    control=True
).add_to(m)

    for row in data:
        nom_lieu = row.get("lieu") or row.get("gare") or row.get("ville")
        if nom_lieu:
            lat, lon = get_coordinates(nom_lieu)
            if lat and lon:
                popup = f"<b>{nom_lieu}</b><br>Ligne : {row.get('ligne')}<br>Type : {row.get('incident')}<br>Heure : {row.get('horodatage') or row.get('heure')}<br>Commentaire : {row.get('commentaire', '')}"
                folium.Marker([lat, lon], popup=popup, icon=folium.Icon(color="red")).add_to(m)

    st_data = st_folium(m, width=700, height=500)
