FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de configuration de dépendances
COPY predict/pyproject.toml* predict/requirements.txt* ./

# Installation des dépendances (s'adapte si tu as un requirements ou pyproject)
RUN pip install --no-cache-dir uvicorn fastapi streamlit requests scikit-learn pandas numpy

# Copie de tout le code de l'application dans le conteneur
COPY . .

EXPOSE 8000 8501