"""API FastAPI de prediction d'annulation pour les navettes maritimes.

Responsabilite:
- charger le modele et ses metadata depuis `artifacts/`
- exposer un endpoint de prediction a partir de variables meteo

Entrees:
- fichiers `model.pkl` et `features.json`
- payload JSON conforme au modele Pydantic `WeatherData`

Sorties:
- reponse JSON avec la prediction et la probabilite

Commande:
- `uvicorn src.predict_annulation:app --host 0.0.0.0 --port 8000`
"""

import json
import os
import pickle
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .meteo import get_forecast_24h

# ========================================
# Configuration
# ========================================
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL = PROJECT_ROOT / "v3_hybride" / "artifacts" / "model_v3.pkl"
DEFAULT_METRICS = PROJECT_ROOT / "v3_hybride" / "artifacts" / "metrics_v3.json"

MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL)))
FEATURES_PATH = Path(os.getenv("FEATURES_PATH", str(DEFAULT_METRICS)))

app = FastAPI(
    title="Navettes Maritimes - Prédiction d'Annulation",
    description="API pour prédire les annulations de navettes basées sur les données météo",
    version="1.0.0",
)

# Cache global du modèle
_model = None
_features_metadata = None

# ========================================
# Pydantic Models
# ========================================
class WeatherData(BaseModel):
    """Données météo d'entrée pour une prédiction."""
    wave_height_max: Optional[float] = None
    wave_direction_dominant: Optional[float] = None
    wave_period_max: Optional[float] = None
    wind_wave_height_max: Optional[float] = None
    swell_wave_height_max: Optional[float] = None
    temperature_max: Optional[float] = None
    temperature_min: Optional[float] = None
    wind_speed_max: Optional[float] = None
    wind_gusts_max: Optional[float] = None
    wind_direction_dominant: Optional[float] = None
    wave_height_max: float
    wave_period_max: float
    temperature_max: Optional[float] = None
    temperature_min: Optional[float] = None
    wind_speed_max: float
    wind_gusts_max: float
    Vent_Orientation: str
    # Métier (V3)
    Capitaine: str
    Bateau: str
    Ligne: str


class PredictionResponse(BaseModel):
    """Réponse de prédiction."""
    annulation_probability: float
    annulation_predicted: bool  # True = annulée, False = confirmée
    confidence: float  # Entre 0 et 1


class HealthResponse(BaseModel):
    """Santé du service."""
    status: str
    model_loaded: bool
    n_features: Optional[int] = None

# ========================================
# Chargement du modèle
# ========================================
def load_model():
    """Charge le modèle et les métadonnées."""
    global _model, _features_metadata

    try:
        if _model is not None:
            return  # Déjà chargé

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Modèle non trouvé : {MODEL_PATH}")
        if not FEATURES_PATH.exists():
            raise FileNotFoundError(f"Métadonnées non trouvées : {FEATURES_PATH}")

        print(f"Chargement du modèle depuis {MODEL_PATH}...")
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)

        print(f"Chargement des métadonnées depuis {FEATURES_PATH}...")
        with open(FEATURES_PATH, "r") as f:
            _features_metadata = json.load(f)
        print(f"Modèle et métadonnées chargés (Features: {len(_features_metadata['feature_names'])})")

    except Exception as e:
        print(f"❌ Erreur chargement : {e}")

