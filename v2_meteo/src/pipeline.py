"""Pipeline principal de collecte, consolidation et split.

Responsabilite:
- orchestrer la collecte des donnees brutes
- consolider les donnees mensuelles
- produire les splits train/val/test

Entrees:
- configuration des modules `collect`, `consolidate` et `split`

Sorties:
- donnees brutes, consolidees et splits ML dans `data/`

Commande:
- `python -m src.pipeline`
"""

from pathlib import Path

import v2_meteo.src.collect_meteo as collect_meteo
import src.consolidate as consolidate
import src.split as split


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_pipeline():
    print("DÉMARRAGE DU PIPELINE MÉTÉO MARINE")
    print(f"Projet: {PROJECT_ROOT}")
    print("-" * 40)

    # Étape 1 : Collecte
    print("\nÉTAPE 1 : Collecte des données...")
    collect_meteo.main()

    # Étape 2 : Consolidation
    print("\nÉTAPE 2 : Consolidation des fichiers...")
    consolidate.main()

    # Étape 3 : Split ML
    print("\nÉTAPE 3 : Création des splits train/val/test...")
    split.main()

    print("\nPIPELINE TERMINÉ AVEC SUCCÈS")


def main():
    run_pipeline()


if __name__ == "__main__":
    main()