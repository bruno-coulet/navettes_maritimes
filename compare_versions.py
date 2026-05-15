import json
from pathlib import Path

#!/usr/bin/env python
"""
REPORTING : Outil de Comparaison de Performance (V1, V2, V3)
----------------------------------------------------------
LOGIQUE :
Ce script centralise les résultats des trois phases du projet :
1. V1 (Baseline) : Modèle historique basé sur les données Excel (maritime/).
2. V2 (Météo)   : Modèle basé uniquement sur l'API Open-Meteo (open_meteo/).
3. V3 (Hybride) : Modèle final combinant météo + facteurs métiers (capitaines/bateaux).

UNIFORMISATION :
Le script utilise une lecture "plate" des fichiers JSON. Chaque script d'entraînement
(train_v1, train_v2, train_v3) doit générer un fichier 'metrics_vX.json' à la racine
de son dossier artifacts respectif avec les clés : accuracy, precision, recall, f1, n_features.

SORTIE :
- Un tableau comparatif détaillé dans le terminal.
- Mise à jour du fichier 'REPORT_FINAL.md' pour archivage et présentation.
"""

def load_json(path):
    """Charge un JSON proprement avec gestion d'erreurs."""
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def main():
    print("="*95)
    print("RAPPORT DE PERFORMANCE GLOBAL : V1 (Baseline) vs V2 (Météo) vs V3 (Hybride)")
    print("="*95)

    # Chemins vers tes nouveaux artifacts uniformisés
    paths = {
        "V1 (Maritime Pur)": Path("v1_baseline/artifacts/metrics_v1.json"),
        "V2 (Météo Seule)": Path("v2_meteo/artifacts/metrics_v2.json"),
        "V3 (Hybride)": Path("v3_hybride/artifacts/metrics_v3.json")
    }

    results = {}
    for name, path in paths.items():
        data = load_json(path)
        if data:
            # Comme tout est uniformisé, on charge le dictionnaire directement
            results[name] = data

    if not results:
        print("\n❌ Aucun artifact trouvé. Vérifie que les fichiers metrics_vX.json existent.")
        return

    # 1. AFFICHAGE DANS LE TERMINAL
    metrics_to_show = ["accuracy", "precision", "recall", "f1"]
    
    header = f"\n{'Métrique':<15}"
    for name in results.keys():
        header += f" | {name:<20}"
    print(header)
    print("-" * 95)

    for m in metrics_to_show:
        row = f"{m:<15}"
        for name in results.keys():
            val = results[name].get(m, 0)
            row += f" | {val:<20.4f}"
        print(row)

    print("-" * 95)
    
    # Ligne des Features (Indicateur crucial de complexité)
    row_feat = f"{'n_features':<15}"
    for name in results.keys():
        n_feat = results[name].get('n_features', 'N/A')
        row_feat += f" | {str(n_feat):<20}"
    print(row_feat)
    
    print("=" * 95)

    # 2. GÉNÉRATION AUTOMATIQUE DU RAPPORT MARKDOWN
    report_path = Path("REPORT_FINAL.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ⚓ Rapport de Performance Final - Navettes Maritimes\n\n")
        f.write("Ce rapport compare les itérations successives du modèle de prédiction.\n\n")
        
        f.write("| Métrique | " + " | ".join(results.keys()) + " |\n")
        f.write("| :--- | " + " :---: |" * len(results) + "\n")
        for m in metrics_to_show:
            row = f"| **{m}**"
            for name in results.keys():
                val = results[name].get(m, 0)
                row += f" | {val:.4f}"
            f.write(row + " |\n")
        
        f.write(f"| **Features** | " + " | ".join([str(results[n].get('n_features', 'N/A')) for n in results.keys()]) + " |\n\n")
        
        f.write("## 💡 Analyse\n")
        f.write("- **V1** : Modèle historique, solide mais manque de sensibilité sur les annulations.\n")
        f.write("- **V2** : Preuve que la météo Open-Meteo est un puissant moteur de prédiction.\n")
        f.write("- **V3** : Meilleur compromis. L'ajout des données métiers (bateaux/capitaines) stabilise la précision.\n")

    print(f"\nRapport final généré avec succès : {report_path}")

if __name__ == "__main__":
    main()