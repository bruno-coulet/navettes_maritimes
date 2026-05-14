"""Point d'entree du service navettes.

Responsabilite:
- lancer l'API de prediction d'annulation exposee par `src.predict_annulation`
- garder un point d'entree simple a executer depuis le dossier `navettes/`

Entrees:
- modele et metadata exportes dans `artifacts/`

Sorties:
- service FastAPI demarre via Uvicorn

Commande:
- `python main.py`
- ou `uvicorn src.predict_annulation:app --host 0.0.0.0 --port 8000`
"""

from uvicorn import run


if __name__ == "__main__":
    run("src.predict_annulation:app", host="0.0.0.0", port=8000, reload=False)
