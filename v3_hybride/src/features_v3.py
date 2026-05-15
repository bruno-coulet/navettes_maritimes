"""
features V3 : conserver TOUTES les features métier + ajouter météo open_meteo

Grain = 1 traversée (pas agrégé)

Objectif :
- garder 136 features métier
- ajouter météo API alignée temporellement
"""

import pandas as pd
from pathlib import Path

# ==============================================================================
# DEFINITIONS POUR L'IMPORT (Utilisé par train_v3.py)
# ==============================================================================

TARGET = "Annulation"

FEATURES_V3 = [
    # Métier
    'Capitaine', 'Bateau', 'Ligne', 'HouleMax', 'HoulePeriode', 
    'Ciel', 'Mer', 'Vent', 'HouleDominante',
    # Open-Meteo
    'wave_height_max', 'wave_direction_dominant', 'wave_period_max',
    'wind_wave_height_max', 'swell_wave_height_max', 'temperature_max',
    'temperature_min', 'wind_speed_max', 'wind_gusts_max'
]

if __name__ == "__main__":

    print("=" * 70)
    print("MERGE V3 : Maritime (complet) + open_meteo")
    print("=" * 70)


    # =========================
    # 1. Chargement données
    # =========================

    maritime_path = Path("maritime/data/maritime_clean.csv")
    meteo_path = Path("open_meteo/data/processed/consolidated_2024_01_01-au-2026_04_30.parquet")

    maritime_df = pd.read_csv(maritime_path)
    meteo_df = pd.read_parquet(meteo_path)

    # =========================
    # 2. Préparation timestamps
    # =========================

    maritime_df["Horaire"] = pd.to_datetime(maritime_df["Horaire"])
    # On normalise à la date (00:00:00) pour tout le monde
    # Toutes les navettes du 12 mai auront la même valeur 2026-05-12 00:00:00
    # dans la colonne datetime_round.
    maritime_df["datetime_round"] = maritime_df["Horaire"].dt.normalize()

    # On crée une colonne date arrondie à l’heure (ou jour selon granularité meteo)
    # maritime_df["datetime_round"] = maritime_df["Horaire"].dt.floor("h")

    meteo_df["date"] = pd.to_datetime(meteo_df["date"])

    # Si meteo = daily :
    meteo_df["datetime_round"] = meteo_df["date"]

    # =========================
    # 3. Merge
    # =========================

    print("\n[1/3] Merge maritime + météo...")

    merged = pd.merge(
        maritime_df,
        meteo_df,
        on="datetime_round",
        how="inner"
    )

    print(f"Shape après merge : {merged.shape}")

    # =========================
    # 4. Nettoyage
    # =========================

    # Drop colonnes inutiles si doublons
    cols_to_drop = ["date"]
    merged = merged.drop(columns=[c for c in cols_to_drop if c in merged.columns])

    # =========================
    # 5. Target
    # =========================

    # Si déjà binaire : OK
    # Sinon option :

    merged["Annulation"] = merged["Annulation"].astype(int)

    print(f"Taux annulation : {merged['Annulation'].mean() * 100:.2f}%")

    # =========================
    # 6. Sauvegarde
    # =========================

    output_path = Path("open_meteo/data/processed/training_merged_v3.parquet")
    merged.to_parquet(output_path, index=False)

    print(f"\n✅ Dataset V3 sauvegardé : {output_path}")
    print(f"Colonnes: {len(merged.columns)}")

    print("\n" + "=" * 70)
    print("✅ MERGE V3 TERMINÉ")
    print("=" * 70)


