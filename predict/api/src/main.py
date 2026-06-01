"""API FastAPI de prediction d'annulation pour les navettes maritimes.

Responsabilite:
- charger le modele et ses metadonnees depuis `artifacts/`
- exposer un endpoint de prediction a partir de variables meteo

Entrees:
- fichiers `model.pkl` et `metrics_v3.json`
- payload JSON conforme au modele Pydantic `WeatherData`

Sorties:
- reponse JSON avec la prediction et la probabilite

Commande:
- `uvicorn src.main:app --host 0.0.0.0 --port 8000`
"""

import json
import os
import pickle
from pathlib import Path
from typing import Optional, Any

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
METRICS_PATH = Path(os.getenv("FEATURES_PATH", str(DEFAULT_METRICS)))

app = FastAPI(
    title="Navettes Maritimes - Prédiction d'Annulation",
    description="API pour prédire les annulations de navettes basées sur les données météo",
    version="1.0.0",
)

# Cache global du modèle
_model = None
_features_metadata = None

DEFAULT_WEATHER_GUARDRAILS = {
    "enabled": True,
    "min_reason_count": 2,
    "thresholds": {
        "wind_speed_max": {"moderate": 45.0, "severe": 55.0, "unit": "km/h", "label": "vent soutenu"},
        "wind_gusts_max": {"moderate": 60.0, "severe": 75.0, "unit": "km/h", "label": "rafales fortes"},
        "wave_height_max": {"moderate": 2.0, "severe": 2.8, "unit": "m", "label": "houle importante"},
        "wind_wave_height_max": {"moderate": 1.2, "severe": 1.8, "unit": "m", "label": "mer du vent elevee"},
        "swell_wave_height_max": {"moderate": 1.5, "severe": 2.2, "unit": "m", "label": "swell eleve"},
    },
    "keywords": [
        "tempete",
        "orage",
        "agite",
        "agitée",
        "tres agite",
        "très agité",
        "fort",
        "violent",
        "violente",
        "mauvais",
        "mauvaise",
        "houleux",
        "houleuse",
        "difficile",
    ],
}

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
    Vent_Orientation: Optional[str] = None
    Ciel: Optional[str] = None
    Mer: Optional[str] = None
    Vent: Optional[str] = None
    HouleDominante: Optional[str] = None
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
# Garde fous métier
# ========================================
def _safe_float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = payload.get(key, default)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _degrees_to_orientation(degrees: Optional[float]) -> Optional[str]:
    if degrees is None:
        return None

    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = int((float(degrees) + 11.25) // 22.5) % 16
    return directions[index]


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _get_weather_guardrail_config() -> dict[str, Any]:
    if _features_metadata is None:
        return DEFAULT_WEATHER_GUARDRAILS

    config = _features_metadata.get("weather_guardrails")
    if isinstance(config, dict):
        return config

    return DEFAULT_WEATHER_GUARDRAILS


def _weather_guardrail_reasons(payload: dict[str, Any], guardrail_config: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    thresholds = guardrail_config.get("thresholds", {})

    for feature_name, rule in thresholds.items():
        label = rule.get("label", feature_name)
        value = _safe_float(payload, feature_name)
        moderate_limit = float(rule.get("moderate", 0.0))
        severe_limit = float(rule.get("severe", moderate_limit))
        unit = rule.get("unit", "")

        if value <= 0.0:
            continue
        if value >= severe_limit:
            reasons.append(f"{label} ({value:.1f} {unit})")
        elif value >= moderate_limit:
            reasons.append(f"{label} ({value:.1f} {unit})")

    bad_weather_keywords = tuple(guardrail_config.get("keywords", DEFAULT_WEATHER_GUARDRAILS["keywords"]))

    for field_name in ("Ciel", "Mer", "Vent", "HouleDominante"):
        raw_value = payload.get(field_name)
        normalized = _normalize_text(raw_value)
        if normalized and any(keyword in normalized for keyword in bad_weather_keywords):
            reasons.append(f"{field_name.lower()} défavorable ({raw_value})")

    return reasons


def _build_model_input(payload: dict[str, Any]) -> pd.DataFrame:
    """Construit une ligne d'entrée compatible avec les features du modèle."""
    if _features_metadata is None:
        raise HTTPException(status_code=503, detail="Métadonnées du modèle non chargées")

    feature_names = _features_metadata.get("feature_names", [])
    input_row = {feature_name: 0.0 for feature_name in feature_names}

    numeric_mapping = {
        "HouleMax": _safe_float(payload, "wave_height_max"),
        "HoulePeriode": _safe_float(payload, "wave_period_max"),
        "HouleDominante": _safe_float(payload, "wave_direction_dominant"),
        "wave_height_max": _safe_float(payload, "wave_height_max"),
        "wave_period_max": _safe_float(payload, "wave_period_max"),
        "wave_direction_dominant": _safe_float(payload, "wave_direction_dominant"),
        "wind_wave_height_max": _safe_float(payload, "wind_wave_height_max"),
        "swell_wave_height_max": _safe_float(payload, "swell_wave_height_max"),
        "temperature_max": _safe_float(payload, "temperature_max"),
        "temperature_min": _safe_float(payload, "temperature_min"),
        "wind_speed_max": _safe_float(payload, "wind_speed_max"),
        "wind_gusts_max": _safe_float(payload, "wind_gusts_max"),
        "wind_direction_dominant": _safe_float(payload, "wind_direction_dominant"),
    }

    for feature_name, value in numeric_mapping.items():
        if feature_name in input_row:
            input_row[feature_name] = value

    orientation = payload.get("Vent_Orientation")
    if orientation is None:
        orientation = _degrees_to_orientation(payload.get("wind_direction_dominant"))

    if orientation is not None:
        orientation = str(orientation).strip()
        vent_feature = f"Vent_{orientation}"
        if vent_feature in input_row:
            input_row[vent_feature] = 1.0

    for prefix in ("Ciel", "Mer", "Vent", "HouleDominante"):
        value = payload.get(prefix)
        if value is None:
            continue
        feature_name = f"{prefix}_{value}"
        if feature_name in input_row:
            input_row[feature_name] = 1.0

    for prefix in ("Capitaine", "Bateau", "Ligne"):
        value = payload.get(prefix)
        if value is None:
            continue
        feature_name = f"{prefix}_{value}"
        if feature_name in input_row:
            input_row[feature_name] = 1.0

    return pd.DataFrame([input_row], columns=feature_names)


def apply_maritime_guardrails(payload: dict[str, Any], prediction_result: dict[str, Any]) -> dict[str, Any]:
    """Force l'annulation si la meteo depasse des seuils de securite."""

    guardrail_config = _get_weather_guardrail_config()
    if not guardrail_config.get("enabled", True):
        prediction_result["guardrail_triggered"] = False
        prediction_result["guardrail_reason"] = None
        return prediction_result

    reasons = _weather_guardrail_reasons(payload, guardrail_config)

    min_reason_count = int(guardrail_config.get("min_reason_count", 2))
    thresholds = guardrail_config.get("thresholds", {})

    severe_conditions = [
        _safe_float(payload, feature_name) >= float(rule.get("severe", 0.0))
        for feature_name, rule in thresholds.items()
    ]

    if reasons and (any(severe_conditions) or len(reasons) >= min_reason_count):
        prediction_result["annulation_probability"] = 1.0
        prediction_result["annulation_predicted"] = True
        prediction_result["confidence"] = 1.0
        prediction_result["guardrail_triggered"] = True
        prediction_result["guardrail_reason"] = "Mauvaise meteo detectee : " + ", ".join(reasons) if reasons else "Mauvaise meteo detectee"
    else:
        prediction_result["guardrail_triggered"] = False
        prediction_result["guardrail_reason"] = None

    return prediction_result


def predict_annulation(payload: dict[str, Any]) -> dict[str, Any]:
    """Calcule la prediction du modele puis applique les garde-fous."""

    if _model is None or _features_metadata is None:
        raise HTTPException(status_code=503, detail="Modele non charge")

    X = _build_model_input(payload)
    probabilities = _model.predict_proba(X)[0]
    classes = list(getattr(_model, "classes_", [0, 1]))
    positive_class_index = classes.index(1) if 1 in classes else len(probabilities) - 1

    prediction_result = {
        "annulation_probability": float(probabilities[positive_class_index]),
        "annulation_predicted": bool(_model.predict(X)[0]),
        "confidence": float(probabilities.max()),
    }

    return apply_maritime_guardrails(payload, prediction_result)

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
        if not METRICS_PATH.exists():
            raise FileNotFoundError(f"Métadonnées non trouvées : {METRICS_PATH}")

        print(f"Chargement du modèle depuis {MODEL_PATH}...")
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)

        print(f"Chargement des métadonnées depuis {METRICS_PATH}...")
        with open(METRICS_PATH, "r") as f:
            _features_metadata = json.load(f)
        print(f"Modèle et métadonnées chargés (Features: {len(_features_metadata.get('feature_names', []))})")

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
async def predict(request: WeatherData):
    """Effectue une prédiction d'annulation pour une traversée unique."""
    try:
        payload = request.model_dump()
        resultat = predict_annulation(payload)
        resultat["model_version"] = getattr(_model, "version", "v3_hybride")
        return resultat

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur prédiction: {str(e)}")


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
    if _model is None or _features_metadata is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")

    try:
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"Fichier non trouvé : {csv_path}")

        # Charger
        df = pd.read_csv(csv_file)
        features = _features_metadata.get("feature_names", [])
        X = df.reindex(columns=features, fill_value=0).fillna(0)

        # Prédire
        predictions = _model.predict(X)
        probabilities = _model.predict_proba(X)
        classes = list(getattr(_model, "classes_", [0, 1]))
        positive_class_index = classes.index(1) if 1 in classes else probabilities.shape[1] - 1

        # Ajouter au DataFrame
        df["annulation_predicted"] = predictions
        df["annulation_probability"] = probabilities[:, positive_class_index]
        df["confidence"] = probabilities.max(axis=1)

        guardrail_results = []
        for _, row in df.iterrows():
            result = {
                "annulation_probability": float(row["annulation_probability"]),
                "annulation_predicted": bool(row["annulation_predicted"]),
                "confidence": float(row["confidence"]),
            }
            guardrail_results.append(apply_maritime_guardrails(row.to_dict(), result))

        df["annulation_probability"] = [result["annulation_probability"] for result in guardrail_results]
        df["annulation_predicted"] = [result["annulation_predicted"] for result in guardrail_results]
        df["confidence"] = [result["confidence"] for result in guardrail_results]
        df["guardrail_triggered"] = [result["guardrail_triggered"] for result in guardrail_results]
        df["guardrail_reason"] = [result["guardrail_reason"] for result in guardrail_results]

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
    if _model is None or _features_metadata is None:
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

        # 3. On boucle sur chaque ligne pour générer le bulletin
        for ligne in all_lignes:
            payload = {
                "wave_height_max": forecast["wave_height_max"],
                "wave_period_max": forecast["wave_period_max"],
                "wind_speed_max": forecast["wind_speed_max"],
                "wind_gusts_max": forecast["wind_gusts_max"],
                "temperature_max": forecast["temperature_max"],
                "temperature_min": forecast["temperature_min"],
                "Capitaine": default_capitaine,
                "Bateau": default_bateau,
                "Ligne": ligne,
            }

            resultat = predict_annulation(payload)

            results.append({
                "ligne": ligne,
                "probabilite_annulation": float(resultat["annulation_probability"]),
                "statut": "⚠️ ANNULATION FORCÉE" if resultat.get("guardrail_triggered") else ("⚠️ RISQUE" if resultat["annulation_probability"] > 0.5 else "✅ OK"),
                "guardrail_triggered": bool(resultat.get("guardrail_triggered", False)),
                "guardrail_reason": resultat.get("guardrail_reason"),
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
