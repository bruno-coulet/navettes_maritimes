"""
Train V3 : modèle fusion (météo Open-Meteo + features métier)

Objectif :
- utiliser toutes les features pertinentes du merge V3
- entraîner un modèle robuste
- sauvegarder modèle + features + métriques
"""

import json
import pickle
from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# =========================
# CONFIG
# =========================

DATA_PATH = Path("meteo_marine/data/processed/training_merged_v3.parquet")

ARTIFACTS_DIR = Path("meteo_marine/artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ARTIFACTS_DIR / "model_v3.pkl"
FEATURES_PATH = ARTIFACTS_DIR / "features_v3.json"
METRICS_PATH = ARTIFACTS_DIR / "metrics_v3.json"

# Import features
from features_v3 import FEATURES_V3, TARGET


# =========================
# 1. LOAD
# =========================

def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_parquet(DATA_PATH)

    print(f"\nDataset loaded: {df.shape}")
    print(f"Columns: {len(df.columns)}")

    return df


# =========================
# 2. PREPARE FEATURES
# =========================

def prepare_features(df):

    print("\n[1/4] Preparing features...")

    # TARGET
    y = df[TARGET]

    # FEATURES
    X = df[FEATURES_V3].copy()

    # Détection catégoriel auto
    categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

    print(f"Categorical columns: {len(categorical_cols)}")

    # One-hot encoding
    X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)

    print(f"Shape after encoding: {X.shape}")

    return X, y


# =========================
# 3. TRAIN
# =========================

def train_model(X, y):

    print("\n[2/4] Training model...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # Prediction
    y_pred = model.predict(X_test)

    # Metrics
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "n_samples": len(X),
        "n_features": X.shape[1],
        "target_rate": float(y.mean())
    }

    print("\nMetrics:")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")

    return model, metrics, X.columns.tolist()


# =========================
# 4. SAVE
# =========================

def save_artifacts(model, metrics, feature_names):

    print("\n[3/4] Saving artifacts...")

    # Model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    # Features
    with open(FEATURES_PATH, "w") as f:
        json.dump(feature_names, f, indent=2)

    # Metrics
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Model saved: {MODEL_PATH}")
    print(f"✅ Features saved: {FEATURES_PATH}")
    print(f"✅ Metrics saved: {METRICS_PATH}")


# =========================
# MAIN
# =========================

def main():

    print("=" * 70)
    print("TRAINING V3 : Fusion météo + métier")
    print("=" * 70)

    df = load_data()

    X, y = prepare_features(df)

    model, metrics, feature_names = train_model(X, y)

    save_artifacts(model, metrics, feature_names)

    print("\n✅ TRAINING V3 COMPLETED")


if __name__ == "__main__":
    main()
