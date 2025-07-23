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

# CSS responsive pour