# ========================================
# Routes
# ========================================
@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage."""
    try:
        load_model()
    except Exception as e:
        print(f"⚠️  Erreur au chargement du modèle : {e}")


@app.post("/predict")
async def predict(data: WeatherData):
    if _model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")

    try:
        # 1. On récupère la liste exacte des 146 colonnes du modèle
        feature_names = _features_metadata["feature_names"]

        # 2. On crée un dictionnaire "vide" (tous à 0.0)
        input_row = {f: 0.0 for f in feature_names}

        # 3. On remplit les valeurs numériques
        # Note : On mappe wave_height_max sur HouleMax pour la compatibilité V1/V3
        # mapping_num = {
        #     "wave_height_max": data.wave_height_max,
        #     "HouleMax": data.wave_height_max, # Double mapping pour la robustesse
        #     "wave_period_max": data.wave_period_max,
        #     "HoulePeriode": data.wave_period_max,
        #     "temperature_max": data.temperature_max,
        #     "temperature_min": data.temperature_min,
        #     "wind_speed_max": data.wind_speed_max,
        #     "wind_gusts_max": data.wind_gusts_max
        # }
        input_row["wave_height_max"] = data.wave_height_max
        input_row["HouleMax"] = data.wave_height_max  # Doublon V1/V3
        input_row["wave_period_max"] = data.wave_period_max
        input_row["wave_direction_dominant"] = data.wave_direction_dominant
        input_row["wind_speed_max"] = data.wind_speed_max
        input_row["wind_gusts_max"] = data.wind_gusts_max
        input_row["wind_direction_dominant"] = data.wind_direction_dominant

        # Gestion des neutres pour éviter de parasiter le modèle
        input_row["temperature_max"] = data.temperature_max if data.temperature_max is not None else 18.0
        input_row["temperature_min"] = data.temperature_min if data.temperature_min is not None else 12.0

        # 4. ACTIVATION DES COLONNES CATÉGORIELLES (One-Hot)
        # On "allume" (1.0) uniquement les colonnes sélectionnées
        categories = [
            f"Capitaine_{data.Capitaine}",
            f"Bateau_{data.Bateau}",
            f"Ligne_{data.Ligne}",
            f"Vent_{data.Vent_Orientation}" # Ton fameux doublon NW, SE, etc.
        ]

        for cat_col in categories:
            if cat_col in input_row:
                input_row[cat_col] = 1.0

        # 5. VALEURS PAR DÉFAUT POUR LES CHAMPS ABSENTS (ex: Ciel)
        # Si le modèle attend un ciel et qu'on ne l'a pas, on met 'Clair' par défaut
        if "Ciel_Clair " in input_row:
            input_row["Ciel_Clair "] = 1.0

        # 6. CRÉATION DU DATAFRAME
        # On s'assure que l'ordre des colonnes est EXACTEMENT celui du modèle
        X = pd.DataFrame([input_row])[feature_names]

        # 7. PRÉDICTION
        prob = float(_model.predict_proba(X)[0][1])

        return {
            "annulation_probability": prob,
            "status": "success"
        }

    except Exception as e:
        print(f"Erreur lors de la prédiction : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

        # for feat, val in mapping_num.items():
        #     if feat in input_row:
        #         input_row[feat] = val

        # # 4. On "allume" les colonnes catégorielles (One-Hot Encoding)
        # # On construit le nom de la colonne comme le modèle l'a appris
        # cols_to_activate = [
        #     f"Capitaine_{data.Capitaine}",
        #     f"Bateau_{data.Bateau}",
        #     f"Ligne_{data.Ligne}"
        # ]

        # for col in cols_to_activate:
        #     if col in input_row:
        #         input_row[col] = 1.0
        #     else:
        #         # Optionnel : log si une valeur n'est pas reconnue
        #         print(f"⚠️ Valeur inconnue pour le modèle : {col}")

        # # On active la colonne d'orientation du vent envoyée par le front
        # col_vent = f"Vent_{data.Vent_Orientation}" # Ex: Vent_NW
        # if col_vent in input_row:
        #     input_row[col_vent] = 1.0

        # # 5. Conversion en DataFrame avec l'ordre STRICT des colonnes
        # X = pd.DataFrame([input_row])[all_features]

        # # 6. Prédiction
        # probabilities = _model.predict_proba(X)
        # prob_annulation = float(probabilities[0][1])

        # return {
        #     "annulation_probability": prob_annulation,
        #     "prediction": "Annulation" if prob_annulation > 0.5 else "Maintenu",
        #     "confidence": float(max(probabilities[0])),
        #     "model_version": "V3_Hybride"
        # }

    # except Exception as e:
    #     print(f"Erreur lors de la prédiction : {str(e)}")
    #     raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Vérifier la santé du service."""
    return HealthResponse(
        status="ok" if _model is not None else "degraded",
        model_loaded=_model is not None,
        n_features=_features_metadata.get("n_features") if _features_metadata else None,
    )

