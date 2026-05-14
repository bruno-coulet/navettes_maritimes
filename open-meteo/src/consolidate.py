"""Consolidation des fichiers mensuels meteo marine.

Responsabilite:
- fusionner les exports mensuels en un seul jeu exploitable pour le ML
- optimiser quelques types de colonnes pour reduire la memoire

Entrees:
- fichiers mensuels produits dans `data/raw/`

Sorties:
- fichier consolide dans `data/processed/`

Commande:
- `python -m src.consolidate`
- ou execution via `src.pipeline`
"""

import pandas as pd
from pathlib import Path


def _display_path(path: Path) -> str:
    """Retourne un chemin lisible, relatif au projet quand possible."""
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _optimize_memory_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Réduit l'empreinte mémoire des colonnes numériques sans perte métier notable."""
    optimized = df.copy()

    float_cols = optimized.select_dtypes(include=["float64"]).columns
    if len(float_cols) > 0:
        optimized[float_cols] = optimized[float_cols].astype("float32")

    int_cols = optimized.select_dtypes(include=["int64", "int32"]).columns
    for col in int_cols:
        col_min = optimized[col].min()
        col_max = optimized[col].max()

        if col_min >= 0 and col_max <= 65535:
            optimized[col] = optimized[col].astype("uint16")
        elif -32768 <= col_min <= col_max <= 32767:
            optimized[col] = optimized[col].astype("int16")
        elif -2147483648 <= col_min <= col_max <= 2147483647:
            optimized[col] = optimized[col].astype("int32")

    return optimized

def consolidate_monthly_data():
    """
    Consolide tous les fichiers CSV mensuels de data/raw/ en un seul fichier
    Sauvegarde dans data/processed/consolidated-start-date-au-end-date.parquet
    """
    
    # Parcours tous les fichiers CSV dans data/raw/
    raw_dir = Path("data/raw")
    
    if not raw_dir.exists():
        print(f"Erreur: Le dossier {raw_dir} n'existe pas")
        print("Exécutez d'abord collect.py pour générer les données")
        return False
    
    # Récupération de tous les CSV
    csv_files = sorted(raw_dir.glob("**/meteo_*.csv"))
    
    if not csv_files:
        print(f"Aucun fichier CSV trouvé dans {raw_dir}")
        return False
    
    print(f"=== CONSOLIDATION DES DONNÉES ===")
    print(f"Nombre de fichiers à fusionner: {len(csv_files)}\n")
    
    # Lecture et fusion de tous les fichiers
    dataframes = []
    total_rows = 0
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            print(f"✓ Lecture: {_display_path(csv_file)} ({len(df)} lignes)")
            dataframes.append(df)
            total_rows += len(df)
        except Exception as e:
            print(f"✗ Erreur lecture {_display_path(csv_file)}: {e}")
            continue
    
    if not dataframes:
        print("Aucun fichier n'a pu être lu")
        return False
    
    # Fusion des DataFrames
    print(f"\nFusion de {len(dataframes)} fichiers...")
    consolidated_df = pd.concat(dataframes, ignore_index=True)
    
    # Suppression des doublons si présents
    initial_rows = len(consolidated_df)
    consolidated_df = consolidated_df.drop_duplicates(subset=['date'], keep='first')
    duplicates_removed = initial_rows - len(consolidated_df)
    
    if duplicates_removed > 0:
        print(f"Doublons supprimés: {duplicates_removed}")
    
    # Tri par date
    if 'date' in consolidated_df.columns:
        consolidated_df['date'] = pd.to_datetime(consolidated_df['date'])
        consolidated_df = consolidated_df.sort_values('date').reset_index(drop=True)

    # Optimisation mémoire (float64 -> float32, int64 -> uint16/int16/int32)
    memory_before = consolidated_df.memory_usage(deep=True).sum()
    consolidated_df = _optimize_memory_dtypes(consolidated_df)
    memory_after = consolidated_df.memory_usage(deep=True).sum()
    if memory_before > 0:
        gain_pct = (memory_before - memory_after) / memory_before * 100
        print(
            f"Optimisation mémoire: {memory_before / 1024:.1f} KB -> {memory_after / 1024:.1f} KB ({gain_pct:.1f}%)"
        )
    
    # Création du dossier processed/
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarde du fichier consolidé avec plage de dates dans le nom (Parquet)
    if 'date' in consolidated_df.columns and not consolidated_df.empty:
        start_str = consolidated_df['date'].min().strftime("%Y_%m_%d")
        end_str = consolidated_df['date'].max().strftime("%m_%d")
        output_filename = f"consolidated_{start_str}-au-{end_str}.parquet"
    else:
        output_filename = "consolidated.parquet"

    output_file = processed_dir / output_filename
    consolidated_df.to_parquet(output_file, index=False, engine="fastparquet")
    
    print(f"\n=== RÉSULTATS ===")
    print(f"✓ Fichier consolidé: {output_file}")
    print(f"Total de lignes: {len(consolidated_df)}")
    print(f"Plage temporelle: {consolidated_df['date'].min()} à {consolidated_df['date'].max()}")
    print(f"\nDimensions: {consolidated_df.shape}")
    print(f"Colonnes: {', '.join(consolidated_df.columns.tolist())}")
    
    # Statistiques
    print(f"\n=== STATISTIQUES ===")
    numeric_cols = consolidated_df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        print(consolidated_df[numeric_cols].describe())
    else:
        print("Aucune colonne numérique disponible pour les statistiques.")
    
    return True


def main():
    """Point d'entrée du script de consolidation."""
    if not consolidate_monthly_data():
        print("Consolidation échouée")


if __name__ == "__main__":
    main()
