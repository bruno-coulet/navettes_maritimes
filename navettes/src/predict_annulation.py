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

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ========================================
# Configuration
# ========================================
MODEL_PATH = Path(os.getenv("MODEL_PATH", "/model/model.pkl"))
FEATURES_PATH = Path(os.getenv("FEATURES_PATH", "/model/features.json"))

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
    
    print(f"✓ Modèle chargé : {_features_metadata.get('model_type', 'unknown')}")
    print(f"✓ Features attendues : {_features_metadata.get('n_features', 'unknown')}")


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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Vérifier la santé du service."""
    return HealthResponse(
        status="ok" if _model is not None else "degraded",
        model_loaded=_model is not None,
        n_features=_features_metadata.get("n_features") if _features_metadata else None,
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(data: WeatherData):
    """
    Prédire l'annulation d'une navette en fonction des données météo.
    
    Retourne :
    - annulation_probability : probabilité d'annulation (0-1)
    - annulation_predicted : True si prédiction = annulation
    - confidence : confiance du modèle
    """
    if _model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    
    try:
        # Convertir les données en DataFrame avec les bonnes colonnes
        features = _features_metadata["feature_names"]
        input_dict = data.dict()
        
        # Créer un vecteur d'entrée avec les bonnes colonnes
        X = pd.DataFrame([input_dict])[features].fillna(0)
        
        # Prédiction
        prediction = _model.predict(X)[0]
        probability = _model.predict_proba(X)[0]
        
        # Probabilité d'annulation (classe 1)
        annulation_prob = float(probability[1])
        
        return PredictionResponse(
            annulation_probability=annulation_prob,
            annulation_predicted=bool(prediction),
            confidence=float(max(probability)),
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur de prédiction : {str(e)}")


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


if __name__ == "__main__":
    import os
    import uvicorn
    
    load_model()
    uvicorn.run(app, host="0.0.0.0", port=8000)