@app.post("/predict_batch")
async def predict_batch(csv_path: str):
    """
    Prédire les annulations pour un lot de données (CSV).

    Charge le CSV, applique le modèle, retourne un CSV enrichi.
    """
    if _model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")

    try:
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"Fichier non trouvé : {csv_path}")

        # Charger
        df = pd.read_csv(csv_file)
        features = _features_metadata["feature_names"]
        X = df[features].fillna(0)

        # Prédire
        predictions = _model.predict(X)
        probabilities = _model.predict_proba(X)

        # Ajouter au DataFrame
        df["annulation_predicted"] = predictions
        df["annulation_probability"] = probabilities[:, 1]
        df["confidence"] = probabilities.max(axis=1)

        # Exporter
        output_path = Path("/app/predictions") / f"predictions_{csv_file.stem}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

        return {
            "status": "success",
            "input_file": str(csv_file),
            "output_file": str(output_path),
            "n_predictions": len(df),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur batch : {str(e)}")


@app.get("/")
async def root():
    """Documentation racine."""
    return {
        "title": "Navettes Maritimes - Prédiction d'Annulation",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Vérifier la santé du service",
            "POST /predict": "Prédire une annulation",
            "POST /predict_batch": "Prédire un lot de données",
            "GET /docs": "Documentation interactive (Swagger UI)",
        },
    }


@app.get("/predict/tomorrow")
async def predict_tomorrow():
    """
    Récupère la météo de demain et prédit le statut de toutes les lignes 
    pour un capitaine et un bateau par défaut.
    """
    if _model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")

    try:
        # 1. Récupération auto de la météo via ton nouveau script
        forecast = get_forecast_24h()
        
        # 2. On définit les constantes pour le bulletin global
        # (Tu peux les changer ou les rendre dynamiques plus tard)
        default_capitaine = "0cb84352" 
        default_bateau = "Ratonneau"
        all_lignes = _features_metadata.get("lignes_list", [
            "Vieux Port-Frioul", "Frioul-Vieux Port", 
            "Vieux Port-IF", "IF-Vieux Port",
            "Estaque-Vieux Port"
        ])

        results = []
        feature_names = _features_metadata["feature_names"]

        # 3. On boucle sur chaque ligne pour générer le bulletin
        for ligne in all_lignes:
            input_row = {f: 0.0 for f in feature_names}

            # Remplissage météo
            input_row["HouleMax"] = forecast["wave_height_max"]
            input_row["wave_height_max"] = forecast["wave_height_max"]
            input_row["wind_speed_max"] = forecast["wind_speed_max"]
            input_row["wind_gusts_max"] = forecast["wind_gusts_max"]
            input_row["temperature_max"] = forecast["temperature_max"]
            input_row["temperature_min"] = forecast["temperature_min"]

            # Encodage métier
            if f"Capitaine_{default_capitaine}" in input_row:
                input_row[f"Capitaine_{default_capitaine}"] = 1.0
            if f"Bateau_{default_bateau}" in input_row:
                input_row[f"Bateau_{default_bateau}"] = 1.0
            if f"Ligne_{ligne}" in input_row:
                input_row[f"Ligne_{ligne}"] = 1.0

            # Prédiction
            X = pd.DataFrame([input_row])[feature_names]
            prob = float(_model.predict_proba(X)[0][1])

            results.append({
                "ligne": ligne,
                "probabilite_annulation": prob,
                "statut": "⚠️ RISQUE" if prob > 0.5 else "✅ OK"
            })

        return {
            "date_prevision": "Demain",
            "meteo_source": "Open-Meteo",
            "details_meteo": forecast,
            "bulletin": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur prévision auto : {str(e)}")

if __name__ == "__main__":
    import os
    import uvicorn

    load_model()
    uvicorn.run(app, host="0.0.0.0", port=8000)
