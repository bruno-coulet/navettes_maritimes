# Dockerfile historique pour la pipeline d'entraînement.
# Utilisé par `docker-compose.orchestration.yml` lors de la génération du modèle.
# Conservé comme référence et pour les ré-exécutions du pipeline, pas pour le VPS de production.
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers sources
COPY pyproject.toml pyproject.lock* ./
COPY src/ ./src/
COPY data/ ./data/

# Installer les dépendances Python
RUN pip install --no-cache-dir -e .

# Volume pour les artefacts du modèle
VOLUME /app/artifacts

# Par défaut : entraîner le modèle
CMD ["python", "src/train_annulation.py"]
