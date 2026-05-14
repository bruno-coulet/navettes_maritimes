# Orchestration Docker : Collecte Météo → Entraînement Modèle → Prédiction

Ce document explique comment orchestrer les trois services (meteo_marine → maritime → navettes) via Docker Compose.

---

## Architecture

```
meteo_marine_collect
    ↓ (produit data/processed/*.parquet)
maritime_model
    ↓ (produit artifacts/model.pkl + features.json)
navettes_pred (API 8000)
```

**Services Docker** :
- `meteo_marine_collect` : Collecte les données météo brutes et les consolide
- `maritime_model` : Entraîne le modèle d'annulation sur les données historiques
- `navettes_pred` : Expose une API pour prédire les annulations

**Volumes partagés** :
- `meteo_data` : Données métro (raw + processed)
- `maritime_data` : Données historiques maritimes
- `maritime_artifacts` : Modèle et métadonnées
- `navettes_predictions` : Résultats de prédictions

---

## Usage

### Démarrer la pipeline complète

```bash
# Depuis le dossier parent `navettes_maritimes/`
cd ~/projets/navettes_maritimes/
docker-compose -f docker-compose.orchestration.yml up --build

# Ou avec détachement (background)
docker-compose -f docker-compose.orchestration.yml up -d --build
```

Cela exécute les 3 services dans l'ordre, en respectant les dépendances :
1. `meteo_marine_collect` → collecte météo
2. `maritime_model` (dépend de #1) → entraîne modèle
3. `navettes_pred` (dépend de #2) → démarre l'API

### Lancer un service spécifique

```bash
# Uniquement la collecte météo
docker-compose -f docker-compose.orchestration.yml run meteo_marine_collect

# Uniquement l'entraînement
docker-compose -f docker-compose.orchestration.yml run maritime_model

# Uniquement l'API de prédiction
docker-compose -f docker-compose.orchestration.yml run navettes_pred
```

### Accéder à l'API de prédiction

```bash
# Santé du service
curl http://localhost:8000/health

# Interface interactive (Swagger)
# http://localhost:8000/docs

# Prédire une annulation
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "wave_height_max": 2.5,
    "wave_direction_dominant": 45,
    "wind_speed_max": 15,
    "temperature_max": 20
  }'
```

### Arrêter les services

```bash
docker-compose -f docker-compose.orchestration.yml down

# Avec nettoyage des volumes
docker-compose -f docker-compose.orchestration.yml down -v
```

---

## Déploiement sur VPS

### 1. Préparation

```bash
# Cloner les 3 repos dans un dossier parent unique
git clone <meteo_marine> navettes_maritimes/meteo_marine
git clone <maritime> navettes_maritimes/maritime
git clone <navettes> navettes_maritimes/navettes

# Structure recommandée
~/projets/
  └─ navettes_maritimes/
      ├─ meteo_marine/
      ├─ maritime/
      ├─ navettes/
      └─ docker-compose.orchestration.yml
``` 

### 2. Configuration VPS

```bash
# Installer Docker
curl -sSL https://get.docker.com | sh

# (Optionnel) Installer Docker Compose standalone
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-linux-x86_64 \
  -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
```

docker-compose -f docker-compose.orchestration.yml up -d --build
### 3. Lancer la pipeline

```bash
cd ~/projets/navettes_maritimes/
docker-compose -f docker-compose.orchestration.yml up -d --build
```

### 4. Orchestration périodique (Cron)

Pour relancer la collecte/entraînement chaque nuit :

```bash
# Ajouter à crontab (crontab -e)
0 2 * * * cd ~/projets && docker-compose -f docker-compose.orchestration.yml run --rm meteo_marine_collect && docker-compose -f docker-compose.orchestration.yml run --rm maritime_model
```

Cela exécute la collecte et l'entraînement chaque jour à 2h du matin.

### 5. Monitoring

```bash
# Logs en temps réel
docker-compose -f docker-compose.orchestration.yml logs -f

# Logs d'un service spécifique
docker-compose -f docker-compose.orchestration.yml logs maritime_model

# Vérifie état des conteneurs
docker ps
docker-compose -f docker-compose.orchestration.yml ps
```

---

## Troubleshooting

### ❌ "model.pkl not found"

Vérifier que `maritime_model` a bien exécuté et généré les artefacts :
```bash
docker-compose -f docker-compose.orchestration.yml logs maritime_model
```

### ❌ "Cannot connect to /var/run/docker.sock"

Sur une machine locale sans Docker Desktop :
```bash
# Installer Docker via le script officiel
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### ❌ Port 8000 déjà utilisé

Changer le port dans `docker-compose.orchestration.yml` :
```yaml
navettes_pred:
  ports:
    - "8001:8000"  # Port local 8001
```

---

## Variables d'environnement

Dans `docker-compose.orchestration.yml`, tu peux surcharger les variables :

```bash
# Désactiver la détection auto du proxy
METEO_EXAMPLE_PROXY=0 docker-compose -f docker-compose.orchestration.yml up
```

---

## Fichiers de sortie

Après exécution complète :

```
meteo_data/
  ├─ raw/          # Données brutes mensuelles
  ├─ processed/    # Données consolidées

maritime_artifacts/
  ├─ model.pkl         # Modèle entraîné
  ├─ features.json     # Métadonnées et performances

navettes_predictions/
  └─ predictions_*.csv # Résultats de prédictions
```

---

## Prochaines améliorations

- [ ] Ajouter Prometheus + Grafana pour monitoring
- [ ] Ajouter versioning du modèle (MLflow)
- [ ] Scheduler externe (Airflow) pour workflows plus complexes
- [ ] Tests automatisés dans la pipeline (pytest)
- [ ] Notification Slack/email en cas d'erreur
