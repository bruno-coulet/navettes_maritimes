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
