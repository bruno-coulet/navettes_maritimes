"""Frontend Streamlit pour l'API de prédiction d'annulation de navettes maritimes."""

from __future__ import annotations
import os
import requests
import streamlit as st
from typing import Any
from pathlib import Path
import pandas as pd

# Dossier où se trouve app.py
CURRENT_DIR = Path(__file__).parent
IMAGE_PATH = CURRENT_DIR / "img" / "lebateau.jpg"
API_URL = os.getenv("API_URL", "http://localhost:8000/predict")

st.title("Navettes Maritimes")
st.set_page_config(page_title="Navettes Maritimes V3", page_icon="🚢", layout="wide")
if IMAGE_PATH.exists():
    st.image(str(IMAGE_PATH))
else:
    st.warning(f"Image non trouvée à l'emplacement : {IMAGE_PATH}")


# couleur de bouton #E76B42
# couleur de texte #393D46
# couleur pour les alertes critiques #E30510

# Listes issues des features V3 (nettoyées des préfixes pour l'UI)
CAPITAINES = ["0cb84352", "0d121578", "14082eb5", "1509f9cf", "1718b47d", "185e82ca", "1b34dcd4", "1cf4a8b5", "1ed3875f", "23d15265", "2caaceac", "33603a19", "357c3e95", "37852178", "3954bf2d", "39af1330", "3a85997b", "3cb5e71c", "3da84ea0", "3e528ded", "44df863c", "4a43010f", "4db5823d", "4ea37f6d", "52e2838f", "5ba1d311", "60f35e90", "633ee2cc", "67eee8d4", "6decabc9", "6e2e1ed7", "781ea93a", "7f2a897b", "87eb49a2", "8843e5b9", "8b638b7c", "9c91e0cb", "9e6fdb63", "a060d80f", "a6ab9a79", "a6edc93d", "ab0aaf45", "ace2ff49", "ad6931e3", "b5826588", "bdd4013b", "c1263f83", "c27be312", "c35d80c4", "c563db71", "c9970e45", "cb2c3739", "cf9d1f29", "d0f033d5", "d27338fd", "d5df07d7", "d74108d2", "d7f002ce", "daffbea6", "e212f1aa", "e6fffe58", "ea2bcbe6", "ef7af6bd", "f1446137", "f2d105cb", "f32c6167", "f74faffe", "fc3f7e33", "fcb64262", "fd07cd3b"]
BATEAUX = ["Chevalier Paul", "Cisampo", "EDantes", "HJEsperandieu", "Hélios", "Lydie13", "Planier", "Pomègues", "Ratonneau", "Revellata 1", "San Antonio X", "Thalassa 7", "Îles d'or XV"]
LIGNES = ["Frioul-IF", "Frioul-Vieux Port", "Goudes-Pointe Rouge", "IF-Frioul", "IF-Vieux Port", "Pointe Rouge-Goudes", "Pointe Rouge-Vieux Port", "Vieux Port-Estaque", "Vieux Port-Frioul", "Vieux Port-IF", "Vieux Port-Pointe Rouge"]
DIRECTIONS_VENT = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _default_payload() -> dict[str, float | None]:
    return {
        "wave_height_max": None,
        "wave_direction_dominant": None,
        "wave_period_max": None,
        "wind_wave_height_max": None,
        "swell_wave_height_max": None,
        "temperature_max": None,
        "temperature_min": None,
        "wind_speed_max": None,
        "wind_gusts_max": None,
        "wind_direction_dominant": None,
    }

def _field(number_label: str, key: str, help_text: str, default: float = 0.0) -> float:
    return st.number_input(number_label, value=default, help=help_text, key=key)

def get_forecast_24h():
    """Récupère les prévisions pour Marseille (Frioul)."""

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 43.28,
        "longitude": 5.30,
        "hourly": ["wave_height", "wave_period", "wind_speed_10m", "wind_gusts_10m"],
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "timezone": "Europe/Paris",
        "forecast_days": 1
    }

    st.write(f"DEBUG: Appel de l'URL : {TOMORROW_URL}")
    response = requests.get(url, params=params)
    data = response.json()

    # On agrège pour obtenir les 'max' du lendemain
    return {
        "wave_height_max": max(data["hourly"]["wave_height"]),
        "wave_period_max": max(data["hourly"]["wave_period"]),
        "wind_speed_max": max(data["hourly"]["wind_speed_10m"]),
        "wind_gusts_max": max(data["hourly"]["wind_gusts_10m"]),
        "temperature_max": data["daily"]["temperature_2m_max"][0],
        "temperature_min": data["daily"]["temperature_2m_min"][0]
    }



# st.info("Ce modèle combine les données météo et les facteurs métiers (Capitaine/Bateau).")
st.set_page_config(page_title="Navettes Maritimes", page_icon="🚢", layout="centered")
st.divider()
st.subheader("Prévision météo pour demain")

