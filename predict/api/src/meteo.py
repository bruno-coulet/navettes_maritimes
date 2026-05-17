# import requests
# import pandas as pd

# def get_forecast_24h():
#     """Récupère les prévisions pour Marseille (Frioul)."""
#     # Note : Open-Meteo sépare parfois la météo classique et la marine
#     # url = "https://api.open-meteo.com/v1/forecast"
#     url = "https://api.open-meteo.com/v1/marine"
#     params = {
#         "latitude": 43.275,
#         "longitude": 5.325,
#         # "latitude": 43.28,
#         # "longitude": 5.30,
#         "hourly": ["wave_height", "wave_period", "wind_speed_10m", "wind_gusts_10m"],
#         "daily": ["temperature_2m_max", "temperature_2m_min"],
#         "timezone": "Europe/Paris",
#         "forecast_days": 1
#     }
    
#     try:
#         response = requests.get(url, params=params, timeout=10)
#         response.raise_for_status()
#         data = response.json()
        
#         # Vérifie que les clés existent et ne sont pas vides
#         hourly = data.get("hourly", {})
#         daily = data.get("daily", {})

#         # Utilise une valeur par défaut (0.0) si le max ne peut pas être calculé
#         # C'est ici que l'erreur '>' se produisait
#         def safe_max(lst):
#             clean_list = [x for x in lst if x is not None]
#             return max(clean_list) if clean_list else 0.0

#         return {
#             "wave_height_max": safe_max(hourly.get("wave_height", [])),
#             "wave_period_max": safe_max(hourly.get("wave_period", [])),
#             "wind_speed_max": safe_max(hourly.get("wind_speed_10m", [])),
#             "wind_gusts_max": safe_max(hourly.get("wind_gusts_10m", [])),
#             "temperature_max": safe_max(daily.get("temperature_2m_max", [])),
#             "temperature_min": safe_max(daily.get("temperature_2m_min", []))
#         }
#     except Exception as e:
#         print(f"❌ Erreur Open-Meteo : {e}")
#         # Retourne des valeurs par défaut pour ne pas faire planter l'API
#         return {
#             "wave_height_max": 0.5, "wave_period_max": 4.0,
#             "wind_speed_max": 10.0, "wind_gusts_max": 20.0,
#             "temperature_max": 20.0, "temperature_min": 15.0
#         }


import requests

# def get_forecast_24h():
#     """Récupère les prévisions pour Marseille (Frioul) en combinant l'API Marine et Forecast."""
#     lat, lon = 43.275, 5.325
#     timezone = "Europe/Paris"
#     forecast_days = 1

#     # Initialisation des dictionnaires pour stocker les blocs horaires et journaliers
#     marine_hourly = {}
#     forecast_hourly = {}
#     forecast_daily = {}

#     # --- 1. REQUÊTE COMMUNE : ENDPOINT MARINE (Vagues & Houle) ---
#     try:
#         marine_url = "https://api.open-meteo.com/v1/marine"
#         marine_params = {
#             "latitude": lat,
#             "longitude": lon,
#             "hourly": ["wave_height", "wave_period"],
#             "timezone": timezone,
#             "forecast_days": forecast_days
#         }
#         res_marine = requests.get(marine_url, params=marine_params, timeout=10)
#         res_marine.raise_for_status()
#         marine_hourly = res_marine.json().get("hourly", {})
#     except Exception as e:
#         print(f"⚠️ Alerte Open-Meteo Marine : {e}")

#     # --- 2. REQUÊTE COMMUNE : ENDPOINT FORECAST (Vent & Températures) ---
#     try:
#         forecast_url = "https://api.open-meteo.com/v1/forecast"
#         forecast_params = {
#             "latitude": lat,
#             "longitude": lon,
#             "hourly": ["wind_speed_10m", "wind_gusts_10m"],
#             "daily": ["temperature_2m_max", "temperature_2m_min"],
#             "timezone": timezone,
#             "forecast_days": forecast_days
#         }
#         res_forecast = requests.get(forecast_url, params=forecast_params, timeout=10)
#         res_forecast.raise_for_status()
#         forecast_data = res_forecast.json()
#         forecast_hourly = forecast_data.get("hourly", {})
#         forecast_daily = forecast_data.get("daily", {})
#     except Exception as e:
#         print(f"⚠️ Alerte Open-Meteo Forecast : {e}")

#     # Fonction de sécurité pour extraire la valeur maximale
#     def safe_max(lst):
#         clean_list = [x for x in lst if x is not None]
#         return max(clean_list) if clean_list else None

