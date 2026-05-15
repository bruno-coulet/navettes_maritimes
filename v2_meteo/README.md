# Météo Marine Marseille - ML Classification

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tool: uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Outil de collecte et de classification (Machine Learning) des données de météo marine de Marseille via l'API open-meteo.

---

## Architecture Orchestrée

Ce projet est composé de **3 services Docker** orchestrés qui communiquent via des volumes partagés :

```
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

### Services et Chemins

| Service | Rôle | Localisation | Entrée | Sortie | Port |
|---------|------|-------------|--------|--------|------|
| **meteo_marine_collect** | Collecte données brutes | `~/projets/navettes_maritimes/meteo_marine/` | open_meteo API | `data/processed/` | — |
| **maritime_model** | Entraîne RandomForest | `~/projets/navettes_maritimes/maritime/` | `maritime_clean.csv` | `artifacts/model.pkl` | — |
| **navettes_pred** | API de prédiction | `~/projets/navettes_maritimes/navettes/` | `model.pkl` | Predictions | **8000** |

### Ordre d'Exécution

1. **`meteo_marine_collect`** : Récupère la météo via open_meteo → `meteo_data:/app/data`
2. **`maritime_model`** : Entraîne le modèle sur données historiques → `maritime_artifacts:/app/artifacts`
3. **`navettes_pred`** : Démarre l'API (accède au modèle) sur port 8000

### Commandes de Lancement

#### Option 1 : Pipeline complète (Docker Compose, recommandé)

```bash
cd ~/projets/navettes_maritimes/
docker-compose -f docker-compose.orchestration.yml up --build
```

Cela lance les 3 services **dans l'ordre**, en respectant les dépendances. L'API sera accessible sur `http://localhost:8000`.

#### Option 2 : Services individuels

```bash
# Uniquement collecte
docker-compose -f docker-compose.orchestration.yml run meteo_marine_collect

# Uniquement entraînement (après collecte)
docker-compose -f docker-compose.orchestration.yml run maritime_model

# Uniquement API (après entraînement)
docker-compose -f docker-compose.orchestration.yml run navettes_pred
```

#### Option 3 : Développement local (sans Docker)

```bash
# meteo_marine : collecte + consolidation
cd ~/projets/meteo_marine/
uv sync && uv run -m src.pipeline

# maritime : entraînement
cd ~/projets/maritime/
pip install scikit-learn joblib pandas
python src/train_annulation.py

# navettes : API
cd ~/projets/navettes/
pip install fastapi uvicorn pandas
uvicorn src.predict_annulation:app --host 0.0.0.0 --port 8000
```

### Déploiement sur VPS

```bash
# Installation Docker
curl -sSL https://get.docker.com | sh

# Cloner les 3 repos dans ~/projets/
cd ~/projets/
docker-compose -f docker-compose.orchestration.yml up -d --build

# Monitoring
docker-compose -f docker-compose.orchestration.yml logs -f
```

**Scheduler automatique** (collecte + entraînement chaque nuit à 2h) :

```bash
# crontab -e
0 2 * * * cd ~/projets && docker-compose -f docker-compose.orchestration.yml run --rm meteo_marine_collect && docker-compose -f docker-compose.orchestration.yml run --rm maritime_model
```

---

## Objectif détaillé

Récupérer et organiser les données quotidiennes de météo marine (vagues, vent, température) pour un outil de prédiction des annulations de navettes maritimes de Marseille.

Le projet croise les données de vagues (Marine API) et les données atmosphériques (ERA5 Archive).

## Installation Rapide (Recommandé)

Le pipeline principal utilise open_meteo et ne nécessite pas de clé API.

Si votre environnement est derrière un proxy d'entreprise, créez un fichier local `.env`
à partir de [`.env.example`](.env.example) et renseignez `HTTP_PROXY` / `HTTPS_PROXY`.
Dans VS Code, activez aussi `python.terminal.useEnvFile` pour que le terminal intégré
injecte automatiquement les variables du fichier `.env`.

Il est normal que `HTTP_PROXY` et `HTTPS_PROXY` pointent vers le même serveur proxy.
Si le proxy demande une authentification, l'URL peut inclure les identifiants :
`http://utilisateur:motdepasse@proxy:port`.

```bash
# 1. Installation des dépendances avec uv
uv sync

# 2 : Pipeline complet (option A)
uv run -m src.pipeline

# 2 : étapes séparées  (option B)
# Collecte des données en fichiers mensuels
uv run -m src.collect
# Consolidation en un seul fichier
uv run -m src.consolidate
# Splits du fichier consolidé en jeu de train/val/test pour le Machine Learning
uv run -m src.split
```

