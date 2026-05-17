"""Point d'entree historique du projet `meteo_marine`.

Responsabilite:
- lancer le pipeline principal ou un petit exemple de verification des proxies
- conserver la compatibilite avec les anciens lancements `python main.py`

Entrees:
- variable d'environnement `METEO_EXAMPLE_PROXY`
- configuration du pipeline dans `src.pipeline`

Sorties:
- execution du pipeline Meteo Marine ou affichage du comportement proxy

Commande:
- `python main.py`
- ou `METEO_EXAMPLE_PROXY=1 python main.py` pour l'exemple
"""

from v2_meteo.src.pipeline import main as pipeline_main
import os


def run_proxy_example() -> None:
    """Exemple minimal pour montrer `force_proxy` et la résolution automatique."""
    from src.utils import MeteoMarineMarseille

    print("Exemple: instanciation MeteoMarineMarseille avec différents modes proxy")
    for mode in (None, False, True):
        client = MeteoMarineMarseille(timeout=10, force_proxy=mode)
        print(f"force_proxy={mode!r} -> proxies: {client.proxies}")


if __name__ == "__main__":
    if os.getenv("METEO_EXAMPLE_PROXY"):
        run_proxy_example()
    else:
        pipeline_main()