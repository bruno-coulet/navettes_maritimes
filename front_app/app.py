"""Streamlit frontend for the navettes maritime prediction API."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000/predict")


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


st.set_page_config(page_title="Navettes Maritimes", page_icon="🚢", layout="centered")

st.title("Navettes Maritimes")
st.caption("Frontend Streamlit pour interroger l'API FastAPI de prédiction.")

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
    payload: dict[str, Any] = _default_payload()

    col1, col2 = st.columns(2)
    with col1:
        payload["wave_height_max"] = _field("Hauteur max des vagues", "wave_height_max", "mètres")
        payload["wave_period_max"] = _field("Période max des vagues", "wave_period_max", "secondes")
        payload["swell_wave_height_max"] = _field("Hauteur max de houle", "swell_wave_height_max", "mètres")
        payload["temperature_min"] = _field("Température min", "temperature_min", "°C")
        payload["wind_speed_max"] = _field("Vitesse max du vent", "wind_speed_max", "km/h")

    with col2:
        payload["wave_direction_dominant"] = _field("Direction dominante des vagues", "wave_direction_dominant", "degrés")
        payload["wind_wave_height_max"] = _field("Hauteur max des vagues de vent", "wind_wave_height_max", "mètres")
        payload["temperature_max"] = _field("Température max", "temperature_max", "°C")
        payload["wind_gusts_max"] = _field("Rafales max", "wind_gusts_max", "km/h")
        payload["wind_direction_dominant"] = _field("Direction dominante du vent", "wind_direction_dominant", "degrés")

    submitted = st.form_submit_button("Prédire")

if submitted:
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        st.success("Prédiction obtenue")
        st.metric("Probabilité d'annulation", f"{result['annulation_probability']:.2%}")
        st.metric("Annulation prédite", "Oui" if result["annulation_predicted"] else "Non")
        st.metric("Confiance", f"{result['confidence']:.2%}")
        st.json(result)
    except Exception as exc:  # pragma: no cover - UI feedback
        st.error(f"Erreur de prédiction: {exc}")
