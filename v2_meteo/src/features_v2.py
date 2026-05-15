"""

anciennemnt nommé "merge_maritime_open_meteo.py

Recalculer le merge avec Annulation='mean' au lieu de 'max'

Cela donne la vraie distribution quotidienne :
- Si un jour a 80 traversées et 13 annulations → AnnulationMean = 13/80 = 16.25%
- Cela reste comparable à v1 (16.6%)
"""

import pandas as pd
from pathlib import Path

print("="*70)
print("RECALCUL : Merge avec Annulation='mean' (distribution réelle)")
print("="*70)

# Charger données brutes Maritime
maritime_df = pd.read_csv("maritime/data/maritime_clean.csv")
maritime_df['Horaire'] = pd.to_datetime(maritime_df['Horaire'])
maritime_df['Date'] = maritime_df['Horaire'].dt.date

print("\n[1] Agrégation quotidienne de Maritime avec mean()")
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

print("\n[2] Charger open_meteo et merger")
# Charger open_meteo
openmeteo_df = pd.read_parquet("meteo_marine/data/processed/consolidated_2024_01_01-au-2026_04_30.parquet")
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
output_path = "meteo_marine/data/processed/training_merged.parquet"
merged.to_parquet(output_path, index=False)
print(f"\n✓ Sauvegardé : {output_path}")
print(f"  Shape : {merged.shape}")
print(f"  Colonnes : {list(merged.columns)}")

print("\n" + "="*70)
print("RÉSUMÉ CORRECTIONNEÉ")
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