#     # Extraction des métriques
#     wave_height_max = safe_max(marine_hourly.get("wave_height", []))
#     wave_period_max = safe_max(marine_hourly.get("wave_period", []))
#     wind_speed_max = safe_max(forecast_hourly.get("wind_speed_10m", []))
#     wind_gusts_max = safe_max(forecast_hourly.get("wind_gusts_10m", []))
#     temperature_max = safe_max(forecast_daily.get("temperature_2m_max", []))
#     temperature_min = safe_max(forecast_daily.get("temperature_2m_min", []))

#     # Si TOUT a échoué (pas d'internet ou API en panne), on applique des fallbacks sains
#     if wave_height_max == 0.0 and wind_speed_max == 0.0:
#         print("❌ Erreur critique Open-Meteo : Utilisation des données de secours.")
#         return {
#             "wave_height_max": 0.5, "wave_period_max": 4.0,
#             "wind_speed_max": 10.0, "wind_gusts_max": 20.0,
#             "temperature_max": 20.0, "temperature_min": 15.0
#         }

#     return {
#         "wave_height_max": wave_height_max if wave_height_max is not None else 0.5,
#         "wave_period_max": wave_period_max if wave_period_max is not None else 4.0,
#         "wind_speed_max": wind_speed_max if wind_speed_max is not None else 10.0,
#         "wind_gusts_max": wind_gusts_max if wind_gusts_max is not None else 20.0,
#         "temperature_max": temperature_max if temperature_max is not None else 20.0,
#         "temperature_min": temperature_min if temperature_min is not None else 15.0
#     }


def get_forecast_24h():
    """Récupère les prévisions pour Marseille (Frioul) en combinant l'API Marine et Forecast."""
    lat, lon = 43.275, 5.325
    timezone = "Europe/Paris"
    forecast_days = 1

    marine_hourly = {}
    forecast_hourly = {}
    forecast_daily = {}

    # --- 1. ENDPOINT MARINE (Vagues & Houle) ---
    # Correction : On passe une chaîne de caractères séparée par une virgule
    try:
        marine_url = "https://api.open-meteo.com/v1/marine"
        marine_params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wave_height,wave_period",  # 👈 Correction ici
            "timezone": timezone,
            "forecast_days": forecast_days
        }
        res_marine = requests.get(marine_url, params=marine_params, timeout=10)
        res_marine.raise_for_status()
        marine_hourly = res_marine.json().get("hourly", {})
    except Exception as e:
        print(f"⚠️ Alerte Open-Meteo Marine : {e}")

    # --- 2. ENDPOINT FORECAST (Vent & Températures) ---
    # Correction : Idem, chaînes séparées par des virgules
    try:
        forecast_url = "https://api.open-meteo.com/v1/forecast"
        forecast_params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wind_speed_10m,wind_gusts_10m",  # 👈 Correction ici
            "daily": "temperature_2m_max,temperature_2m_min",  # 👈 Correction ici
            "timezone": timezone,
            "forecast_days": forecast_days
        }
        res_forecast = requests.get(forecast_url, params=forecast_params, timeout=10)
        res_forecast.raise_for_status()
        forecast_data = res_forecast.json()
        forecast_hourly = forecast_data.get("hourly", {})
        forecast_daily = forecast_data.get("daily", {})
    except Exception as e:
        print(f"⚠️ Alerte Open-Meteo Forecast : {e}")

    # Fonction de sécurité pour extraire la valeur maximale
    def safe_max(lst):
        clean_list = [x for x in lst if x is not None]
        return max(clean_list) if clean_list else None

    # Extraction des métriques
    wave_height_max = safe_max(marine_hourly.get("wave_height", []))
    wave_period_max = safe_max(marine_hourly.get("wave_period", []))
    wind_speed_max = safe_max(forecast_hourly.get("wind_speed_10m", []))
    wind_gusts_max = safe_max(forecast_hourly.get("wind_gusts_10m", []))
    temperature_max = safe_max(forecast_daily.get("temperature_2m_max", []))
    temperature_min = safe_max(forecast_daily.get("temperature_2m_min", []))

    # Si TOUT a échoué, fallbacks de secours
    if wave_height_max is None and wind_speed_max is None:
        print("❌ Erreur critique Open-Meteo : Utilisation des données de secours.")
        return {
            "wave_height_max": 0.5, "wave_period_max": 4.0,
            "wind_speed_max": 10.0, "wind_gusts_max": 20.0,
            "temperature_max": 20.0, "temperature_min": 15.0
        }

    return {
        "wave_height_max": wave_height_max if wave_height_max is not None else 0.5,
        "wave_period_max": wave_period_max if wave_period_max is not None else 4.0,
        "wind_speed_max": wind_speed_max if wind_speed_max is not None else 10.0,
        "wind_gusts_max": wind_gusts_max if wind_gusts_max is not None else 20.0,
        "temperature_max": temperature_max if temperature_max is not None else 20.0,
        "temperature_min": temperature_min if temperature_min is not None else 15.0
    }