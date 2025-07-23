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

import streamlit as st

# Optimisation mobile
st.set_page_config(
    page_title="RailRadar",
    layout="centered",  # ou "wide" selon ton design
    initial_sidebar_state="collapsed"
)

# Astuce CSS pour améliorer le rendu sur mobile
st.markdown("""
    <style>
    @media only screen and (max-width: 600px) {
        .css-1d391kg {padding: 1rem !important;}
        .css-1v0mbdj {padding-top: 0rem !important;}
    }
    </style>
""", unsafe_allow_html=True)

# === CONNEXION AU GOOGLE SHEET ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
service_account_info = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1uzo113iwwEPQcv3SNSP4e0MvubpPItQANdU0k9zeW6s").sheet1

# === CONFIG STREAMLIT ===
st.set_page_config(page_title="RailRadar", layout="centered")

if 'reports' not in st.session_state:
    st.session_state.reports = []

# === TITRE PRINCIPAL ===
st.title("RailRadar – Signale les galères, sauve des trajets")

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

        # Enregistrement local (session)
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

        st.success("Signalement enregistré. Merci !")

# === AFFICHAGE DES SIGNALEMENTS ===
st.header("Derniers signalements")

if st.session_state.reports:
    df = pd.DataFrame(st.session_state.reports[::-1])
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucun signalement pour l’instant. Sois le premier à aider les autres !")

# === CARTE INTERACTIVE DES INCIDENTS ===
st.subheader("🗺 Carte des incidents signalés")

# Données fictives (remplaçables plus tard par des vraies coordonnées)
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
st.sidebar.header("En cours de développement")
st.sidebar.markdown("- Carte interactive des gares signalées")
st.sidebar.markdown("- Notifications par ligne suivie")
st.sidebar.markdown("- Connexion API SNCF")
st.sidebar.markdown("- Système de fiabilité des usagers")
