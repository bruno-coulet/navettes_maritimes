# Guide Docker - Météo Marine ML

## Installation de Docker

### macOS
```bash
brew install docker
# Puis lancer Docker Desktop depuis Applications
```

### Linux
```bash
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker $USER
```

### Windows
```powershell
winget install -e --id Docker.DockerDesktop
# Puis lancer Docker Desktop depuis le menu Démarrer
```

---

## Workflow Docker

### 1. Builder l'image

```bash
make docker-build
# ou manuellement:
docker build -t open-meteo:latest .
```

**Résultat:**
- Image: `open-meteo:latest` (~600MB avec dépendances ML)
- Multi-stage build pour optimiser la taille

### 2. Exécuter une collecte

```bash
# Avec docker run simple
docker run --rm -v $(PWD)/data:/app/data open-meteo:latest

# Ou avec Make
make docker-run
```

Sur Windows PowerShell:
```powershell
docker run --rm -v "${PWD}/data:/app/data" open-meteo:latest
```

Les données seront sauvegardées dans `./data/raw/` de votre machine.

### 3. Avec docker-compose (recommandé)

#### Collecter les données
```bash
docker compose run --rm collect-data
```

Modifiez les variables d'environnement dans `docker-compose.yml`:
```yaml
environment:
  START_DATE: "2025-12-01"
  END_DATE: "2025-12-31"
```

#### Consolider les données
```bash
docker compose run --rm consolidate-data
```

Génère le fichier consolidé dans `data/processed/`.

#### Créer les splits ML
```bash
docker compose run --rm split-data
```

Génère `train.parquet`, `val.parquet` et `test.parquet` dans `data/processed/`.

#### Lancer Jupyter pour l'exploration
```bash
docker compose run --rm jupyter
```

Puis ouvrez: `http://localhost:8888`

---

## Structure des volumes

```bash
# Les données sont persistées sur votre machine:
./data/
├── raw/              # Collectées dans le conteneur
├── processed/        # Consolidées dans le conteneur
└── ...
```

**Important:** Le dossier `./data` doit exister avant le premier lancement:
```bash
mkdir -p data/raw data/processed
```

Sur Windows PowerShell:
```powershell
New-Item -ItemType Directory -Force data/raw, data/processed
```

---

## Commandes utiles

```bash
# Voir les images
docker images | grep meteo

# Voir les conteneurs en cours
docker ps

# Voir les logs d'un conteneur
docker logs open-meteo-collect

# Arrêter un conteneur
docker stop open-meteo-collect

# Supprimer tout (images + conteneurs)
make docker-clean
```

---

## Troubleshooting

### Erreur: "Cannot connect to Docker daemon"
Assurez-vous que Docker est lancé:
```bash
# macOS
open /Applications/Docker.app

# Linux
sudo systemctl start docker
```

Sur Windows PowerShell:
```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### Erreur: "Permission denied"
```bash
# Ajouter votre user au groupe docker
sudo usermod -aG docker $USER
# Redémarrer ou:
newgrp docker
```

### Données non persistées
Vérifiez que le chemin du volume est correct:
```bash
docker run -v $(pwd)/data:/app/data open-meteo:latest
```

Sur Windows PowerShell:
```powershell
docker run -v "${PWD}/data:/app/data" open-meteo:latest
```

### Image trop grande
Nettoyez les images non utilisées:
```bash
docker system prune -a
```

---

## Performance

| Approche | Avantages | Inconvénients |
|----------|-----------|--------------|
| **Local (uv)** | Rapide, debug facile | Dépendances à installer |
| **Docker** | Reproductible, isolation | Overhead initial, taille image |
| **Docker Compose** | Orchestration, volumes | Plus complexe |

**Recommandation:**
- **Développement:** Local avec `uv`
- **Production/CI-CD:** Docker
- **Équipe:** Docker Compose

---

## CI/CD (Exemple GitHub Actions)

```yaml
name: Meteo Marine ML

on: [push]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: false
          tags: open-meteo:test
```

