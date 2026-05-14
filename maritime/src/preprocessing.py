"""Preparation des artefacts de pretraitement pour la modelisation.

Responsabilite:
- charger `maritime_clean.csv` ou un DataFrame equivalent
- appliquer le pipeline de `src.preprocessing_utils`
- exporter les artefacts de modelisation dans `artifacts/preprocessing/...`

Entrees:
- `maritime_clean.csv`, un CSV de ligne, ou un DataFrame en memoire

Sorties:
- CSV pretraite, CSV numerique, CSV reduit et metadata JSON

Commande:
- `python src/preprocessing.py`
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.paths import get_artifacts_dir, get_data_dir
from src.preprocessing_utils import preprocess_maritime_data


def _resolve_source(source: str | Path | pd.DataFrame | None) -> tuple[pd.DataFrame, str]:
    """Charge la source de données et retourne le DataFrame + un libellé d'entrée."""
    if source is None:
        source_path = get_data_dir() / "maritime_clean.csv"
        return pd.read_csv(source_path, index_col=0), source_path.stem

    if isinstance(source, pd.DataFrame):
        return source.copy(), "in_memory"

    source_path = Path(source)
    return pd.read_csv(source_path, index_col=0), source_path.stem


def _drop_reduced_columns(df: pd.DataFrame, prefixes: tuple[str, ...]) -> pd.DataFrame:
    """Supprime les familles de variables trop volumineuses pour certains essais."""
    columns_to_drop = [
        column
        for column in df.columns
        if any(column.startswith(prefix) for prefix in prefixes)
    ]
    return df.drop(columns=columns_to_drop, errors="ignore")


def prepare_modeling_artifacts(
    source: str | Path | pd.DataFrame | None = None,
    output_dir: str | Path | None = None,
    reduced_prefixes: tuple[str, ...] = ("Ciel_", "Bateau_", "Capitaine_"),
) -> dict[str, Any]:
    """Prépare les données et exporte les artefacts nécessaires à la modélisation.

    Retourne un dictionnaire contenant les DataFrames produits ainsi que les chemins
    d'export, afin de faciliter l'entraînement ou l'analyse locale.
    """
    raw_df, source_label = _resolve_source(source)
    processed_df = preprocess_maritime_data(raw_df)

    numeric_df = processed_df.select_dtypes(include=["number", "bool"]).copy()
    reduced_df = _drop_reduced_columns(numeric_df, reduced_prefixes)

    artifacts_root = Path(output_dir) if output_dir is not None else get_artifacts_dir() / "preprocessing" / source_label
    artifacts_root.mkdir(parents=True, exist_ok=True)

    processed_path = artifacts_root / "preprocessed.csv"
    numeric_path = artifacts_root / "preprocessed_numeric.csv"
    reduced_path = artifacts_root / "preprocessed_reduced.csv"
    metadata_path = artifacts_root / "metadata.json"

    processed_df.to_csv(processed_path, index=True)
    numeric_df.to_csv(numeric_path, index=True)
    reduced_df.to_csv(reduced_path, index=True)

    metadata = {
        "source": source_label,
        "input_rows": int(processed_df.shape[0]),
        "input_columns": processed_df.columns.tolist(),
        "numeric_columns": numeric_df.columns.tolist(),
        "reduced_columns": reduced_df.columns.tolist(),
        "reduced_prefixes": list(reduced_prefixes),
        "target_column": "Annulation" if "Annulation" in processed_df.columns else None,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "source_label": source_label,
        "processed_df": processed_df,
        "numeric_df": numeric_df,
        "reduced_df": reduced_df,
        "artifacts_dir": artifacts_root,
        "processed_path": processed_path,
        "numeric_path": numeric_path,
        "reduced_path": reduced_path,
        "metadata_path": metadata_path,
        "metadata": metadata,
    }


def main() -> None:
    """Point d'entrée CLI pour générer les artefacts de préprocessing."""
    result = prepare_modeling_artifacts()

    print(f"Artefacts générés dans : {result['artifacts_dir']}")
    print(f"- {result['processed_path'].name}")
    print(f"- {result['numeric_path'].name}")
    print(f"- {result['reduced_path'].name}")
    print(f"- {result['metadata_path'].name}")


if __name__ == "__main__":
    main()
