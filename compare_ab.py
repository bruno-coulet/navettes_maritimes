import json
from pathlib import Path

print("="*60)
print("COMPARAISON A/B : v1 Maritime vs v2 Open-Meteo")
print("="*60)

# Charger v1
v1_path = Path("maritime/artifacts/models_v1_20260513_145955/version.json")
with open(v1_path) as f:
    v1 = json.load(f)

# Charger v2 (Open-Meteo)
v2_path = Path("meteo_marine/artifacts/features_openmeteo.json")
with open(v2_path) as f:
    v2 = json.load(f)

m1 = v1["metrics"]
m2 = v2["metrics"]

print(f"\n{'Métrique':<15} {'v1 Maritime':<20} {'v2 Open-Meteo':<20} {'Δ':<15}")
print("-" * 70)

for key in ["accuracy", "precision", "recall", "f1"]:
    v1_val = m1.get(key, 0)
    v2_val = m2.get(key, 0)
    delta = v2_val - v1_val
    delta_str = f"{delta:+.4f}"
    print(f"{key:<15} {v1_val:<20.4f} {v2_val:<20.4f} {delta_str:<15}")

print("\n" + "="*60)
print("RÉSUMÉ")
print("="*60)

print(f"\n✓ v1 Maritime")
print(f"  - Source: consolidation_maritime.xlsx (79k horaires)")
print(f"  - Features: 136 (Vent, Houle, Température, encodées)")
print(f"  - Accuracy: {m1['accuracy']:.4f}")
print(f"  - F1-Score: {m1['f1']:.4f}")

print(f"\n✓ v2 Open-Meteo")
print(f"  - Source: Open-Meteo merged (719 jours)")
print(f"  - Features: {v2['n_features']} (wave_height, temperature, wind, etc)")
print(f"  - Accuracy: {m2['accuracy']:.4f}")
print(f"  - F1-Score: {m2['f1']:.4f}")

if m1["f1"] > m2["f1"]:
    print(f"\n🏆 GAGNANT : v1 Maritime (F1 +{m1['f1'] - m2['f1']:.4f})")
    print(f"\nRecommandation: Rester sur consolidation_maritime.xlsx pour le moment")
else:
    print(f"\n🏆 GAGNANT : v2 Open-Meteo (F1 +{m2['f1'] - m1['f1']:.4f})")
    print(f"\nRecommandation: Migrer vers Open-Meteo")

print(f"\n" + "="*60)
