"""Entraînement du modele d'annulation pour les navettes maritimes.

Anciennement nommé train_annulation.py
renommé pour différencier des futurs modèles basés sur Open-Meteo.

Responsabilite:
- charger les donnees pretraitees ou les artefacts de preprocessing
- entrainer un RandomForest
- exporter le modele et ses metadata pour l'inference

Entrees:
- `data/maritime_clean.csv` ou `artifacts/preprocessing/maritime_clean/preprocessed.csv`

Sorties:
- `artifacts/model.pkl`
- `artifacts/features.json`

Commande:
- `python src/train_annulation.py`
"""

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from v1_baseline.src.preprocessing_utils import preprocess_maritime_data
from v1_baseline.src.paths import get_artifacts_dir, get_data_dir


def load_and_prepare_data(csv_path: str | None = None) -> tuple[pd.DataFrame, pd.Series]:
    """
    Charge et prépare les données pour l'entraînement.
    
    Si csv_path est None, utilise le fichier par défaut du projet maritime.
    """
    if csv_path is None:
        csv_path = Path(__file__).resolve().parents[1] / "data" / "maritime_clean.csv"
    
    print(f"Chargement des données depuis {csv_path}...")
    df = pd.read_csv(csv_path, index_col=0)
    
    if df.empty:
        raise ValueError(f"Fichier vide : {csv_path}")
    
    # Vérifier que la cible existe
    if "Annulation" not in df.columns:
        raise ValueError("Colonne 'Annulation' manquante dans les données")
    
    # Préparation : si des artefacts pré-calculés existent, les utiliser
    artifacts_root = get_artifacts_dir() / "preprocessing" / "maritime_clean"
    preprocessed_path = artifacts_root / "preprocessed.csv"

    if preprocessed_path.exists():
        print(f"Chargement des artefacts prétraités depuis {preprocessed_path}...")
        df_processed = pd.read_csv(preprocessed_path, index_col=0)
    else:
        print("Préprocessing des données (aucun artefact trouvé, exécution du pipeline)...")
        df_processed = preprocess_maritime_data(df)
    
    # Séparer features et cible
    X = df_processed.drop(columns=["Annulation"], errors="ignore")
    
    # Filtrer les colonnes non-numériques (datetime, object, etc.)
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    X = X[numeric_cols]
    
    y = df_processed["Annulation"]
    
    print(f"Données préparées : {X.shape[0]} lignes, {X.shape[1]} features")
    print(f"Distribution cible : {y.value_counts().to_dict()}")
    
    return X, y


def train_model(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42) -> dict:
    """
    Entraîne un modèle RandomForest et évalue ses performances.
    """
    print("\nSplit train/test...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    print(f"Train : {X_train.shape[0]} samples | Test : {X_test.shape[0]} samples")
    
    print("\nEntraînement du modèle RandomForest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Prédictions et évaluation
    y_pred = model.predict(X_test)
    
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }
    
    print(f"\n=== RÉSULTATS ===")
    print(f"Accuracy  : {metrics['accuracy']:.4f}")
    print(f"Precision : {metrics['precision']:.4f}")
    print(f"Recall    : {metrics['recall']:.4f}")
    print(f"F1-Score  : {metrics['f1']:.4f}")
    print(f"Confusion Matrix : {metrics['confusion_matrix']}")
    
    return {
        "model": model,
        "feature_names": X.columns.tolist(),
        "metrics": metrics,
        "n_features": X.shape[1],
    }


def save_artifacts(training_result: dict, output_dir: str = "artifacts") -> None:
    """
    Exporte le modèle et la configuration pour l'inférence.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    model = training_result["model"]
    feature_names = training_result["feature_names"]
    metrics = training_result["metrics"]
    
    # Sauvegarder le modèle
    model_file = output_path / "model.pkl"
    with open(model_file, "wb") as f:
        pickle.dump(model, f)
    print(f"\n✓ Modèle sauvegardé : {model_file}")
    
    # Sauvegarder les features et métadonnées
    features_file = output_path / "features.json"
    metadata = {
        "feature_names": feature_names,
        "n_features": training_result["n_features"],
        "model_type": "RandomForestClassifier",
        "metrics": {k: v for k, v in metrics.items() if k != "confusion_matrix"},
        "confusion_matrix": metrics["confusion_matrix"],
    }
    with open(features_file, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata sauvegardé : {features_file}")


def main():
    """Point d'entrée principal."""
    try:
        # Charger et préparer
        X, y = load_and_prepare_data()
        
        # Entraîner
        result = train_model(X, y)
        
        # Sauvegarder
        save_artifacts(result)
        
        print("\n✅ Pipeline d'entraînement terminé avec succès !")
        
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        raise


if __name__ == "__main__":
    main()
