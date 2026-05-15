"""Utilitaires de collecte et traitement des donnees meteo marine.

Responsabilite:
- recuperer les donnees quotidiennes via open_meteo
- construire des summaries journaliers exploitables pour le ML

Entrees:
- coordonnees geographiques, dates de collecte, options de sauvegarde

Sorties:
- DataFrames de donnees brutes ou fusionnees, et fichiers CSV/JSON selon la configuration

Commande:
- module utilitaire, importe par `src.collect` et `src.pipeline`
"""

"""
Utilitaires pour la collecte et traitement des données météo marine de Marseille

=== ARCHITECTURE ===

Ce module collecte les données quotidiennes de météo marine via des APIs publiques.

Sources de données:
1. open_meteo Marine API (UTILISÉ ✅)
   - Vagues: hauteur, direction, période
   - Houle vs vagues de vent
   - URL: https://marine-api.open_meteo.com/v1/marine
   - Avantages: Gratuit, pas d'auth, fiable

2. open_meteo ERA5 Archive (UTILISÉ ✅)
   - Température, vent, pression, humidité
   - Données de réanalyse (historique fiable)
   - URL: https://archive-api.open_meteo.com/v1/era5
   - Avantages: Gratuit, pas d'auth, complet

3. Météo-France API (NON UTILISÉ ❌)
   - Bulletins BMS (Bulletins Météo Marine)
   - Payant, authentification requise
   - Endpoints: Non documentés/instables
   - Status: Code legacy conservé pour référence

=== FLUX DE DONNÉES ===

1. collect_historical_data_batch()
   ├─ get_marine_weather_open_meteo() → Vagues
   └─ get_weather_data_open_meteo() → Météo générale

2. process_to_daily_summary()
   └─ Fusionne marine_data + weather_data

3. save_data()
   └─ Exporte en CSV (optionnellement JSON)

=== UTILISATION ===

from src.utils import MeteoMarineMarseille

client = MeteoMarineMarseille()
data = client.collect_historical_data_batch(start_date, end_date)
daily_df = client.process_to_daily_summary(data)
client.save_data(daily_df, start_date, end_date, save_json=False)
"""

import requests
import json
import os
import socket
from datetime import datetime, timedelta
import time
import pandas as pd
from pathlib import Path
from urllib.parse import urlparse


