"""
Traitement des features V2 et fusion des registres maritimes et météo.

Responsabilité:
- Charger l'historique d'exploitation maritime brut (V1)
  sans les variables météo déclarative de l'exploitation.
- Agréger les données à la maille quotidienne (correction du biais statistique 'mean')
- Charger dynamiquement l'historique Open-Meteo consolidé (Parquet)
  maille quotidienne, perd la granularité fine, mais nettoie le bruit statistique
- Fusionner les deux univers sur la clé temporelle (Date)
- Générer la cible binaire finale basée sur le seuil métier de 16.6%

Entrées:
- v1_baseline/data/maritime_clean.csv
- v2_meteo/data/processed/consolidated_*.parquet (Détection dynamique)

Sorties:
- v2_meteo/data/processed/training_merged_meteo.parquet

Commande:
- `uv run python -m v2_meteo.src.features_v2`

Commande précédente (pour générer le fichier consolidé nécessaire):
- `uv run python -m v2_meteo.src.consolidate`

Commande suivante (pour entrainer le modele avec ce nouveau fichier):
- `uv run python -m v2_meteo.src.train_v2`

"""

import pandas as pd
from pathlib import Path

print("="*70)
print("CALCUL : Merge avec Annulation='mean' (distribution réelle)")
print("="*70)

# Charger données brutes Maritime, ROOT est 3 niveau au dessus de __file__
PROJECT_ROOT = Path(__file__).resolve().parents[2]
v2_meteo = Path(__file__).resolve().parents[1]
maritime_path = PROJECT_ROOT / "v1_baseline" / "data" / "maritime_clean.csv"

maritime_df = pd.read_csv(maritime_path)
maritime_df['Horaire'] = pd.to_datetime(maritime_df['Horaire'])
maritime_df['Date'] = maritime_df['Horaire'].dt.date

print("\nAgrégation quotidienne de Maritime avec mean()")

daily_mean = maritime_df.groupby('Date').agg({
    'Annulation': ['count', 'sum', 'mean'],
    'Ligne': 'first',
    'Vent': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
    'VentNoeud': 'max',
    'HouleDominante': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
    'HouleMax': 'max',
    'Houle': 'mean',
    'HoulePeriode': 'mean',
    'Mer': 'max',
    'Temperature': ['min', 'max'],
    'Ciel': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
}).reset_index()

daily_mean.columns = ['Date', 'N_Traversees', 'N_Annulations', 'AnnulationPct',
                      'Ligne', 'Vent', 'VentNoeud', 'HouleDominante', 'HouleMax',
                      'Houle', 'HoulePeriode', 'Mer', 'Temperature_min', 'Temperature_max', 'Ciel']

daily_mean['Date'] = pd.to_datetime(daily_mean['Date'])
daily_mean = daily_mean.sort_values('Date')

print(f"Total jours : {len(daily_mean)}")
print(f"% annulations (moyenne) : {daily_mean['AnnulationPct'].mean()*100:.1f}%")
print(f"Écart-type : {daily_mean['AnnulationPct'].std()*100:.1f}%")
print(f"Min/Max : {daily_mean['AnnulationPct'].min()*100:.1f}% - {daily_mean['AnnulationPct'].max()*100:.1f}%")

print("\nCharger open_meteo et merger")
# Charger dynamiquement le fichier open_meteo consolidé
# lister tous les fichiers qui commencent par consolidated_ et finissent par .parquet
consolidated_files = list((v2_meteo / "data" / "processed").glob("consolidated_*.parquet"))
if not consolidated_files:
    raise FileNotFoundError(
        f"Aucun fichier consolidé trouvé dans {v2_meteo / 'data' / 'processed'}. "
        "Exécutez d'abord le script consolidate.py."
    )
# Prend le 1er fichier (le seul le plus récent)
consolidated_file = consolidated_files[0]
print(f"Fichier consolidé trouvé : {consolidated_file.name}")

openmeteo_df = pd.read_parquet(consolidated_file)
openmeteo_df['date'] = pd.to_datetime(openmeteo_df['date'])

# Filter sur intersection
daily_mean_filtered = daily_mean[
    (daily_mean['Date'] >= '2024-01-01') & 
    (daily_mean['Date'] <= '2026-01-09')
].copy()

print(f"Maritime filtered 2024-2026 : {len(daily_mean_filtered)} jours")
print(f"  % annulations : {daily_mean_filtered['AnnulationPct'].mean()*100:.1f}%")

# Merger
daily_mean_filtered.rename(columns={'Date': 'date'}, inplace=True)
merged = pd.merge(
    daily_mean_filtered,
    openmeteo_df,
    on='date',
    how='inner'
)

print(f"Après merge : {len(merged)} jours")
print(f"  % annulations : {merged['AnnulationPct'].mean()*100:.1f}%")

# Convertir AnnulationPct en classe binaire (0/1) avec threshold 0.5 ou continuer en probabilité
print("\nOptions de conversion :")
print(f"  1. Garder comme probabilité (0.0 - 1.0) → pour regression/probabilistic model")
print(f"  2. Threshold 0.5 → 0 si < 50% annulations, 1 si >= 50%")
print(f"  3. Threshold 0.166 (même que v1) → 0 si < 16.6%, 1 si >= 16.6%")

# Option 3 : threshold = 16.6% (moyenne v1)
merged['Annulation_binary'] = (merged['AnnulationPct'] >= 0.166).astype(int)
print(f"\nAvec threshold 16.6% : {merged['Annulation_binary'].mean()*100:.1f}% annulations")

# Sauvegarder
v2_meteo = Path(__file__).resolve().parents[1]
output_path = v2_meteo / "data" / "processed" / "training_merged_meteo.parquet"

merged.to_parquet(output_path, index=False)
print(f"\n✓ Sauvegardé : {output_path}")



merged.to_parquet(output_path, index=False)
print(f"\n✓ Sauvegardé : {output_path}")
print(f"  Shape : {merged.shape}")
print(f"  Colonnes : {list(merged.columns)}")

print("\n" + "="*70)
print("RÉSUMÉ")
print("="*70)
print(f"""
Distribution d'annulation :
  v1 Maritime brut (79,285 horaires) : 16.6%
  v1 Maritime quotidien avec mean() : ~16.6% (cohérent)
  v2 open_meteo merged avec mean() : {merged['AnnulationPct'].mean()*100:.1f}%
  
Erreur précédente : 
  ❌ Utilisé Annulation='max' → surreprésente : 65.6%
  
Correction :
  ✅ Utiliser Annulation='mean' → distribution réelle : {merged['AnnulationPct'].mean()*100:.1f}%
  
Impact sur modèle :
  v2 aurait eu déséquilibre artificiel (65% vs 35%)
  Maintenant plus proche de v1 (17% vs 83%)
""")
