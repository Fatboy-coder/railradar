# RailRadar — Version Cloud

RailRadar est une application web légère conçue pour signaler rapidement les incidents (retards, suppressions, anomalies) sur les lignes de train en temps réel.

Cette version cloud permet à tout utilisateur de :

- Signaler un incident ferroviaire simplement
- Centraliser les données via Google Sheets
- Visualiser les gares et lignes impactées (carte à venir)
- Suivre l'évolution des incidents signalés

---

## 🚀 Déploiement sur Streamlit Cloud

1. **Forkez ou clonez** ce dépôt GitHub
2. Connectez-vous sur [Streamlit Cloud](https://share.streamlit.io/)
3. Cliquez sur **"Create app"** puis sélectionnez ce repo
4. Ciblez le fichier principal : `railradar_app_clean.py`
5. ⚙️ Ajoutez vos identifiants Google Sheets (service account) dans les *Secrets*

---

## 📦 Stack technique

- **Python** + **Streamlit**
- **Google Sheets API** (data storage)
- **OAuth2 via `gspread` + `oauth2client`**

---

## 📍Prochaines fonctionnalités

- Carte interactive des gares signalées
- Notifications intelligentes par ligne suivie
- Connexion API SNCF
- Système de fiabilité basé sur les retours des utilisateurs
