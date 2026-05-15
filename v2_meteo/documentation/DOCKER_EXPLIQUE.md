# Docker - Guide Complet

## Architecture Docker

### Fichiers Docker

```
Dockerfile             # Image de base (Python 3.11)
docker-compose.yml     # Orchestration multi-services
.dockerignore          # Fichiers à exclure
```

### Image Docker

**Approche multi-stage** (optimisée):
1. **Builder stage**: Construit l'environnement virtuel
2. **Runtime stage**: Image finale (plus légère)

**Résultat**: ~600 MB au lieu de 1+ GB

## 📦 Dockerfile expliqué

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
RUN pip install uv
WORKDIR /app
COPY pyproject.toml .
RUN uv venv && uv pip install -e .

# Stage 2: Runtime (final)
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv  # Copier l'env du builder
COPY . .
RUN mkdir -p data/raw data/processed
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "src.pipeline"]
```

### Points clés:

1. **Base légère**: `python:3.11-slim` (~150 MB vs 900 MB)
2. **uv dans builder**: Installe dépendances rapidement
3. **Multi-stage**: Élimine `uv` et dépendances de build du final
4. **Volume data/**: Persistance entre conteneurs
5. **ENTRYPOINT/CMD**: Lance `src.pipeline` par défaut

## 🚀 Commandes Docker

### Build

```bash
# Build l'image
docker build -t open_meteo:latest .

# Avec tag versionnée
docker build -t open_meteo:v1.0.0 .

# Afficher les images
docker images | grep meteo
```

### Run simple

```bash
# Exécution basique (données éphémères)
docker run open_meteo:latest

# Avec volume (données persistées)
docker run --rm \
  -v $(pwd)/data:/app/data \
  open_meteo:latest

# Avec variables d'environnement
docker run --rm \
  -v $(pwd)/data:/app/data \
  -e START_DATE="2025-01-01" \
  -e END_DATE="2025-01-31" \
  open_meteo:latest
```

## 🐳 Docker Compose

### Structure

```yaml
services:
  collect-data:
    # Exécute collect.py
    # Profil: docker compose run --rm collect-data
    
  consolidate-data:
    # Exécute consolidate.py
    # Profil: docker compose run --rm consolidate-data

  split-data:
    # Exécute split.py
    # Profil: docker compose run --rm split-data
    
  jupyter:
    # Serveur Jupyter (port 8888)
    # Profil: docker compose run --rm jupyter
```

### Utilisation

```bash
# Voir les services disponibles
docker compose ps

# Collecter les données
docker compose run --rm collect-data

# Consolider les données
docker compose run --rm consolidate-data

# Créer les splits ML
docker compose run --rm split-data

# Lancer Jupyter
docker compose run --rm jupyter
# → http://localhost:8888

# Arrêter tous les services
docker compose down

# Nettoyer (volumes aussi)
docker compose down -v
```

### Volumes

```yaml
volumes:
  - ./data:/app/data        # Données persistées sur l'hôte
  - ./notebooks:/app/notebooks  # Notebooks Jupyter
```

Les données restent accessible après arrêt du conteneur.

## 🔄 Workflow Docker complet

### 1. Build initial

```bash
docker build -t open_meteo:latest .
```

**Durée**: ~5-10 min (première fois)
**Taille**: ~600 MB (téléchargé une seule fois)

### 2. Collecte données

```bash
docker compose run --rm collect-data
```

**Données générées**: `data/raw/2025_11/meteo_*.csv`

### 3. Consolidation

```bash
docker compose run --rm consolidate-data
```

**Fichier généré**:
- `data/processed/consolidated_YYYY_MM_DD-au-MM_DD.parquet`

### 4. Split ML

```bash
docker compose run --rm split-data
```

**Fichiers générés**:
- `data/processed/train.parquet`
- `data/processed/val.parquet`
- `data/processed/test.parquet`

### 5. ML (local ou Docker)

```bash
# Local
jupyter lab

