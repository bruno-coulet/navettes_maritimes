#!/usr/bin/env python
"""
ENTRAÎNEMENT V1 (Baseline Maritime)
-----------------------------------
Ce script entraîne le modèle original basé sur les données historiques
maritimes (consolidation_maritime.xlsx).

Il produit désormais un fichier 'metrics_v1.json' avec une structure
standardisée pour faciliter la comparaison avec la V2 et la V3.
"""

import json
from pathlib import Path
from datetime import datetime
# On garde ton import existant pour la logique métier
from features_v1 import load_and_prepare_data, train_model

# === CONFIGURATION ===
BASE_DIR = Path(__file__).resolve().parents[2]
MARITIME_DIR = BASE_DIR / "maritime"
ARTIFACTS_DIR = MARITIME_DIR / "artifacts"
# On crée un dossier spécifique pour cette exécution
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR = ARTIFACTS_DIR / f"run_v1_{TIMESTAMP}"

def main():
    print("="*60)
    print(f"ENTRAÎNEMENT V1 : Baseline Maritime")
    print("="*60)

    # 1. Chargement des données
    X, y = load_and_prepare_data()

    # 2. Entraînement
    print(f"[2/4] Entraînement du modèle...")

    # On récupère l'unique dictionnaire renvoyé
    results = train_model(X, y)

    # Extraction depuis le dictionnaire (on adapte aux clés probables)
    # Si c'est un dictionnaire, les clés sont sûrement 'model' et 'metrics'
    model = results.get('model')
    metrics = results.get('metrics', results) # Si pas de clé metrics, c'est que results est le dictionnaire de métriques

    # 3. Préparation des métriques UNIFORMISÉES
    output_metrics = {
        "accuracy": metrics.get("accuracy", 0),
        "precision": metrics.get("precision", 0),
        "recall": metrics.get("recall", 0),
        "f1": metrics.get("f1", 0),
        "n_samples": len(X),
        "n_features": len(X.columns),
        "run_date": datetime.now().isoformat()
    }

    # 4. Sauvegarde
    print(f"[3/4] Sauvegarde des artifacts...")
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    # Sauvegarde metrics_v1.json (Dossier run + Racine artifacts)
    for target_path in [RUN_DIR / "metrics_v1.json", ARTIFACTS_DIR / "metrics_v1.json"]:
        with open(target_path, "w") as f:
            json.dump(output_metrics, f, ensure_ascii=False, indent=4)

    # Sauvegarde model_v1.pkl
    import joblib
    joblib.dump(model, ARTIFACTS_DIR / "model_v1.pkl")

    print(f"\n✅ TERMINÉ")
    print(f"📊 Métriques prêtes : {ARTIFACTS_DIR}/metrics_v1.json")

if __name__ == "__main__":
    main()