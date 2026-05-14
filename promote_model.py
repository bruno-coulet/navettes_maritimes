#!/usr/bin/env python
"""
Promouvoir le modèle v1 Maritime en production.

Actions :
1. Copier model.pkl depuis v1_timestamp vers artifacts/model.pkl (officiel)
2. Copier features.json vers artifacts/features.json
3. Archiver ancien modèle
4. Mettre à jour .env si nécessaire
"""

import shutil
from pathlib import Path
from datetime import datetime

def promote_model_to_production():
    """Promeut v1 Maritime en modèle officiel."""
    
    print("="*60)
    print("PROMOTION : v1 Maritime → Production")
    print("="*60)
    
    # Chemins
    maritime_dir = Path("maritime")
    v1_dir = maritime_dir / "artifacts" / "models_v1_20260513_145955"
    prod_model = maritime_dir / "artifacts" / "model.pkl"
    prod_features = maritime_dir / "artifacts" / "features.json"
    
    if not v1_dir.exists():
        print(f"❌ Dossier v1 non trouvé : {v1_dir}")
        return
    
    # Archiver ancien modèle si existe
    if prod_model.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = maritime_dir / "artifacts" / f"model_backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        print(f"\n[1/3] Archivage ancien modèle...")
        shutil.copy(prod_model, backup_dir / "model.pkl")
        shutil.copy(prod_features, backup_dir / "features.json")
        print(f"  ✓ Sauvegardé dans {backup_dir}")
    
    # Copier v1 en production
    print(f"\n[2/3] Copie v1 → Production...")
    shutil.copy(v1_dir / "model.pkl", prod_model)
    shutil.copy(v1_dir / "features.json", prod_features)
    print(f"  ✓ {prod_model}")
    print(f"  ✓ {prod_features}")
    
    # Récapitulatif
    print(f"\n[3/3] Validation...")
    import json
    with open(prod_features) as f:
        features = json.load(f)
    
    print(f"\n✓ PROMOTION COMPLÉTÉE")
    print(f"{'='*60}")
    print(f"Modèle : Maritime v1")
    print(f"Accuracy : {features['metrics']['accuracy']:.4f}")
    print(f"F1-Score : {features['metrics']['f1']:.4f}")
    print(f"Features : {features['n_features']}")
    print(f"{'='*60}")
    
    print(f"\n✅ Modèle officiel updated. Redémarrez navettes API pour charger le nouveau modèle.")


if __name__ == "__main__":
    promote_model_to_production()