if st.button("🗓️ Générer le bulletin météo"):
    with st.spinner("Récupération de la météo et calcul des risques..."):
        try:
            # On appelle notre nouvelle route API
            TOMORROW_URL = API_URL.replace("/predict", "/predict/tomorrow")
            res = requests.get(TOMORROW_URL)

            if res.status_code == 200:
                data = res.json()
                meteo = data["details_meteo"]
                bulletin = data["bulletin"]

                # 1. Affichage des conditions météo prévues
                st.info(f"**Météo prévue (Marseille/Frioul) :** \n"
                        f"🌊 Vagues : {meteo['wave_height_max']}m | "
                        f"💨 Vent : {meteo['wind_speed_max']}km/h (Rafales : {meteo['wind_gusts_max']}km/h) | "
                        f"🌡️ Temp : {meteo['temperature_min']}°C à {meteo['temperature_max']}°C")

                # 2. Construction d'un tableau propre pour le bulletin
                # On transforme la liste en DataFrame pour un bel affichage
                import pandas as pd
                df_bulletin = pd.DataFrame(bulletin)

                # On renomme les colonnes pour l'utilisateur
                df_bulletin.columns = ["Ligne", "Risque d'annulation", "Statut"]

                # Formatage des pourcentages
                df_bulletin["Risque d'annulation"] = df_bulletin["Risque d'annulation"].apply(lambda x: f"{x:.1%}")

                # Affichage du tableau
                st.table(df_bulletin)

                st.caption("Note : Calcul basé sur le bateau 'Ratonneau' et le capitaine par défaut.")
            else:
                st.error("Impossible de récupérer le bulletin automatique.")

        except Exception as e:
            st.error(f"Erreur lors de la génération du bulletin : {e}")

with st.sidebar:
    st.header("Configuration")
    st.write(f"API: {API_URL}")
    if st.button("Tester la santé de l'API"):
        try:
            health_url = API_URL.replace("/predict", "/health")
            response = requests.get(health_url, timeout=10)
            response.raise_for_status()
            st.success(response.json())
        except Exception as exc:  # pragma: no cover - UI feedback
            st.error(f"API indisponible: {exc}")

st.subheader("Données météo")

with st.form("prediction_form"):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚢 Exploitation")
        capitaine = st.selectbox("Capitaine", CAPITAINES)
        bateau = st.selectbox("Bateau", BATEAUX)
        ligne = st.selectbox("Ligne", LIGNES)

    with col2:
        st.subheader("🌦️ Conditions Météo")
        wind_s = st.number_input("Vitesse Vent (km/h)", value=15.0)
        wind_g = st.number_input("Rafales (km/h)", value=25.0)
        wind_orientation = st.selectbox("Orientation (Rose des vents)", DIRECTIONS_VENT, index=14) # NW par défaut
        wind_deg = st.number_input("Direction précise (Degrés)", value=290)

    st.divider()

    st.subheader("🌊 État de la Mer")
    sea1, sea2 = st.columns(2)
    with sea1:
        wave_h = st.number_input("Hauteur max Vagues (m)", value=0.5, step=0.1, max_value=5.0)
        wave_p = st.number_input("Période Vagues (s)", value=4.0, step=0.5)

    with sea2:
        wave_dir = st.number_input("Direction de la houle (Degrés)", value=270)

    submitted = st.form_submit_button("Calculer la probabilité d'annulation ou de maintien")

    if submitted:
        # Construction du payload pour l'API
        # On envoie les valeurs brutes, le backend (FastAPI) s'occupera du One-Hot Encoding
        payload = {
            "wave_height_max": wave_h,
            "wave_period_max": wave_p,
            "wave_direction_dominant": float(wave_dir),
            # "temperature_max": temp_max,
            # "temperature_min": temp_min,
            "wind_speed_max": wind_s,
            "wind_gusts_max": wind_g,
            "wind_direction_dominant": float(wind_deg),
            "Capitaine": capitaine,
            "Bateau": bateau,
            "Ligne": ligne,
            "Vent_Orientation": wind_orientation
        }

        try:
            res = requests.post(API_URL, json=payload)

            if res.status_code == 200:
                data = res.json()
                prob_annulation = data["annulation_probability"]
                prob_maintien = 1 - prob_annulation

                st.divider() # Petite ligne de séparation pour la clarté

                if prob_annulation > 0.5:
                    st.error(f"⚠️ RISQUE D'ANNULATION : {prob_annulation:.1%}")
                    st.progress(prob_annulation)
                else:
                    st.success(f"✅ DÉPART PROBABLE : {prob_maintien:.1%}")
                    st.progress(prob_maintien)
                    st.write(f"Le modèle est confiant à {prob_maintien:.1%} sur le maintien de la desserte.")

                # Détail technique discret en bas
                with st.expander("Détails techniques"):
                    st.json(data)

            else:
                    st.error(f"Erreur API : {res.text}")
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")
