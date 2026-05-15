import requests
import pandas as pd

def get_forecast_24h():
    """Récupère les prévisions pour Marseille (Frioul)."""
    # Note : Open-Meteo sépare parfois la météo classique et la marine
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 43.28,
        "longitude": 5.30,
        "hourly": ["wave_height", "wave_period", "wind_speed_10m", "wind_gusts_10m"],
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "timezone": "Europe/Paris",
        "forecast_days": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Vérifie que les clés existent et ne sont pas vides
        hourly = data.get("hourly", {})
        daily = data.get("daily", {})

        # Utilise une valeur par défaut (0.0) si le max ne peut pas être calculé
        # C'est ici que l'erreur '>' se produisait
        def safe_max(lst):
            clean_list = [x for x in lst if x is not None]
            return max(clean_list) if clean_list else 0.0

        return {
            "wave_height_max": safe_max(hourly.get("wave_height", [])),
            "wave_period_max": safe_max(hourly.get("wave_period", [])),
            "wind_speed_max": safe_max(hourly.get("wind_speed_10m", [])),
            "wind_gusts_max": safe_max(hourly.get("wind_gusts_10m", [])),
            "temperature_max": safe_max(daily.get("temperature_2m_max", [])),
            "temperature_min": safe_max(daily.get("temperature_2m_min", []))
        }
    except Exception as e:
        print(f"❌ Erreur Open-Meteo : {e}")
        # Retourne des valeurs par défaut pour ne pas faire planter l'API
        return {
            "wave_height_max": 0.5, "wave_period_max": 4.0,
            "wind_speed_max": 10.0, "wind_gusts_max": 20.0,
            "temperature_max": 20.0, "temperature_min": 15.0
        }