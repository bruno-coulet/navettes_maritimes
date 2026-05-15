# Structure du projet

## Organisation des fichiers

```
.
├── main.py                 # Compatibilité ascendante (wrapper)
├── src/pipeline.py         # Pipeline complet (collecte + consolidation + split)
├── src/collect.py          # Collecte des données open_meteo
├── src/consolidate.py      # Consolidation des fichiers mensuels
├── src/split.py            # Création des splits train/val/test
├── src/utils.py            # Classe MeteoMarineMarseille et fonctions utilitaires
├── pyproject.toml         # Dépendances (uv)
├── Dockerfile             # Image Docker
├── docker-compose.yml     # Orchestration
├── Makefile              # Commandes utiles
├── .gitignore            # Fichiers à ignorer
└── data/
    ├── raw/              # Données brutes (organisées par année)
    │   ├── 2024/         # Fichiers CSV de 2024
    │   ├── 2025/         # Fichiers CSV de 2025
    │   └── 2026/         # Fichiers CSV de 2026
    └── processed/        # Données consolidées pour ML
```

## Fichiers principaux

### `src/pipeline.py`
- **Orchestration du pipeline complet**
- Appelle `src.collect`, `src.consolidate`, puis `src.split`
- Exécution: `python -m src.pipeline` ou `uv run -m src.pipeline`

### `main.py`
- Wrapper de compatibilité vers `src.pipeline`
- Exécution historique conservée temporairement

### `src/collect.py`
- **Point d'entrée de la collecte** des données open_meteo
- Constantes: `START_DATE`, `END_DATE`
- Exécution: `python -m src.collect` ou `uv run -m src.collect`

### `src/utils.py`
- **Classe `MeteoMarineMarseille`** avec méthodes:
  - `get_marine_weather_open_meteo()` - Vagues
  - `get_weather_data_open_meteo()` - Météo générale
  - `collect_historical_data_batch()` - Collecte par lots
  - `process_to_daily_summary()` - Traitement quotidien
  - `save_data()` - Sauvegarde organisée

### `src/consolidate.py`
- Étape 2: Fusion des données mensuelles
- Génère `data/processed/consolidated_YYYY_MM_DD-au-MM_DD.parquet`
- Exécution: `python -m src.consolidate` ou `uv run -m src.consolidate`

### `src/split.py`
- Étape 3: Création des splits train/val/test
- Lit le dernier fichier consolidé dans `data/processed/`
- Exécution: `python -m src.split` ou `uv run -m src.split`

## Workflow de développement

### Localement (recommandé pour le développement)

```bash
# Installation
uv sync

# Collecte données
uv run -m src.collect

# Consolidation
uv run -m src.consolidate

# Split ML
uv run -m src.split

# Pipeline complet
uv run -m src.pipeline
```

### Avec Make

```bash
make install
make collect
make consolidate
```

### Avec Docker

```bash
make docker-build
docker compose run --rm collect-data
docker compose run --rm consolidate-data
```

## Avantages de cette structure

✅ **Séparation des responsabilités**
- `src/pipeline.py` : orchestration du pipeline
- `main.py` : wrapper de compatibilité
- `src/collect.py` : collecte open_meteo
- `src/consolidate.py` : consolidation
- `src/split.py` : split ML
- `src/utils.py` : logique métier

✅ **Facilité de test**
- Les fonctions sont isolées dans `utils.py`
- Facile à mocker et tester

✅ **Réutilisabilité**
- `src.utils.MeteoMarineMarseille` peut être importée ailleurs
- `src/consolidate.py` et `src/split.py` exécutables séparément

✅ **Maintenabilité**
- Code lisible et organisé
- Facile d'ajouter de nouvelles fonctionnalités

## Imports

```python
# Dans src.pipeline ou tout autre fichier
from src.utils import MeteoMarineMarseille

# Utilisation
client = MeteoMarineMarseille()
data = client.collect_historical_data_batch(start, end)
```
