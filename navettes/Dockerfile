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
COPY main.py .

# Installer les dépendances Python
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir fastapi uvicorn

# Volume pour les données d'entrée et modèle
VOLUME /input_data /model /app/predictions

# Par défaut : démarrer le serveur de prédiction
EXPOSE 8000
CMD ["uvicorn", "src.predict_annulation:app", "--host", "0.0.0.0", "--port", "8000"]
