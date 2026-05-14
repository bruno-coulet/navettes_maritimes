"""
Analyse : Pourquoi distribution d'annulation différente entre v1 et v2 ?

v1 Maritime :
- 79,285 horaires sur 2023-2026
- 16.6% annulations

v2 Open-Meteo merged :
- 719 jours sur 2024-2026 (intersection)
- 65.6% annulations

Question : C'est la même source d'annulation. Pourquoi l'écart ?

Hypothèse : L'agrégation quotidienne avec 'max' exagère les annulations.
Si une journée a au moins 1 annulation (sur ~10-20 traversées), 
le jour entier = 1 (annulation). C'est un biais d'agrégation.
"""

import pandas as pd
from pathlib import Path

print("="*70)
print("ANALYSE : Distribution d'annulation v1 vs v2")
print("="*70)

# Charger données brutes Maritime
maritime_df = pd.read_csv("maritime/data/maritime_clean.csv")
maritime_df['Horaire'] = pd.to_datetime(maritime_df['Horaire'])
maritime_df['Date'] = maritime_df['Horaire'].dt.date

print("\n[1] v1 Maritime - Distribution brute (horaires)")
print(f"Total horaires : {len(maritime_df)}")
print(f"Annulations : {maritime_df['Annulation'].sum()}")
print(f"% annulations : {maritime_df['Annulation'].mean()*100:.1f}%")

# Voir la distribution par période
maritime_df['YearMonth'] = maritime_df['Horaire'].dt.to_period('M')
print(f"\nDistribution par mois :")
monthly = maritime_df.groupby('YearMonth').agg({
    'Annulation': ['count', 'sum', 'mean']
}).round(3)
monthly.columns = ['Total', 'Annulations', 'Pct']
print(monthly)

print("\n" + "-"*70)
print("\n[2] v1 Maritime - Aggregation quotidienne (comme dans v2)")

# Agregger avec 'max' (ce que j'ai fait dans merge)
daily_max = maritime_df.groupby('Date').agg({
    'Annulation': ['count', 'sum', 'max', 'mean']
}).reset_index()
daily_max.columns = ['Date', 'NTraversees', 'NbAnnulations', 'AnnulationMax', 'PctAnnulations']

print(f"\nTotal jours : {len(daily_max)}")
print(f"Jours avec au moins 1 annulation (max=1) : {(daily_max['AnnulationMax']==1).sum()}")
print(f"% jours avec annulation : {(daily_max['AnnulationMax']==1).mean()*100:.1f}%")
print(f"\nMoyenne traversées/jour : {daily_max['NTraversees'].mean():.1f}")
print(f"Min/Max traversées : {daily_max['NTraversees'].min()} - {daily_max['NTraversees'].max()}")

print("\n" + "-"*70)
print("\n[3] v2 Open-Meteo merged (2024-2026 seulement)")

# Charger merged
merged_df = pd.read_parquet("meteo_marine/data/processed/consolidated_2024_01_01-au-2026_04_30.parquet")

# Filter sur intersection
merged_df['date'] = pd.to_datetime(merged_df['date'])
merged_filtered = merged_df[
    (merged_df['date'] >= '2024-01-01') & 
    (merged_df['date'] <= '2026-01-09')
].copy()

print(f"Total jours : {len(merged_filtered)}")
print(f"Jours avec annulation : {(merged_filtered['Annulation']==1).sum()}")
print(f"% jours avec annulation : {(merged_filtered['Annulation']==1).mean()*100:.1f}%")

print("\n" + "-"*70)
print("\n[4] Comparaison périodes")

# Comparer v1 sur même période que v2
maritime_2024_2026 = maritime_df[
    (maritime_df['Horaire'] >= '2024-01-01') & 
    (maritime_df['Horaire'] <= '2026-01-09')
].copy()

daily_2024_2026 = maritime_2024_2026.groupby('Date').agg({
    'Annulation': ['count', 'sum', 'max']
}).reset_index()

print(f"\nv1 Maritime sur 2024-2026 seulement :")
print(f"  - Horaires : {len(maritime_2024_2026)}")
print(f"  - % annulations brutes : {maritime_2024_2026['Annulation'].mean()*100:.1f}%")
print(f"  - Jours avec >= 1 annulation : {(daily_2024_2026[('Annulation', 'max')]==1).sum()} / {len(daily_2024_2026)}")
print(f"  - % jours avec annulation : {(daily_2024_2026[('Annulation', 'max')]==1).mean()*100:.1f}%")

print(f"\nv2 Open-Meteo 2024-2026 :")
print(f"  - Jours : {len(merged_filtered)}")
print(f"  - % annulations : {merged_filtered['Annulation'].mean()*100:.1f}%")

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("""
L'écart 16.6% → 65.6% vient de :

1. AGRÉGATION QUOTIDIENNE AVEC 'MAX'
   Si une journée a 10 traversées et 1 seule annulation,
   j'enregistre AnnulationMax=1 (tout le jour est annulé)
   vs brut = 1/10 = 10% annulation ce jour
   
   → Cela exagère les annulations

2. PÉRIODE ANALYSÉE
   Maritime 2023-2026 : 16.6% annulations
   Maritime 2024-2026 seulement : probablement ~30-40% (à vérifier)
   Open-Meteo 2024-2026 : 65.6% (agrégation max)
   
   → Les données récentes (2024-2026) ont plus d'annulations

3. MÉTHODE CORRECTE POUR V2
   Au lieu d'utiliser max(), devrait utiliser :
   - mean() : % traversées annulées ce jour
   - sum()/count() : idem
   - Cela donne une distribution plus proche de v1
""")
