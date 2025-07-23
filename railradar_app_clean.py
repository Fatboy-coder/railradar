# === RailRadar App ===
# Application Streamlit pour signaler les galères ferroviaires, avec sauvegarde dans Google Sheets

import streamlit as st
import pandas as pd
import datetime
import pytz
import pydeck as pdk
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import requests
import time
import folium
from streamlit_folium import st_folium

if st.sidebar.checkbox("Carte des incidents"):
    st.subheader("📍 Visualisation géographique des incidents")

    # Rechargement des données en direct
    data = sheet.get_all_records()

    map_center = [48.8566, 2.3522]  # Paris
    m = folium.Map(location=map_center, zoom_start=6)

    for row in data:
        nom_lieu = row.get("gare") or row.get("lieu") or row.get("ville")
        if nom_lieu:
            lat, lon = get_coordinates(nom_lieu)
            if lat and lon:
                popup = f"""
                <b>{nom_lieu}</b><br>
                Ligne : {row.get('ligne')}<br>
                Type : {row.get('type')}<br>
                Heure : {row.get('heure')}<br>
                Commentaire : {row.get('commentaire', '')}
                """
                folium.Marker(
                    [lat, lon],
                    popup=popup,
                    icon=folium.Icon(color="red", icon="train", prefix="fa")
                ).add_to(m)

    st_data = st_folium(m, width=700, height=500)

# === CONNEXION AU GOOGLE SHEET ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
service_account_info = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1uzo113iwwEPQcv3SNSP4e0MvubpPItQANdU0k9zeW6s").sheet1

# Connexion à la feuille "cache_geoloc"
cache_sheet = client.open_by_key("1uzo113iwwEPQcv3SNSP4e0MvubpPItQANdU0k9zeW6s").worksheet("cache_geoloc")

# Fonction pour lire le cache
def read_cache():
    data = cache_sheet.get_all_records()
    return {row["nom_lieu"].lower(): (row["latitude"], row["longitude"]) for row in data}

# Fonction pour ajouter une ligne au cache
def append_to_cache(nom_lieu, lat, lon):
    cache_sheet.append_row([nom_lieu, lat, lon])

# Fonction de géocodage avec cache
def get_coordinates(nom_lieu):
    cache = read_cache()
    nom_clean = nom_lieu.strip().lower()
    
    if nom_clean in cache:
        return cache[nom_clean]
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": nom_lieu,
        "format": "json",
        "limit": 1
    }
    headers = {"User-Agent": "railradar-bot"}
    response = requests.get(url, params=params, headers=headers)
    time.sleep(1)  # Pause par respect des règles d'usage
    
    if response.status_code == 200 and response.json():
        lat = float(response.json()[0]["lat"])
        lon = float(response.json()[0]["lon"])
        append_to_cache(nom_lieu, lat, lon)
        return lat, lon
    else:
        return None, None

# === CONFIGURATION DE LA PAGE (avec logo et PWA) ===
st.set_page_config(
    page_title="RailRadar",
    page_icon="logo.png",  # Ton logo doit être présent dans le dossier
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Lien vers manifest.json et icône Apple (pour PWA)
st.markdown("""
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#32cd32">
    <link rel="apple-touch-icon" href="logo.png">
""", unsafe_allow_html=True)

# CSS responsive pour amélioration mobile
st.markdown("""
    <style>
    @media only screen and (max-width: 600px) {
        .css-1d391kg {padding: 1rem !important;}
        .css-1v0mbdj {padding-top: 0rem !important;}
    }
    </style>
""", unsafe_allow_html=True)

# === GESTION SESSION ===
if 'reports' not in st.session_state:
    st.session_state.reports = []

# === TITRE PRINCIPAL ===
st.title("🚆 RailRadar – Signale les galères, sauve des trajets")

# === FORMULAIRE DE SIGNALEMENT ===
st.header("Signaler un incident")

with st.form("report_form"):
    gare = st.text_input("Gare concernée")
    ligne = st.text_input("Ligne ou train (ex : RER A, TGV 8471)")
    type_incident = st.selectbox("Type d'incident", [
        "Retard", "Suppression", "Fermeture", "Train bondé", "Autre"
    ])
    commentaire = st.text_area("Commentaire (optionnel)")
    envoyer = st.form_submit_button("Envoyer le signalement")

    if envoyer and gare and ligne:
        now = datetime.datetime.now(pytz.timezone("Europe/Paris"))

        # Enregistrement local
        st.session_state.reports.append({
            "heure": now.strftime("%H:%M"),
            "gare": gare.strip().title(),
            "ligne": ligne.strip().upper(),
            "type": type_incident,
            "commentaire": commentaire.strip()
        })

        # Enregistrement Google Sheets
        sheet.append_row([
            now.strftime("%H:%M"),
            gare.strip().title(),
            ligne.strip().upper(),
            type_incident,
            commentaire.strip()
        ])

        st.success("✅ Signalement enregistré. Merci !")

# === AFFICHAGE DES SIGNALEMENTS ===
st.header("Derniers signalements")

if st.session_state.reports:
    df = pd.DataFrame(st.session_state.reports[::-1])
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucun signalement pour l’instant. Sois le premier à aider les autres !")

# === CARTE INTERACTIVE ===
st.subheader("🗺 Carte des incidents signalés")

# Données fictives (à remplacer + tard par coordonnées live)
data = pd.DataFrame([
    {"gare": "Gare de Lyon", "lat": 48.844, "lon": 2.374, "incident": "Retard"},
    {"gare": "Montparnasse", "lat": 48.839, "lon": 2.319, "incident": "Surcharge"},
    {"gare": "Saint-Lazare", "lat": 48.876, "lon": 2.325, "incident": "Agression"}
])

st.pydeck_chart(pdk.Deck(
    initial_view_state=pdk.ViewState(latitude=48.85, longitude=2.35, zoom=10),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=data,
            get_position='[lon, lat]',
            get_fill_color='[200, 30, 0, 160]',
            get_radius=300,
        ),
    ],
))

with st.expander("Voir les incidents géolocalisés"):
    st.dataframe(data)

# === SIDEBAR ===
st.sidebar.header("Fonctionnalités à venir 🚧")
st.sidebar.markdown("- Carte interactive des gares signalées")
st.sidebar.markdown("- Notifications par ligne suivie")
st.sidebar.markdown("- Connexion API SNCF")
st.sidebar.markdown("- Système de fiabilité des usagers")
