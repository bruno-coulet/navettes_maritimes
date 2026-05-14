"""Centralisation des chemins du projet maritime.

Responsabilite:
- resoudre la racine du projet
- fournir les dossiers `data/`, `data/lignes/` et `artifacts/`

Entrees:
- le systeme de fichiers courant ou le chemin du module

Sorties:
- objets `Path` reutilisables dans les scripts et notebooks

Commande:
- module utilitaire, pas de commande directe
"""

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()

    for candidate in (current, *current.parents):
        if (candidate / "src").exists() and (candidate / "data").exists():
            return candidate

    raise FileNotFoundError(f"Impossible de trouver la racine du projet depuis {current}")


def get_project_root() -> Path:
    return find_project_root(Path(__file__))


def get_data_dir() -> Path:
    return get_project_root() / "data"


def get_lignes_dir() -> Path:
    return get_data_dir() / "lignes"


def get_artifacts_dir() -> Path:
    return get_project_root() / "artifacts"
