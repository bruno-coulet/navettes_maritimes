# navettes_maritimes

Dossier parent qui regroupe les 3 repos du projet :

- `open_meteo/` : collecte et préparation des données météo
- `maritime/` : entraînement du modèle d'annulation
- `navettes/` : API de prédiction
- `docker-compose.orchestration.yml` : orchestration complète collecte → entraînement → prédiction

## Structure recommandée

```text
~/projets/navettes_maritimes/
  ├─ open_meteo/
  ├── maritime/
  ├── navettes/
  ├── front_app/
  ├── Dockerfile.api
  ├── Dockerfile.front
  └── docker-compose.orchestration.yml
```

## Lancement

```bash
cd ~/projets/navettes_maritimes/
docker-compose -f docker-compose.orchestration.yml up --build
```

Services exposés :
- collecte : service interne `open_meteo_collect`
- entraînement : service interne `maritime_model`
- API : `http://localhost:8000`


# 🚢 Navettes Maritimes - Prédiction d'Annulation

## 📌 Description

Projet de **prédiction d'annulation de navettes maritimes** basé sur :

1. **Collecte de données météo** (`open_meteo/`)
2. **Entraînement d'un modèle de ML** (`maritime/`)
3. **Inférence et prédiction en temps réel** (`navettes/`)

---

## 🛠 Prérequis

- Docker >= 20.10
- Docker Compose >= 1.29
- 4 Go de RAM minimum (8 Go recommandé pour l'entraînement)

---

## 🚀 Déploiement

### 1. Cloner le dépôt

```bash
git clone git@github.com:bruno-coulet/navettes_maritimes.git
cd navettes_maritimes
```

### 2. Configurer l'environnement

#### Centralized configuration

Les variables d'environnement sont centralisées à la racine du projet dans un fichier `.env`.

**Créer le fichier `.env` en copiant l'exemple** :
```bash
cp .env.example .env
```

Editer `.env` avec vos valeurs (surtout les proxies et clés API) :

```ini
# Proxy (si nécessaire)
HTTP_PROXY=http://proxy.rtm.lan:3129
HTTPS_PROXY=http://proxy.rtm.lan:3129
ALL_PROXY=

# Météo-France API key (laisser vide en VCS)
METEO_FRANCE_API_KEY=

# Ports et chemins
NAVETTES_PRED_PORT=8000
METEO_DATA_PATH=./data/meteo
MODEL_PATH=./data/artifacts/model.pkl
FEATURES_PATH=./data/artifacts/features.json
```

**Note** : Le fichier `.env` n'est jamais commité (voir `.gitignore`). Seul `.env.example` est dans le dépôt.

### Service-specific examples

Chaque service possède également un fichier `.env.example` local :
- `maritime/.env.example` : variables relatives au traitement des données maritimes
- `navettes/.env.example` : variables relatives à l'API de prédiction
- `open_meteo/.env.example` : variables proxy pour la collecte météo
- `front_app/.env.example` : URL publique de l'API et port Streamlit

Un développeur peut créer des fichiers `.env` locaux pour chaque service s'il souhaite des surcharges spécifiques.

#### Déploiement VPS / Traefik

Pour un déploiement exposé par Traefik, utilisez plutôt les Dockerfiles racine :
- `Dockerfile.api` pour le backend FastAPI
- `Dockerfile.front` pour le frontend Streamlit

Les Dockerfiles historiques dans `open_meteo/` et `maritime/` restent utiles pour la pipeline de collecte et d'entraînement, mais ils ne sont pas nécessaires pour le front de production.

Le fichier `docker-compose.orchestration.yml` garde le rôle de pipeline interne collecte → entraînement → prédiction. Pour le VPS, il est préférable d'avoir un compose séparé, par exemple `docker-compose.vps.yml`, afin de ne pas mélanger les dépendances de build avec les labels Traefik et les routes publiques.

### 3. Lancer la pipeline complète

```bash
docker-compose -f docker-compose.orchestration.yml up --build
```

### 4. Accéder à l'API de prédiction

- URL : `http://localhost:8000`
- Endpoint de test : `GET /health` (vérifie que le service est en ligne)
- Endpoint de prédiction : `POST /predict` (à documenter selon ton API)

---

## 📂 Structure du Projet

```
navettes_maritimes/
├── .env                # Configuration centralisée (À CRÉER depuis .env.example)
├── .env.example        # Template de configuration
├── open_meteo/
│   ├── .env.example    # Exemple de variables locales (optionnel)
│   ├── src/
│   ├── data/
│   └── README.md       # Service de collecte des données météo
├── maritime/
│   ├── .env.example    # Exemple de variables locales (optionnel)
│   ├── notebooks/      # Notebooks d'exploration et entraînement
│   ├── src/            # Modules d'entraînement et de prétraitement
│   ├── data/
│   └── README.md       # Service d'entraînement du modèle
├── navettes/
│   ├── .env.example    # Exemple de variables locales (optionnel)
│   ├── src/            # API FastAPI de prédiction
│   └── README.md       # Service d'inférence en temps réel
├── docker-compose.orchestration.yml  # Orchestration Docker
└── README.md           # Ce fichier (instructions principales)
```

---

## 🔧 Développement

### Organisation générale

- **Données** : Les données brutes et traitées sont stockées dans `./data/`.
- **Modèle** : Le modèle entraîné est sauvegardé dans `./data/artifacts/model.pkl` avec ses métadonnées en `features.json`.
- **Logs** : Les logs des services sont accessibles via `docker logs <container_name>`.

### Travailler localement (sans Docker)

Chaque service peut être développé indépendamment :

1. **open_meteo** : récupère les données météo (voir `open_meteo/README.md`)
2. **maritime** : entraîne et exporte le modèle (voir `maritime/README.md`)
3. **navettes** : expose une API de prédiction (voir `navettes/README.md`)

### Configuration locales des services

Si vous souhaitez une configuration locale différente pour un service, créez un `.env` dans le dossier du service en copiant le `.env.example` correspondant. Les variables d'environnement du service seront chargées à partir de ce fichier `.env` local.

---

## 📊 Exemple d'Utilisation

1. **Collecte** : Les données météo sont automatiquement récupérées et stockées.
2. **Entraînement** : Le modèle est entraîné sur les données historiques.
3. **Prédiction** : Envoyer une requête POST à `/predict` avec les données d'entrée pour obtenir une prédiction.

---

## 🤝 Contact

Bruno Coulet - [bruno.coulet@laplateforme.io](mailto:bruno.coulet@laplateforme.io)  
[GitHub](https://github.com/bruno-coulet)
