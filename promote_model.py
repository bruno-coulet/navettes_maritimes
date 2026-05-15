#!/usr/bin/env python
"""
MLOps : Script de Promotion du Modèle (Champion vs Challenger)

LOGIQUE DU SCRIPT :
------------------
1. RÉFÉRENTIEL (Champion) : modèle actuellement utilisé en production (dossier /production).
2. NOUVEAU (Challenger) : modèle nouvellement entraîner (ex: V3, V4...).
3. CRITÈRE DE VALIDATION : Le script compare le 'Recall'. Si le Challenger fait mieux,
   il est "promu" : on archive l'ancien et on place le nouveau en production.

L'intérêt est d'automatiser le passage en production tout en ayant un filet de sécurité.
"""

import shutil
import json
from pathlib import Path
from datetime import datetime

# === CONFIGURATION DES CHEMINS ===
BASE_DIR = Path(__file__).resolve().parent

# Le Challenger (la V3 que tu viens de finir)
CHALLENGER_DIR = BASE_DIR / "open_meteo" / "artifacts"
CHALLENGER_METRICS = CHALLENGER_DIR / "metrics_v3.json"
CHALLENGER_MODEL = CHALLENGER_DIR / "model_v3.pkl"

# La Production (Le modèle qui sera lu par l'application finale)
PROD_DIR = BASE_DIR / "production"
PROD_METRICS = PROD_DIR / "metrics_live.json"
PROD_MODEL = PROD_DIR / "model_live.pkl"

def load_metrics(path):
    """Charge les métriques d'un fichier JSON. Retourne None si absent."""
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Gère le fait que V1/V2 ont une clé 'metrics', pas V3
        return data.get("metrics", data)

def promote():
    """
    Compare le nouveau modèle au modèle en production et effectue la promotion
    si les performances sont supérieures.
    """
    print("="*60)
    print("PIPELINE DE PROMOTION : CHALLENGER vs CHAMPION")
    print("="*60)

    # 1. Chargement des scores
    m_challenger = load_metrics(CHALLENGER_METRICS)
    m_champion = load_metrics(PROD_METRICS)

    if not m_challenger:
        print("Erreur : Impossible de trouver les métriques du Challenger (V3).")
        return

    # 2. Logique de décision
    should_promote = False
    
    if m_champion is None:
        print("Aucun modèle en production. Promotion automatique.")
        should_promote = True
    else:
        # On compare sur le RECALL (crucial pour les annulations maritimes)
        score_new = m_challenger.get('recall', 0)
        score_old = m_champion.get('recall', 0)
        
        print(f"Recall Challenger : {score_new:.4f}")
        print(f"Recall Champion   : {score_old:.4f}")

        if score_new > score_old:
            print(f"Amélioration détectée (+{score_new - score_old:.4f})")
            should_promote = True
        else:
            print("Le Challenger n'est pas meilleur. Promotion annulée.")

    # 3. Action de Promotion
    if should_promote:
        PROD_DIR.mkdir(exist_ok=True)

        # Archivage de l'ancien modèle si existant
        if PROD_MODEL.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = PROD_DIR / f"model_backup_{timestamp}.pkl"
            shutil.move(PROD_MODEL, backup_name)
            print(f"📦 Ancien modèle archivé : {backup_name.name}")

        # Copie du nouveau modèle en Production
        shutil.copy(CHALLENGER_MODEL, PROD_MODEL)
        shutil.copy(CHALLENGER_METRICS, PROD_METRICS)
        
        print(f"\nSUCCÈS : Le modèle V3 est désormais le modèle officiel (Live) !")
        print(f"Destination : {PROD_DIR.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    promote()