FROM python:3.10-slim

WORKDIR /app

# Installation des outils système nécessaires pour compiler certaines libs Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 1. Copier d'abord les fichiers de dépendances de la racine pour profiter du cache Docker
COPY pyproject.toml uv.lock* ./

# 2. Installer les dépendances globales (FastAPI, Streamlit, Scikit-learn, etc.)
# Si tu utilises "uv", on l'installe, sinon on utilise pip standard de manière robuste
RUN pip install --no-cache-dir uvicorn fastapi streamlit requests scikit-learn pandas numpy openpyxl

# 3. Copier l'intégralité du code du projet dans le conteneur
COPY . .

# Exposer les ports de l'API (8000) et du Front (8501)
EXPOSE 8000 8501