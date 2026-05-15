import pandas as pd

print("=== maritime_clean.csv ===")
df = pd.read_csv('data/maritime_clean.csv')
print(df.head(2))
print(f"\nColonnes: {list(df.columns)}")
print(f"Horaire dtype: {df['Horaire'].dtype}")
print(f"Dates min/max: {df['Horaire'].min()} - {df['Horaire'].max()}")
print(f"Shape: {df.shape}")
print(f"Annulation values: {df['Annulation'].unique()}")
