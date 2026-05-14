import pandas as pd
from pathlib import Path

# Trouver le fichier consolidated
data_dir = Path('meteo_marine/data/processed')
consolidated_files = list(data_dir.glob('consolidated_*.parquet'))

if not consolidated_files:
    print("❌ Pas de fichier consolidated_*.parquet trouvé")
    print(f"Fichiers dans {data_dir}:")
    for f in data_dir.glob('*'):
        print(f"  - {f.name}")
else:
    consolidated_file = consolidated_files[0]
    print(f"=== {consolidated_file.name} ===")
    df = pd.read_parquet(consolidated_file)
    print(df.head(2))
    print(f"\nColonnes: {list(df.columns)}")
    print(f"Dtypes:\n{df.dtypes}")
    print(f"\nDates min/max: {df['date'].min()} - {df['date'].max()}")
    print(f"Shape: {df.shape}")
    print(f"\nMissing values:\n{df.isnull().sum()}")
