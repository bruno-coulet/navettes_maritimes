#!/usr/bin/env python
"""Script de nettoyage et anonymisation des données maritimes.

Reproduit le workflow de notebooks/01_cleaning.ipynb avec ajout de l'anonymisation.

Responsabilité:
- charger le fichier source brut `data/consolidation_maritime.xlsx`
- nettoyer les colonnes horaires et météo
- anonymiser la colonne "Capitaine"
- produire la base propre commune au projet maritime

Entrées:
- `data/consolidation_maritime.xlsx`

Sorties:
- `data/maritime_clean.csv` (avec Capitaine anonymisé)

Commande:
- python -m src.run_cleaning
- ou: python src/run_cleaning.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Configuration du path pour les imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd

from src.paths import get_data_dir
from src.cleaning_utils import (
    load_raw_data,
    clean_raw_data,
    reorganize_columns,
    anonymize_capitaine,
)


def run_cleaning(verbose: bool = True) -> pd.DataFrame:
    """Exécute le pipeline complet de nettoyage et anonymisation.
    
    Parameters
    ----------
    verbose : bool, optional
        Affiche les étapes du traitement (défaut: True)
        
    Returns
    -------
    pd.DataFrame
        DataFrame nettoyé et anonymisé exporté en CSV
    """
    data_dir = get_data_dir()
    source_path = data_dir / "consolidation_maritime.xlsx"
    output_path = data_dir / "maritime_clean.csv"
    
    if verbose:
        print(f"[1/5] Localisation du projet: {project_root}")
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source Excel introuvable: {source_path}")
    
    if verbose:
        print(f"[2/5] Chargement: {source_path}")
    df = load_raw_data(source_path)
    initial_rows = len(df)
    
    if verbose:
        print(f"      Lignes chargées: {initial_rows}")
        print(f"[3/5] Nettoyage des données")
    df = clean_raw_data(df)
    cleaned_rows = len(df)
    
    if verbose:
        print(f"      Lignes après nettoyage: {cleaned_rows}")
        print(f"[4/5] Réorganisation des colonnes")
    df = reorganize_columns(df)
    
    if verbose:
        print(f"[5/5] Anonymisation de la colonne 'Capitaine'")
    df["Capitaine"] = df["Capitaine"].apply(anonymize_capitaine)
    
    if verbose:
        print(f"      Premiers IDs anonymisés: {df['Capitaine'].head(3).tolist()}")
        print(f"[Export] Sauvegarde en CSV: {output_path}")
    df.to_csv(output_path, index=True)
    
    if verbose:
        print(f"✓ Pipeline terminé avec succès")
        print(f"  Lignes initiales: {initial_rows}")
        print(f"  Lignes exportées: {cleaned_rows}")
    
    return df


if __name__ == "__main__":
    run_cleaning(verbose=True)