## Pipeline de Données
Le projet suit un flux strict pour garantir la reproductibilité des modèles :

1. **Collecte (`src.collect`)** : Récupération des données brutes -> `data/raw/`.
2. **Consolidation (`src.consolidate`)** : Fusion et nettoyage -> `data/processed/consolidated_YYYY_MM_DD-au-MM_DD.parquet`.
3. **Split ML (`src.split`)** : Création des fichiers `train.parquet`, `val.parquet`, `test.parquet` -> `data/processed/`.
4. **Pipeline (`src.pipeline`)** : Orchestration des 3 étapes (collecte + consolidation + split).

### Features collectées :
* **Marine** : Hauteur/Direction/Période des vagues, Houle.
* **Météo** : Température, Vent (vitesse/rafales/direction).

## Modes Avancés (Docker & Makefile)
Si vous préférez ne pas utiliser `uv` en direct :
* **Make** : `make install`, `make collect`, `make consolidate`, `make split`.
* **Docker** : `docker compose run --rm collect-data`.

Le mode **Make** est idéal pour standardiser les commandes dans l'équipe, avec des alias simples à retenir.
Le mode **Docker** est recommandé si vous voulez un environnement reproductible, isolé de votre machine locale.
En pratique : utilisez `uv` pour itérer vite en local, puis `Docker`/`Make` pour fiabiliser l'exécution sur d'autres postes ou en CI.

## Configuration locale

Si le réseau de l'entreprise bloque l'accès direct à open_meteo, ajoutez vos variables
de proxy dans un fichier `.env` local à la racine du projet :

```env
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port
```

Si votre proxy d'entreprise est un proxy HTTP classique, gardez bien `http://` dans
les deux variables, y compris `HTTPS_PROXY`.

Si vous obtenez une erreur `407 Proxy Authentication Required`, le proxy attend des
identifiants. Dans ce cas, il faut utiliser une URL de proxy authentifiée ou passer
par la configuration réseau recommandée par l'entreprise.

Pour que le terminal intégré de VS Code lise ce fichier, activez le réglage
`python.terminal.useEnvFile` dans les paramètres Python de VS Code.
Si ce réglage est désactivé, les variables du `.env` ne sont pas injectées dans le terminal.

## Exemple d'utilisation : modes proxy

Une petite utilité permet de vérifier le comportement automatique / forcé / désactivé
du proxy. Pour exécuter l'exemple localement, définissez la variable d'environnement
suivante puis lancez `python main.py` depuis la racine du projet :

```bash
# Affiche les valeurs de `client.proxies` pour les trois modes
export METEO_EXAMPLE_PROXY=1   # sous PowerShell : $env:METEO_EXAMPLE_PROXY=1
python main.py
```

Interprétation des modes affichés :
- `force_proxy=None` : mode automatique — le client n'utilisera le proxy que s'il est joignable.
- `force_proxy=False`: proxy désactivé (même si `.env` contient des variables).
- `force_proxy=True` : forcer l'utilisation des variables de proxy même si elles semblent injoignables.

L'exemple est utile pour tester si vous êtes à la maison (connexion directe) ou
au bureau (proxy d'entreprise). En production, laissez `force_proxy=None` pour
la détection automatique, ou fournissez explicitement `force_proxy=True` si vous
savez que le proxy doit être utilisé.

## Performance

| Opération | Temps | Taille |
|-----------|-------|--------|
| Collecte 31 jours | ~2-3 min | ~5-10 KB |
| Consolidation annuelle | ~5-10 sec | ~150-200 KB |
| Chargement train.parquet | <50 ms | ~70-120 KB |

## Documentation Additionnelle
* [README_ML.md](documentation/README_ML.md) : Guide spécifique pour l'entraînement des modèles.
* [UTILS_EXPLIQUE.md](documentation/UTILS_EXPLIQUE.md) : Détails de l'architecture du code.
* [DOCKER.md](documentation/DOCKER.md) : Configuration des conteneurs.
* [DOCKER_EXPLIQUE.md](documentation/DOCKER_EXPLIQUE.md) : Explication détaillée de l'architecture Docker.

Note : un ancien script Météo-France a été archivé dans [archive/requete_meteo_france.py](archive/requete_meteo_france.py).

---

**Licence :** Ce projet est sous licence MIT.
**Auteur :** Bruno Coulet - *Projet réalisé en alternance IA*.