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
- `uv run python -m v2_meteo.src.pipeline`
"""

from pathlib import Path

import v2_meteo.src.a_collect_meteo as a_collect_meteo
import v2_meteo.src.b_consolidate as b_consolidate
import v2_meteo.src.c_features_v2 as c_features_v2
import v2_meteo.src.d_train_v2 as train_v2


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_pipeline():
    print("DÉMARRAGE DU PIPELINE MÉTÉO MARINE")
    print(f"Projet: {PROJECT_ROOT}")
    print("-" * 40)

    print("\n1/4 : Collecte des données...")
    a_collect_meteo.main()

    print("\n2/4 : Consolidation des fichiers...")
    b_consolidate.main()

    print("\n3/4 : sélection des features...")
    c_features_v2.main()

    print("\n4/4 : split et train...")
    train_v2.main()

    print("\nPIPELINE V2 TERMINÉ AVEC SUCCÈS")


def main():
    run_pipeline()


if __name__ == "__main__":
    main()