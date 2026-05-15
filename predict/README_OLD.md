# Navettes - API de prédiction

API FastAPI pour prédire les annulations de navettes maritimes à partir du modèle entraîné par `maritime/`.

## Arborescence

- `src/predict_annulation.py` : service FastAPI
- `Dockerfile` : image de l'API
- `pyproject.toml` : dépendances Python du service

## Lancement local

Depuis `~/projets/navettes_maritimes/navettes/` :

```bash
uv sync
uv run uvicorn src.predict_annulation:app --host 0.0.0.0 --port 8000
```

## Lancement Docker

Depuis `~/projets/navettes_maritimes/` :

```bash
docker-compose -f docker-compose.orchestration.yml up navettes_pred
```

L'interface Swagger est disponible sur `http://localhost:8000/docs`.
