"""Collecte historique des donnees meteo marine quotidienne de Marseille.

Responsabilite:
- interroger les APIs open-meteo (Marine et Archive ERA5)
- normaliser et fusionner les donnees sur une maille quotidienne
- sauvegarder les donnees brutes mensuelles pour le modele ML

Entrees:
- constantes START_DATE / END_DATE    définies dans le script
- API open-meteo Marine (hauteur/direction des vagues, houle)
- API open-meteo Archive (temperatures, vent, rafales)

Sorties:
- fichiers CSV mensuels bruts dans `v2_meteo/data/raw/`


Chronologie d'exécution complète du Pipeline V2 :
1. Collecte       : `uv run python -m v2_meteo.src.a_collect_meteo`
2. Consolidation  : `uv run python -m v2_meteo.src.b_consolidate`
3. Features Merge : `uv run python -m v2_meteo.src.c_features_v2`
4. Entraînement   : `uv run python -m v2_meteo.src.d_train_v2`
5. Comparaison    : `uv run python compare_versions.py`
"""

from datetime import datetime, timedelta

try:
    # Cas package: python -m open_meteo.src.collect
    from .utils import MeteoMarineMarseille
except ImportError:
    try:
        # Cas dossier open_meteo comme racine: python -m src.collect
        from src.utils import MeteoMarineMarseille
    except ImportError:
        # Cas exécution directe du fichier: python open_meteo/src/collect.py
        from utils import MeteoMarineMarseille

# ============================================================================
# CONFIGURATION - Modifier ces constantes pour personnaliser les requêtes
# ============================================================================
# Format: "YYYY-MM-DD" ou None pour utiliser les valeurs par défaut
START_DATE = "2024-01-01"
END_DATE = "2026-04-30" 



# Format de sauvegarde des données
# CSV (recommandé pour ML):
#   + Léger (~5-10 KB pour 31 jours)
#   + Rapide à charger (~1-2 ms)
#   + Compatible pandas/sklearn
#   - Moins flexible pour structures complexes
#
# JSON (utile pour archivage/APIs):
#   + Flexibilité (structures imbriquées possibles)
#   + Standard universel
#   - Lourd (~15-25 KB, +150% vs CSV)
#   - Lent à charger (~5-10 ms, +5x vs CSV)
SAVE_JSON = False  # True = sauvegarde aussi .json; False = que .csv (recommandé)
# ============================================================================


def test_api_connection(timeout=15):
    """Teste rapidement la connectivité aux APIs open_meteo utilisées par le pipeline."""
    print("=== TEST CONNECTIVITÉ API open_meteo ===")

    # Une petite fenêtre temporelle suffit pour valider la connectivité.
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=1)

    client = MeteoMarineMarseille(timeout=timeout)
    print(f"Proxy actif: {client.proxies if client.proxies else 'aucun'}")
    print(
        f"Test sur la période: {start_date.strftime('%Y-%m-%d')} à {end_date.strftime('%Y-%m-%d')}"
    )

    marine_data = client.get_marine_weather_open_meteo(start_date, end_date)
    weather_data = client.get_weather_data_open_meteo(start_date, end_date)

    marine_ok = marine_data is not None
    weather_ok = weather_data is not None

    print(f"API marine: {'OK' if marine_ok else 'KO'}")
    print(f"API weather: {'OK' if weather_ok else 'KO'}")

    if marine_ok or weather_ok:
        print("Connectivité API partielle ou complète: OK")
        return True

    print("Connectivité API: KO (aucune des deux APIs n'est joignable)")
    return False


def main():
    """Point d'entrée principal"""

    # Parsing des dates de configuration
    if END_DATE is None:
        end_date = datetime.now()
    else:
        try:
            end_date = datetime.strptime(END_DATE, "%Y-%m-%d")
        except ValueError:
            print(f"Erreur: END_DATE '{END_DATE}' doit être au format YYYY-MM-DD")
            return

    if START_DATE is None:
        start_date = end_date - timedelta(days=730)
    else:
        try:
            start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
        except ValueError:
            print(f"Erreur: START_DATE '{START_DATE}' doit être au format YYYY-MM-DD")
            return

    # Vérification que start_date < end_date
    if start_date >= end_date:
        print(
            f"Erreur: START_DATE ({start_date.date()}) doit être avant END_DATE ({end_date.date()})"
        )
        return

    print("=== COLLECTE DES DONNÉES MÉTÉO MARINE MARSEILLE ===")
    print(f"Période: {start_date.strftime('%Y-%m-%d')} à {end_date.strftime('%Y-%m-%d')}")
    print(f"Durée: {(end_date - start_date).days} jours")

    # Initialisation du client
    meteomarine = MeteoMarineMarseille()

    try:
        # Collecte des données par lots (utilise open_meteo principalement)
        print("\n1. Collecte des données via open_meteo...")
        batch_data = meteomarine.collect_historical_data_batch(start_date, end_date)

        # Traitement en résumé quotidien
        print("\n2. Traitement des données quotidiennes...")
        daily_df = meteomarine.process_to_daily_summary(batch_data)

        if not daily_df.empty:
            # Sauvegarde du résumé quotidien dans structure organisée par mois
            csv_files, json_files = meteomarine.save_data(
                daily_df, start_date, end_date, save_json=SAVE_JSON
            )

            print(f"\n=== RÉSULTATS ===")
            print(f"Nombre de jours collectés: {len(daily_df)}")
            print(f"Période effective: {daily_df['date'].min()} à {daily_df['date'].max()}")
            print(f"\nFichiers sauvegardés:")
            for csv_file in csv_files:
                print(f"- {csv_file}")

            # Affichage d'un échantillon
            print(f"\n=== ÉCHANTILLON DES DONNÉES ===")
            print(daily_df.head(10).to_string())

            # Statistiques
            print(f"\n=== STATISTIQUES ===")
            numeric_cols = daily_df.select_dtypes(include=["float64", "int64"]).columns
            if len(numeric_cols) > 0:
                print(daily_df[numeric_cols].describe())

        else:
            print("Aucune donnée quotidienne n'a pu être extraite.")

    except Exception as e:
        print(f"Erreur lors de la collecte : {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":

    main()

    # Décommentez ces lignes pour tester la connectivité API avant la collecte complète.
    # if not test_api_connection():
    #     raise SystemExit(1)