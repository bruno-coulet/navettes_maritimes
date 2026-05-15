# Workflow ML - open_meteo Marseille

## Structure des données

```
data/
├── raw/    # Données brutes organisées en fichiers mensuels par année
│   ├── 2024/
│   │   └── meteo_2024_12_01-au-12_31.csv
│   ├── 2025/
│   │   ├── meteo_2025_01_01-au-01_31.csv
│   │   ├── meteo_2025_02_01-au-02_28.csv
│   │   └── meteo_2025_11_01-au-11_30.csv
│   └── 2026/
│       └── meteo_2026_01_01-au-01_22.csv
└── processed/                    # Données consolidées pour ML
    ├── consolidated_2025_09_01-au-02_28.parquet
    ├── train.parquet             # 70% des données
    ├── val.parquet               # 15% des données
    └── test.parquet              # 15% des données
```

## Workflow complet

### Étape 1: Récupérer les données brutes

```bash
uv run -m src.collect
```

**Options de personnalisation** (en début du script):
```python
START_DATE = None      # None = il y a 730 jours, ou "2025-01-22"
END_DATE = None        # None = aujourd'hui, ou "2026-01-22"
```

**Résultat:**
- Crée des fichiers CSV mensuels: `data/raw/YYYY/meteo_YYYY_MM_DD-au-MM_DD.csv`
- Chaque fichier contient les données quotidiennes de vagues, vent, température, etc.

### Étape 2: Consolider

```bash
uv run -m src.consolidate
```

**Résultat:**
- `data/processed/consolidated_YYYY_MM_DD-au-MM_DD.parquet` → toutes les données fusionnées

### Étape 3: Créer les splits

```bash
uv run -m src.split
```

**Résultat:**
- `data/processed/train.parquet` → 70% des données (entraînement)
- `data/processed/val.parquet` → 15% des données (validation)
- `data/processed/test.parquet` → 15% des données (test)

## Données disponibles

Chaque ligne représente un jour avec les colonnes:

### Données marines
- `wave_height_max` - Hauteur max des vagues (m)
- `wave_direction_dominant` - Direction des vagues (°)
- `wave_period_max` - Période des vagues (s)
- `wind_wave_height_max` - Hauteur vagues de vent (m)
- `swell_wave_height_max` - Hauteur de la houle (m)

### Données météo
- `temperature_max` - Température max (°C)
- `temperature_min` - Température min (°C)
- `wind_speed_max` - Vitesse vent max (km/h)
- `wind_gusts_max` - Rafales max (km/h)
- `wind_direction_dominant` - Direction vent (°)

### Métadonnées
- `date` - Date (YYYY-MM-DD)

## Utilisation en ML

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Charger les données
train_df = pd.read_parquet('data/processed/train.parquet')
val_df = pd.read_parquet('data/processed/val.parquet')
test_df = pd.read_parquet('data/processed/test.parquet')

# Préparation des features et cible
X_train = train_df.drop('date', axis=1)
X_val = val_df.drop('date', axis=1)
X_test = test_df.drop('date', axis=1)

# Normalisation
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)
X_test = scaler.transform(X_test)

# ... votre modèle ML ici
```

## Notes importantes

✅ Les données sont **temporellement ordonnées** → pas de mélange train/test aléatoire naïf  
✅ Format Parquet typé → plus compact et plus robuste pour le pipeline ML  
✅ Données historiques fiables → source open_meteo (réanalyse ERA5)  
✅ Structure modulaire → facile de rajouter de nouvelles périodes
