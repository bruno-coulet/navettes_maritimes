"""Creation des splits train/val/test pour le ML.

Responsabilite:
- repartir le fichier consolide en jeux d'apprentissage, validation et test
- conserver une repartition stable et reproductible

Entrees:
- fichier consolide dans `data/processed/`

Sorties:
- CSV de splits dans `data/processed/`

Commande:
- `python -m src.split`
- ou execution via `src.pipeline`
"""

from pathlib import Path
from random import Random

import pandas as pd


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


def create_ml_splits(train_ratio=0.7, val_ratio=0.15, random_state=42):
    """
    Crée les splits train/val/test à partir du fichier consolidé.
    Par défaut: 70% train, 15% val, 15% test.
    """
    processed_dir = Path("data/processed")
    # Recherche le dernier fichier consolidé au format Parquet
    candidates = sorted(processed_dir.rglob("consolidated*.parquet"))

    if not candidates:
        print("Erreur: aucun fichier consolidé trouvé dans data/processed")
        print("Exécutez d'abord consolidate.py")
        return False

    consolidated_file = candidates[-1]

    df = pd.read_parquet(consolidated_file, engine="fastparquet")
    df = _optimize_memory_dtypes(df)
    print("\n=== CRÉATION DES SPLITS TRAIN/VAL/TEST ===")
    print(f"Données totales: {len(df)} lignes")

    indices = df.index.tolist()
    rng = Random(random_state)
    rng.shuffle(indices)

    n = len(df)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]

    train_df = df.iloc[train_idx].sort_index().reset_index(drop=True)
    val_df = df.iloc[val_idx].sort_index().reset_index(drop=True)
    test_df = df.iloc[test_idx].sort_index().reset_index(drop=True)

    processed_dir.mkdir(parents=True, exist_ok=True)

    train_file = processed_dir / "train.parquet"
    val_file = processed_dir / "val.parquet"
    test_file = processed_dir / "test.parquet"

    train_df.to_parquet(train_file, index=False, engine="fastparquet")
    val_df.to_parquet(val_file, index=False, engine="fastparquet")
    test_df.to_parquet(test_file, index=False, engine="fastparquet")

    print(f"✓ Train: {len(train_df)} lignes ({train_ratio*100:.0f}%) → {train_file}")
    print(f"✓ Val: {len(val_df)} lignes ({val_ratio*100:.0f}%) → {val_file}")
    print(f"✓ Test: {len(test_df)} lignes ({(1-train_ratio-val_ratio)*100:.0f}%) → {test_file}")

    return True


def main():
    """Point d'entrée du script de split."""
    if not create_ml_splits():
        print("Création des splits échouée")


if __name__ == "__main__":
    main()
