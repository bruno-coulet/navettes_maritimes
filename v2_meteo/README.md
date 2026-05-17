# Météo Marine Marseille - ML Classification (Pipeline V2)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tool: uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Outil de collecte, de consolidation et d'entraînement (Machine Learning) pour la prédiction des annulations de navettes maritimes à Marseille via l'API open-meteo.

**Nouveauté V2 :** Ce pipeline corrige les biais de la V1 en agrégeant les annulations quotidiennes par la moyenne (`mean()`) au lieu du maximum (`max()`), ramenant la distribution de la variable cible à sa réalité terrain (16.6% d'annulations).

---

## Architecture Orchestrée (Docker)

Ce projet peut s'intégrer dans une architecture de **3 services Docker** orchestrés qui communiquent via des volumes partagés :

```text
meteo_marine (collecte)
      ↓
      data/processed/ (données consolidées)
      ↓
maritime (entraînement modèle)
      ↓
      artifacts/ (model.pkl + features.json)
      ↓
navettes (API de prédiction)
      ↓
      Port 8000 (Swagger : /docs)

```

## Installation Rapide (Local)

Le pipeline principal utilise open_meteo et ne nécessite pas de clé API.

```bash
# 1. Installation des dépendances avec uv
uv sync

# 2. Exécution du pipeline complet (Recommandé)
uv run python -m v2_meteo.src.pipeline

# 3. Comparaison des modèles (V1 vs V2)
uv run python compare_versions.py

```

---

## Chronologie d'exécution (Pipeline V2)

Le projet suit un flux d'exécution strict, modulaire et reproductible. Chaque étape a une responsabilité unique :

1. **Collecte (`a_collect_meteo.py`)** : Récupération des données brutes open-meteo (Marine + ERA5) → `data/raw/`.
2. **Consolidation (`b_consolidate.py`)** : Fusion, nettoyage et optimisation mémoire → `data/processed/consolidated_*.parquet`.
3. **Features Merge (`c_features_v2.py`)** : Croisement avec l'historique d'exploitation maritime, agrégation quotidienne, génération de la cible binaire (seuil 16.6%), et split Train/Val/Test.
4. **Entraînement (`d_train_v2.py`)** : Entraînement du modèle RandomForest V2 et sauvegarde des artefacts.
5. **Orchestrateur (`pipeline.py`)** : Lance automatiquement les étapes A, B, C et D à la chaîne.

### Exécution étape par étape

Si vous souhaitez lancer les modules individuellement :

```bash
uv run python -m v2_meteo.src.a_collect_meteo
uv run python -m v2_meteo.src.b_consolidate
uv run python -m v2_meteo.src.c_features_v2
uv run python -m v2_meteo.src.d_train_v2

```

### Features Météo collectées :

* **Marine** : Hauteur, Direction, Période des vagues, Houle dominante.
* **Météo** : Température (min/max), Vent (vitesse, rafales, direction).

---

## Configuration Proxy (Réseau d'entreprise)

Si le réseau bloque l'accès direct à open_meteo, ajoutez vos variables de proxy dans un fichier `.env` local à la racine du projet :

```env
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port

```

*(Note : Si le proxy demande une authentification, utilisez le format `http://utilisateur:motdepasse@proxy:port`)*.

Pour tester le comportement du proxy localement :

```bash
# Affiche les valeurs de configuration proxy
export METEO_EXAMPLE_PROXY=1
uv run python main.py

```

## Performance & Stockage

L'utilisation du format Parquet (`fastparquet`) couplée à l'optimisation des types (`float32`, `uint16`) permet des performances optimales :

| Opération | Temps estimé | Taille disque |
| --- | --- | --- |
| Collecte 31 jours | ~2-3 min | ~5-10 KB (CSV) |
| Consolidation annuelle | ~2-5 sec | ~150-200 KB (Parquet) |
| Chargement ML (Train) | < 50 ms | ~70-120 KB (Parquet) |

## Documentation Additionnelle

* [README_ML.md](https://www.google.com/search?q=documentation/README_ML.md) : Guide spécifique pour l'entraînement des modèles.
* [UTILS_EXPLIQUE.md](https://www.google.com/search?q=documentation/UTILS_EXPLIQUE.md) : Détails de l'architecture du code utilitaire.
* [DOCKER.md](https://www.google.com/search?q=documentation/DOCKER.md) : Configuration des conteneurs.
* [DOCKER_EXPLIQUE.md](https://www.google.com/search?q=documentation/DOCKER_EXPLIQUE.md) : Explication détaillée de l'architecture Docker.

---

**Licence :** Ce projet est sous licence MIT.

**Auteur :** Bruno Coulet - *Projet réalisé en alternance IA*.

```

```