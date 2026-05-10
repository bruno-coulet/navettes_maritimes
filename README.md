# navettes_maritimes

Dossier parent qui regroupe les 3 repos du projet :

- `meteo_marine/` : collecte et préparation des données météo
- `maritime/` : entraînement du modèle d'annulation
- `navettes/` : API de prédiction
- `docker-compose.orchestration.yml` : orchestration complète collecte → entraînement → prédiction

## Structure recommandée

```text
~/projets/navettes_maritimes/
  ├─ meteo_marine/
  ├─ maritime/
  ├─ navettes/
  └─ docker-compose.orchestration.yml
```

## Lancement

```bash
cd ~/projets/navettes_maritimes/
docker-compose -f docker-compose.orchestration.yml up --build
```

Services exposés :
- collecte : service interne `meteo_marine_collect`
- entraînement : service interne `maritime_model`
- API : `http://localhost:8000`


# 🚢 Navettes Maritimes - Prédiction d'Annulation

## 📌 Description

Projet de **prédiction d'annulation de navettes maritimes** basé sur :

1. **Collecte de données météo** (`meteo_marine/`)
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

Créer un fichier `.env` à la racine avec les variables suivantes (exemple dans `.env.example`) :

```ini
NAVETTES_PRED_PORT=8000
METEO_DATA_PATH=./data/meteo
MODEL_PATH=./data/artifacts/model.pkl
FEATURES_PATH=./data/artifacts/features.json
```

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
├── meteo_marine/       # Collecte des données météo (API Météo France, etc.)
├── maritime/           # Entraînement du modèle (nettoyage, features, training)
├── navettes/           # Inférence (API FastAPI/Flask pour les prédictions)
├── docker-compose.orchestration.yml  # Orchestration Docker
└── README.md           # Ce fichier
```

---

## 🔧 Développement

- **Données** : Les données brutes et traitées sont stockées dans `./data/`.
- **Modèle** : Le modèle entraîné est sauvegardé dans `./data/artifacts/`.
- **Logs** : Les logs des services sont accessibles via `docker logs <container_name>`.

---

## 📊 Exemple d'Utilisation

1. **Collecte** : Les données météo sont automatiquement récupérées et stockées.
2. **Entraînement** : Le modèle est entraîné sur les données historiques.
3. **Prédiction** : Envoyer une requête POST à `/predict` avec les données d'entrée pour obtenir une prédiction.

---

## 🤝 Contact

Bruno Coulet - [bcoulet@rtm.fr](mailto:bcoulet@rtm.fr)  
[GitHub](https://github.com/bruno-coulet)
