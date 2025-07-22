import streamlit as st
import pandas as pd
import datetime
import pytz

if 'reports' not in st.session_state:
    st.session_state.reports = []

st.set_page_config(page_title="RailRadar", layout="centered")
st.title("RailRadar – Signale les galères, sauve des trajets")

st.header("Signaler un incident")
with st.form("report_form"):
    gare = st.text_input("Gare concernée")
    ligne = st.text_input("Ligne ou train (ex : RER A, TGV 8471)")
    type_incident = st.selectbox("Type d'incident", ["Retard", "Suppression", "Fermeture", "Train bondé", "Autre"])
    commentaire = st.text_area("Commentaire (optionnel)")
    envoyer = st.form_submit_button("Envoyer le signalement")

    if envoyer and gare and ligne:
        now = datetime.datetime.now(pytz.timezone("Europe/Paris"))
        st.session_state.reports.append({
            "heure": now.strftime("%H:%M"),
            "gare": gare.strip().title(),
            "ligne": ligne.strip().upper(),
            "type": type_incident,
            "commentaire": commentaire.strip()
        })
        st.success("Signalement enregistré. Merci !")

st.header("Derniers signalements")
if st.session_state.reports:
    df = pd.DataFrame(st.session_state.reports[::-1])
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aucun signalement pour l’instant. Sois le premier à aider les autres !")

st.sidebar.header("En cours de développement")
st.sidebar.markdown("- Carte interactive des gares signalées")
st.sidebar.markdown("- Notifications par ligne suivie")
st.sidebar.markdown("- Connexion API SNCF")
st.sidebar.markdown("- Système de fiabilité des usagers")

import streamlit as st
import pandas as pd
import pydeck as pdk

st.subheader("🗺 Carte des incidents signalés")

# Exemple de données : à remplacer par tes vraies données
data = pd.DataFrame([
    {"gare": "Gare de Lyon", "lat": 48.844, "lon": 2.374, "incident": "Retard"},
    {"gare": "Montparnasse", "lat": 48.839, "lon": 2.319, "incident": "Surcharge"},
    {"gare": "Saint-Lazare", "lat": 48.876, "lon": 2.325, "incident": "Agression"}
])

# Affichage carte
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

# Optionnel : Affichage tableau
with st.expander("Voir les signalements"):
    st.dataframe(data)