class MeteoMarineMarseille:
    """Client pour récupérer les données de météo marine de Marseille"""

    def __init__(
        self,
        proxies: dict[str, str] | None = None,
        timeout: int = 30,
        force_proxy: bool | None = False,
    ):
        self.open_meteo_base = "https://marine-api.open_meteo.com/v1"

        # Coordonnées de Marseille
        self.marseille_coords = {"lat": 43.2965, "lon": 5.3698}
        self.request_timeout = timeout
        self.force_proxy = force_proxy

        # If explicit proxies provided, respect them unless force_proxy is False
        if proxies is not None:
            if self.force_proxy is False:
                self.proxies = None
            else:
                self.proxies = proxies
        else:
            self.proxies = self._load_proxies_from_env_file(force_proxy=self.force_proxy)

        self.session = requests.Session()

        self.session.trust_env = False  # Ignore les variables d'environnement (Proxy/DNS système)
        self.session.proxies = {}        # Vide explicitement les proxies pour cette session

    def _load_proxies_from_env_file(self, force_proxy: bool | None = None) -> dict[str, str] | None:
        """Charge la configuration proxy depuis l'environnement ou le fichier .env local."""
        https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
        http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        all_proxy = os.getenv("ALL_PROXY") or os.getenv("all_proxy")

        if https_proxy or http_proxy or all_proxy:
            return self._build_proxies(http_proxy, https_proxy, all_proxy, force_proxy=force_proxy)

        env_file = Path(__file__).resolve().parents[1] / ".env"
        if not env_file.exists():
            return None

        file_values = self._read_env_file(env_file)
        return self._build_proxies(
            file_values.get("HTTP_PROXY"),
            file_values.get("HTTPS_PROXY"),
            file_values.get("ALL_PROXY"),
            force_proxy=force_proxy,
        )

    def _build_proxies(
        self,
        http_proxy: str | None,
        https_proxy: str | None,
        all_proxy: str | None,
        force_proxy: bool | None = None,
    ) -> dict[str, str] | None:
        """Construit le dictionnaire proxies attendu par requests."""
        # force_proxy: True = always use proxies even if unreachable
        #              False = never use proxies
        #              None = autodetect (try reachability)

        if force_proxy is False:
            return None

        if http_proxy or https_proxy:
            proxies: dict[str, str] = {}
            if http_proxy:
                proxies["http"] = http_proxy
            if https_proxy:
                proxies["https"] = https_proxy

            if force_proxy is True:
                return proxies

            # Validate proxies: if proxy is not reachable (e.g., at home), don't return it
            reachable = {}
            for scheme, url in proxies.items():
                if self._is_proxy_reachable(url):
                    reachable[scheme] = url
                else:
                    print(f"Proxy {scheme} non joignable ({url}) — désactivé")

            return reachable if reachable else None

        if all_proxy:

            combined = {"http": all_proxy, "https": all_proxy}

            if force_proxy is True:
                return combined

            reachable = {}
            for scheme, url in combined.items():
                if self._is_proxy_reachable(url):
                    reachable[scheme] = url
                else:
                    print(f"Proxy {scheme} non joignable ({url}) — désactivé")

            return reachable if reachable else None

        return None

    def _is_proxy_reachable(self, proxy_url: str, timeout: float = 2.0) -> bool:
        """Vérifie rapidement si le proxy (host:port) est joignable.

        Accepts urls like 'http://proxy.example:3128' or 'proxy.example:3128'.
        Returns True si une connexion TCP peut être établie, False sinon.
        """
        if not proxy_url:
            return False

        try:
            parsed = urlparse(proxy_url)
            host = parsed.hostname or proxy_url.split(":")[0]
            port = parsed.port

            if port is None:
                # Default port for HTTP proxy
                port = 8080

            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    def _read_env_file(self, env_file: Path) -> dict[str, str]:
        """Lit un fichier .env local simple sans dépendance externe."""
        values: dict[str, str] = {}

        try:
            for raw_line in env_file.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}:
                    values[key] = value
        except OSError:
            return {}

        return values

    def _request_json(self, url, params, source_name):
        # --- CORRECTION IMAC : BYPASS DNS ---
        # On remplace les noms de domaine par l'IP directe (trouvée via nslookup)
        ip_openmeteo = "152.53.84.73"
        target_url = url.replace("marine-api.open-meteo.com", ip_openmeteo)
        target_url = target_url.replace("archive-api.open-meteo.com", ip_openmeteo)

        """Exécute un appel open_meteo en appliquant la configuration proxy si présente."""
        request_kwargs = {
            "params": params,
            "timeout": self.request_timeout,
            "proxies": {},  # Par défaut, pas de proxy
            "verify": False  # Obligatoire car le certificat SSL ne correspondra pas à l'IP
        }

        # COMMENTER TEMORAIREMENT POU DEBUG SUR IMAC PERSONNEL SANS PROXY
        #  if self.proxies:
        #     request_kwargs["proxies"] = self.proxies

        try:
            # Désactive les warnings SSL liés à l'usage de l'IP
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            response = self.session.get(target_url, **request_kwargs)
            response.raise_for_status()
            return response.json()
        # try:
        #     response = self.session.get(url, **request_kwargs)
        #     response.raise_for_status()
        #     return response.json()

        except requests.exceptions.RequestException as e:
            proxy_state = "avec proxy configuré" if self.proxies else "sans proxy configuré"
            print(f"Erreur open_meteo {source_name} ({proxy_state}): {e}")
            return None

    # =====================================================================
    # open_meteo MARINE API (Vagues, houle)
    # =====================================================================

    def get_marine_weather_open_meteo(self, start_date, end_date):
        """
        [open_meteo MARINE] Récupère les données de vagues
        UTILISÉ dans: collect_historical_data_batch()

        Données retournées:
        - Hauteur, direction, période des vagues
        - Houle (swell) vs vagues de vent
        - Formats: horaire + résumé quotidien
        """
        url = f"{self.open_meteo_base}/marine"

        params = {
            "latitude": self.marseille_coords["lat"],
            "longitude": self.marseille_coords["lon"],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": [
                "wave_height",
                "wave_direction",
                "wave_period",
                "wind_wave_height",
                "wind_wave_direction",
                "wind_wave_period",
                "swell_wave_height",
                "swell_wave_direction",
                "swell_wave_period",
            ],
            "daily": [
                "wave_height_max",
                "wave_direction_dominant",
                "wave_period_max",
                "wind_wave_height_max",
                "swell_wave_height_max",
            ],
            "timezone": "Europe/Paris",
        }

        return self._request_json(url, params, "marine")

    # =====================================================================
    # open_meteo ERA5 API (Météo générale)
    # =====================================================================

    def get_weather_data_open_meteo(self, start_date, end_date):
        """
        [open_meteo ERA5] Récupère les données de météo générale
        UTILISÉ dans: collect_historical_data_batch()

        Données retournées:
        - Température (min/max)
        - Vent (vitesse, direction, rafales)
        - Pression, humidité, couverture nuageuse
        - Source: Données de réanalyse (fiables et historiques)
        """
        url = "https://archive-api.open_meteo.com/v1/era5"

        params = {
            "latitude": self.marseille_coords["lat"],
            "longitude": self.marseille_coords["lon"],
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "surface_pressure",
                "cloud_cover",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
            ],
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "wind_direction_10m_dominant",
            ],
            "timezone": "Europe/Paris",
        }

        return self._request_json(url, params, "weather")

    # =====================================================================
    # ORCHESTRATION & TRAITEMENT (Fusion des données)
    # =====================================================================

    def collect_historical_data_batch(self, start_date, end_date, batch_days=30):
        """
        Collecte les données par lots via les 2 APIs open_meteo
        ✅ UTILISÉ dans: src.pipeline

        Processus:
        1. Appelle get_marine_weather_open_meteo() → données de vagues
        2. Appelle get_weather_data_open_meteo() → données météo générale
        3. Regroupe par lots de 30 jours (évite timeouts)
        4. Pause 2 sec entre les lots (respecte les limites API)

        Retour: Liste de dictionnaires avec {"marine_data", "weather_data"}
        """
        all_data = []
        current_start = start_date

        print(
            f"Récupération des données du {start_date} au {end_date} par lots de {batch_days} jours"
        )

        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=batch_days - 1), end_date)

            print(
                f"Traitement du lot: {current_start.strftime('%Y-%m-%d')} à {current_end.strftime('%Y-%m-%d')}"
            )

            # Données marine via open_meteo
            marine_data = self.get_marine_weather_open_meteo(current_start, current_end)

            # Données météo générales via open_meteo
            weather_data = self.get_weather_data_open_meteo(current_start, current_end)

            if marine_data or weather_data:
                batch_data = {
                    "period_start": current_start.strftime("%Y-%m-%d"),
                    "period_end": current_end.strftime("%Y-%m-%d"),
                    "marine_data": marine_data,
                    "weather_data": weather_data,
                }
                all_data.append(batch_data)

            # Pause entre les lots
            time.sleep(2)
            current_start = current_end + timedelta(days=1)

        return all_data

    def process_to_daily_summary(self, batch_data_list):
        """
        Fusionne et traite les données en résumé quotidien
        ✅ UTILISÉ dans: src.pipeline

        Processus:
        1. Extrait données quotidiennes marines et météo
        2. Fusionne par date (inner join sur la date)
        3. Gère les valeurs manquantes (None)
        4. Retourne DataFrame pandas prêt pour sauvegarde/ML
        """
        daily_records = []

        for batch in batch_data_list:
            marine_data = batch.get("marine_data", {})
            weather_data = batch.get("weather_data", {})

            # Traitement des données quotidiennes marines
            if marine_data and "daily" in marine_data:
                daily_marine = marine_data["daily"]
                dates = daily_marine.get("time", [])

                for i, date_str in enumerate(dates):
                    try:
                        record = {
                            "date": date_str,
                            "wave_height_max": (
                                daily_marine.get("wave_height_max", [None])[i]
                                if i < len(daily_marine.get("wave_height_max", []))
                                else None
                            ),
                            "wave_direction_dominant": (
                                daily_marine.get("wave_direction_dominant", [None])[i]
                                if i < len(daily_marine.get("wave_direction_dominant", []))
                                else None
                            ),
                            "wave_period_max": (
                                daily_marine.get("wave_period_max", [None])[i]
                                if i < len(daily_marine.get("wave_period_max", []))
                                else None
                            ),
                            "wind_wave_height_max": (
                                daily_marine.get("wind_wave_height_max", [None])[i]
                                if i < len(daily_marine.get("wind_wave_height_max", []))
                                else None
                            ),
                            "swell_wave_height_max": (
                                daily_marine.get("swell_wave_height_max", [None])[i]
                                if i < len(daily_marine.get("swell_wave_height_max", []))
                                else None
                            ),
                        }

                        # Ajout des données météo si disponibles
                        if weather_data and "daily" in weather_data:
                            daily_weather = weather_data["daily"]
                            weather_dates = daily_weather.get("time", [])

                            if date_str in weather_dates:
                                weather_idx = weather_dates.index(date_str)
                                record.update(
                                    {
                                        "temperature_max": (
                                            daily_weather.get("temperature_2m_max", [None])[
                                                weather_idx
                                            ]
                                            if weather_idx
                                            < len(daily_weather.get("temperature_2m_max", []))
                                            else None
                                        ),
                                        "temperature_min": (
                                            daily_weather.get("temperature_2m_min", [None])[
                                                weather_idx
                                            ]
                                            if weather_idx
                                            < len(daily_weather.get("temperature_2m_min", []))
                                            else None
                                        ),
                                        "wind_speed_max": (
                                            daily_weather.get("wind_speed_10m_max", [None])[
                                                weather_idx
                                            ]
                                            if weather_idx
                                            < len(daily_weather.get("wind_speed_10m_max", []))
                                            else None
                                        ),
                                        "wind_gusts_max": (
                                            daily_weather.get("wind_gusts_10m_max", [None])[
                                                weather_idx
                                            ]
                                            if weather_idx
                                            < len(daily_weather.get("wind_gusts_10m_max", []))
                                            else None
                                        ),
                                        "wind_direction_dominant": (
                                            daily_weather.get("wind_direction_10m_dominant", [None])[
                                                weather_idx
                                            ]
                                            if weather_idx
                                            < len(
                                                daily_weather.get("wind_direction_10m_dominant", [])
                                            )
                                            else None
                                        ),
                                    }
                                )

                        daily_records.append(record)

                    except (IndexError, ValueError) as e:
                        print(f"Erreur traitement date {date_str}: {e}")
                        continue

        return pd.DataFrame(daily_records)

    # =====================================================================
    # SAUVEGARDE
    # =====================================================================

    def save_data(self, data, start_date, end_date, save_json=False):
        """
        Sauvegarde les données traitées
        UTILISÉ dans: src.pipeline

        Format de sortie:
        - CSV: data/raw/YYYY/meteo_YYYY_MM_DD-au-MM_DD.csv (rapide, compacte)
        - JSON: optionnel, données brutes (lourd, legacy)

        Structures:
        - Dossier par année
        - Un fichier par mois couvert par la période
        - Nom du fichier inclut la plage effective du mois
        - Index: réinitialisé (facilite export)

        Retour:
        - csv_files: liste des chemins CSV générés
        - json_files: liste des chemins JSON générés (ou None si save_json=False)
        """
        if not isinstance(data, pd.DataFrame) or data.empty:
            return [], None if not save_json else []

        if "date" not in data.columns:
            raise ValueError("La colonne 'date' est requise pour la sauvegarde mensuelle")

        working_df = data.copy()
        working_df["date"] = pd.to_datetime(working_df["date"], errors="coerce")
        working_df = working_df.dropna(subset=["date"]).sort_values("date")

        csv_files = []
        json_files = []

        for _, month_df in working_df.groupby(working_df["date"].dt.to_period("M")):
            month_start = month_df["date"].min()
            month_end = month_df["date"].max()

            year = month_start.strftime("%Y")
            output_dir = Path("data/raw") / year
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = (
                f"meteo_{month_start.strftime('%Y_%m_%d')}-au-{month_end.strftime('%m_%d')}.csv"
            )
            csv_file = output_dir / filename

            month_to_save = month_df.copy()
            month_to_save["date"] = month_to_save["date"].dt.strftime("%Y-%m-%d")
            month_to_save.to_csv(csv_file, index=False)
            csv_files.append(csv_file)
            print(f"✓ CSV sauvegardé: {csv_file}")

            if save_json:
                json_filename = filename.replace(".csv", ".json")
                json_file = output_dir / json_filename
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(month_to_save.to_dict(orient="records"), f, indent=2, ensure_ascii=False)
                json_files.append(json_file)
                print(f"✓ JSON sauvegardé: {json_file}")

        return csv_files, (json_files if save_json else None)