# Ou Docker + Jupyter
docker compose run --rm jupyter
```

## 📊 Performance Docker

| Opération | Temps | Cache |
|-----------|-------|-------|
| Build (1ère fois) | 5-10 min | ✗ |
| Build (avec cache) | <5 sec | ✓ |
| Run collect | 2-3 min | - |
| Run consolidate | 5-10 sec | - |
| Run split | <5 sec | - |
| Run jupyter | <1 sec | - |

## 🐛 Troubleshooting Docker

### Erreur: "Cannot connect to Docker daemon"

```bash
# macOS: Lancer Docker Desktop
open /Applications/Docker.app

# Linux: Démarrer daemon
sudo systemctl start docker
```

### Erreur: "Permission denied while trying to connect"

```bash
# Ajouter user au groupe docker
sudo usermod -aG docker $USER
newgrp docker  # Ou redémarrer
```

### Données non persistées

```bash
# Vérifier le chemin du volume
docker inspect open_meteo-collect | grep Mounts

# Vérifier les permissions
ls -la ./data/
```

### Image trop grande

```bash
# Nettoyer images inutilisées
docker system prune -a

# Vérifier la taille
docker image ls --format "table {{.Repository}}\t{{.Size}}"
```

### Logs du conteneur

```bash
# Afficher les logs
docker logs open_meteo-collect

# Suivre en direct
docker logs -f open_meteo-collect

# Dernier 100 lignes
docker logs --tail 100 open_meteo-collect
```

## 🔐 Bonnes pratiques

### 1. `.dockerignore`

```ignore
__pycache__/
.git/
.venv/
data/raw/*
*.log
.env
```

Réduit la taille du build context.

### 2. Volumes nombmés vs montés

```bash
# Volume monté (recommandé localement)
-v $(pwd)/data:/app/data

# Volume nommé (recommandé production)
-v meteo-data:/app/data
```

### 3. Environment variables

```bash
# .env local (pas committé)
START_DATE=2025-01-01
END_DATE=2025-12-31

# Utiliser dans docker-compose
docker compose --env-file .env up
```

### 4. Health checks

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import pandas"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## 🚢 Déploiement en production

### Docker Hub

```bash
# Tag pour Docker Hub
docker tag open_meteo:latest username/open_meteo:latest

# Push
docker push username/open_meteo:latest

# Pull depuis autre machine
docker pull username/open_meteo:latest
docker run username/open_meteo:latest
```

### AWS/GCP/Azure

```bash
# Exemple AWS ECR
aws ecr get-login-password | docker login --username AWS --password-stdin 123456.dkr.ecr.us-east-1.amazonaws.com
docker tag open_meteo:latest 123456.dkr.ecr.us-east-1.amazonaws.com/open_meteo:latest
docker push 123456.dkr.ecr.us-east-1.amazonaws.com/open_meteo:latest
```

### CI/CD (GitHub Actions)

```yaml
name: Docker Build & Push
on: [push]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: username/open_meteo:${{ github.sha }}
```

## 📚 Ressources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 💡 Tips

### Exécuter une commande dans conteneur en cours

```bash
docker exec -it open_meteo-collect bash
python -c "import pandas; print(pandas.__version__)"
```

### Sauvegarder/Charger image

```bash
# Export
docker save open_meteo:latest > open_meteo.tar

# Import
docker load < open_meteo.tar
```

### Nettoyer complètement

```bash
# Tout: conteneurs, images, volumes inutilisés
docker system prune -a --volumes
```

## 🎯 Cas d'usage

### Développement local
```bash
uv sync && uv run -m src.pipeline  # Rapide, debug facile
```

### Tests
```bash
docker build -t open_meteo:test .
docker run open_meteo:test
```

### Production
```bash
docker compose -f docker-compose.prod.yml up -d
```

### CI/CD
```bash
# GitHub Actions/GitLab CI
docker build -t open_meteo:ci .
docker run open_meteo:ci pytest
```
