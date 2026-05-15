"""
Train RandomForest model on open_meteo merged data.

Differences vs previous v2:
1. Input: training_merged.parquet (Annulation='mean', distribution réelle)
2. Features: même que avant (wave_height, temperature, wind, etc)
3. Cible: Annulation comme probabilité ou binaire (test les deux)

Données corrigées:
- Periode: 2024-01-01 → 2026-01-09 (719 jours)
- Distribution: 18.5% annulations (vs 65.6% avant, vs 16.6% v1)
"""

import json
import pickle
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


# === CONFIG ===
# Remonte jusqu'à la racine du projet 'navettes_maritimes'
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = PROJECT_ROOT / "open_meteo"
DATA_PATH = BASE_DIR / "data" / "processed" / "training_merged_meteo_only.parquet"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ARTIFACTS_DIR / "model_v2.pkl"
FEATURES_PATH = ARTIFACTS_DIR / "metrics_v2.json"

# Features open_meteo pures (identique à v2)
OPENMETEO_FEATURES = [
    'wave_height_max',
    'wave_direction_dominant', 
    'wave_period_max',
    'wind_wave_height_max',
    'swell_wave_height_max',
    'temperature_max',
    'temperature_min',
    'wind_speed_max',
    'wind_gusts_max',
]


def load_data(parquet_path=DATA_PATH):
    """Charge le dataset mergé."""
    if not parquet_path.exists():
        raise FileNotFoundError(f"Dataset not found: {parquet_path}\n"
                              f"Run: python recalculate_merge.py first")
    
    df = pd.read_parquet(parquet_path)
    print(f"[1/4] Loaded {len(df)} days from {parquet_path.name}")
    print(f"      Annulation distribution:")
    print(f"        - Mean % per day: {df['AnnulationPct'].mean()*100:.1f}%")
    print(f"        - Binary (threshold 16.6%): {df['Annulation_binary'].value_counts().to_dict()}")
    
    return df


def prepare_features(df):
    """Prépare les features open_meteo."""
    print(f"\n[2/4] Feature engineering...")
    
    X = df[OPENMETEO_FEATURES].copy()
    
    # Features dérivées (identique à v2)
    X['wave_to_swell_ratio'] = X['wave_height_max'] / (X['swell_wave_height_max'] + 1e-5)
    X['total_wave_energy'] = X['wave_height_max'] + X['swell_wave_height_max']
    X['wind_to_wave_ratio'] = X['wind_speed_max'] / (X['wave_height_max'] + 1e-5)
    X['temp_range'] = X['temperature_max'] - X['temperature_min']
    
    # Vérifier missing values
    if X.isnull().any().any():
        print("  ⚠ Missing values found, forward-filling...")
        X = X.fillna(method='ffill').fillna(method='bfill')
    
    # Utiliser binary target (threshold 16.6% pour cohérence avec v1)
    y = df['Annulation_binary'].astype(int)
    
    print(f"  ✓ {X.shape[1]} features")
    print(f"  ✓ Target (binary, threshold=16.6%): {y.value_counts().to_dict()}")
    
    return X, y


def train_model(X, y, test_size=0.2, random_state=42):
    """Entraîne RandomForest et retourne métriques."""
    print(f"\n[3/4] Training RandomForest...")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # Entraîner (identique à v2)
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Évaluer
    y_pred = model.predict(X_test)
    metrics = {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, zero_division=0)),
        'f1': float(f1_score(y_test, y_pred, zero_division=0)),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        'test_size': len(X_test),
        'train_size': len(X_train),
    }
    
    print(f"  ✓ Accuracy: {metrics['accuracy']:.4f}")
    print(f"  ✓ F1-Score: {metrics['f1']:.4f}")
    print(f"  ✓ Precision: {metrics['precision']:.4f}")
    print(f"  ✓ Recall: {metrics['recall']:.4f}")
    
    return model, metrics, X.columns.tolist()


# def save_artifacts_old(model, metrics, feature_names, model_path=MODEL_PATH, features_path=FEATURES_PATH):
#     """Sauvegarde le modèle et les métadonnées."""
#     print(f"\n[4/4] Saving artifacts...")
    
#     ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
#     # Modèle
#     with open(model_path, 'wb') as f:
#         pickle.dump(model, f)
#     print(f"  ✓ {model_path}")
    
#     # Features metadata
#     features_info = {
#         'feature_names': feature_names,
#         'n_features': len(feature_names),
#         'model_type': 'RandomForestClassifier',
#         'model_params': {
#             'n_estimators': 100,
#             'max_depth': 10,
#             'min_samples_split': 5,
#         },
#         'metrics': metrics,
#         'trained_at': datetime.now().isoformat(),
#         'source': 'open_meteo (merged with Maritime annulations)',
#         'notes': 'v2: Fixed aggregation bug (mean instead of max)',
#     }
    
#     with open(features_path, 'w') as f:
#         json.dump(features_info, f, indent=2)
#     print(f"  ✓ {features_path}")

def save_artifacts(model, metrics, feature_names):
    """Sauvegarde le modèle et les métriques (Structure Plate Uniformisée)."""
    print(f"\n[4/4] Saving artifacts...")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Sauvegarde du modèle
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    # 2. Sauvegarde des métriques (STRUCTURE PLATE pour compare_versions.py)
    output_metrics = {
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "n_features": len(feature_names),
        "feature_names": feature_names,
        "trained_at": datetime.now().isoformat(),
        "model_type": "RandomForest_V2_MeteoOnly"
    }
    
    with open(FEATURES_PATH, 'w') as f:
        json.dump(output_metrics, f, indent=4)
    
    print(f"  ✓ Model: {MODEL_PATH.name}")
    print(f"  ✓ Metrics: {FEATURES_PATH.name}")

def main():
    """Pipeline complet."""
    print("="*70)
    print("TRAINING: RandomForest on open_meteo Data")
    print("="*70)
    
    # Load
    df = load_data()
    
    # Prepare
    X, y = prepare_features(df)
    
    # Train
    model, metrics, feature_names = train_model(X, y)
    
    # Save
    save_artifacts(model, metrics, feature_names)
    
    print(f"\n{'='*70}")
    print("✓ TRAINING COMPLETE (v2)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
