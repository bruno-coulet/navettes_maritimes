# Image utilisée par ../docker-compose.orchestration.yml
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
