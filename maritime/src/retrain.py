#!/usr/bin/env python
"""
Réentraînement du modèle Maritime avec versioning.

Utilise train_annulation.py existant mais ajoute versioning et comparaison.

Usage:
  python -m src.retrain [--version v1] [--data-source maritime]
  python -m src.retrain --version v2 --data-source openmeteo
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from maritime.src.features_v1 import load_and_prepare_data, train_model, save_artifacts


def retrain(version="v1", data_source="maritime", csv_path=None):
    """
    Réentraîne le modèle avec versioning et sauvegarde comparatif.
    
    Parameters:
    -----------
    version : str
        Identifiant de la version (ex: "v1", "v2_openmeteo")
    data_source : str
        Source de données ("maritime" ou "openmeteo")
    csv_path : str, optional
        Chemin personnalisé vers le CSV à utiliser
    """
    
    print(f"\n{'='*60}")
    print(f"RÉENTRAÎNEMENT : {version} (source: {data_source})")
    print(f"{'='*60}\n")
    
    # 1. Charger et préparer les données
    print(f"[1/4] Chargement des données ({data_source})...")
    X, y = load_and_prepare_data(csv_path=csv_path)
    
    # 2. Entraîner
    print(f"\n[2/4] Entraînement du modèle...")
    training_result = train_model(X, y)
    
    # 3. Créer dossier de version
    print(f"\n[3/4] Préparation des artefacts...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_dir = Path("artifacts") / f"models_{version}_{timestamp}"
    versioned_dir.mkdir(parents=True, exist_ok=True)
    
    # 4. Sauvegarder avec métadonnées de version
    print(f"\n[4/4] Sauvegarde des artefacts...")
    save_artifacts(training_result, output_dir=str(versioned_dir))
    
    # Ajouter metadata de version et comparaison
    version_info = {
        "version": version,
        "timestamp": timestamp,
        "data_source": data_source,
        "csv_path": str(csv_path) if csv_path else "default",
        "metrics": training_result["metrics"],
        "n_samples": X.shape[0],
        "n_features": training_result["n_features"],
    }
    
    version_file = versioned_dir / "version.json"
    with open(version_file, "w") as f:
        json.dump(version_info, f, indent=2)
    
    print(f"\n✓ Modèle {version} sauvegardé dans {versioned_dir}")
    print(f"  - model.pkl")
    print(f"  - features.json")
    print(f"  - version.json (metadata)")
    
    # Afficher résumé
    print(f"\n=== RÉSUMÉ ===")
    print(f"Version: {version}")
    print(f"Accuracy: {training_result['metrics']['accuracy']:.4f}")
    print(f"F1-Score: {training_result['metrics']['f1']:.4f}")
    print(f"Features: {training_result['n_features']}")
    
    return versioned_dir


def compare_versions(version1_dir, version2_dir):
    """Compare deux versions de modèles."""
    print(f"\n{'='*60}")
    print(f"COMPARAISON : {version1_dir.name} vs {version2_dir.name}")
    print(f"{'='*60}\n")
    
    with open(version1_dir / "version.json") as f:
        v1 = json.load(f)
    with open(version2_dir / "version.json") as f:
        v2 = json.load(f)
    
    m1 = v1["metrics"]
    m2 = v2["metrics"]
    
    print(f"{'Métrique':<15} {'Version 1':<15} {'Version 2':<15} {'Δ':<10}")
    print("-" * 55)
    for key in ["accuracy", "precision", "recall", "f1"]:
        v1_val = m1.get(key, 0)
        v2_val = m2.get(key, 0)
        delta = v2_val - v1_val
        delta_str = f"{delta:+.4f}"
        print(f"{key:<15} {v1_val:<15.4f} {v2_val:<15.4f} {delta_str:<10}")
    
    winner = "Version 2" if m2["f1"] > m1["f1"] else "Version 1"
    print(f"\n✓ Meilleur modèle (F1) : {winner}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Réentraîner le modèle Navettes Maritimes")
    parser.add_argument("--version", default="v1", help="Identifiant de version (ex: v1, v2_openmeteo)")
    parser.add_argument("--data-source", default="maritime", help="Source de données (maritime, openmeteo)")
    parser.add_argument("--csv-path", default=None, help="Chemin personnalisé vers le CSV")
    parser.add_argument("--compare", nargs=2, help="Comparer deux versions (paths)")
    
    args = parser.parse_args()
    
    if args.compare:
        compare_versions(Path(args.compare[0]), Path(args.compare[1]))
    else:
        retrain(version=args.version, data_source=args.data_source, csv_path=args.csv_path)
