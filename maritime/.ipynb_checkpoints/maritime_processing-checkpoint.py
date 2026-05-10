import pandas as pd, numpy as np, seaborn as sns, datetime, matplotlib.pyplot as plt, pytz, cartopy.crs as ccrs
from astral.sun import sun
from astral import LocationInfo
from matplotlib.colors import LinearSegmentedColormap
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from pandas.plotting import scatter_matrix




# === CONFIGURATION ===
pd.set_option("display.max_columns", None)

# === IMPORT DU FICHIER ===
source = '../data/frioul_if.csv'
df = pd.read_csv(source, index_col=0)

# === CONVERSION DES DATES/HEURES ===
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Mois'] = df['Date'].dt.month

if 'Heure' in df.columns:
    df['Heure'] = pd.to_datetime('2000-01-01 ' + df['Heure'].astype(str), errors='coerce')
    df['Heure_num'] = df['Heure'].dt.hour

if 'Horaire' in df.columns:
    df['Horaire'] = pd.to_datetime(df['Horaire'], errors='coerce')

# === GESTION FUSEAU HORAIRE ET POSITION ===
paris_tz = pytz.timezone('Europe/Paris')
marseille = LocationInfo("Marseille", "France", "Europe/Paris", latitude=43.2965, longitude=5.3698)

def jourNuit(horaire):
    if pd.isna(horaire):
        return np.nan
    if horaire.tzinfo is None:
        dt_obs = paris_tz.localize(horaire)
    else:
        dt_obs = horaire.astimezone(paris_tz)
    date_obj = dt_obs.date()
    s = sun(marseille.observer, date=date_obj, tzinfo=paris_tz)
    lever = s['sunrise']
    coucher = s['sunset']
    if dt_obs < lever:
        delta = dt_obs - lever
    elif dt_obs > coucher:
        delta = dt_obs - coucher
    else:
        delta = datetime.timedelta(0)
    return round(delta.total_seconds() / 60)

df['JourNuit'] = df['Horaire'].apply(jourNuit)

# === ENCODAGE ORDINAL : état de la mer ===
df['Mer'] = pd.Categorical(
    df['Mer'],
    categories=['ridée', 'belle', 'peu agitée', 'agitée', 'forte'],
    ordered=True
).codes

# === ENCODAGE DU VENT ET DE LA HOULE ===

# Mapping directions cardinales
directions = {
    'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
    'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
    'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
    'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
}

# Vent : conversion en angle puis en composantes
df['Vent_deg'] = df['Vent'].map(directions)
df['Vent_rad'] = np.deg2rad(df['Vent_deg'])
df['Vent_x'] = np.cos(df['Vent_rad'])
df['Vent_y'] = np.sin(df['Vent_rad'])

# Houle : déjà en degrés
df['Houle_rad'] = np.deg2rad(df['Houle'])
df['Houle_x'] = np.cos(df['Houle_rad'])
df['Houle_y'] = np.sin(df['Houle_rad'])

# Détection des directions dangereuses (Mistral : 270°–360° + 0°)
def mistral(angle_deg):
    if angle_deg is None or np.isnan(angle_deg):
        return 0
    angle_deg = angle_deg % 360
    return int(270 <= angle_deg <= 360 or angle_deg == 0)

# Appliquer la logique de danger
df['Vent_deg'] = np.rad2deg(np.arctan2(df['Vent_y'], df['Vent_x'])) % 360
df['Vent_danger'] = df['Vent_deg'].apply(mistral)

df['Houle_deg'] = np.rad2deg(np.arctan2(df['Houle_y'], df['Houle_x'])) % 360
df['Houle_danger'] = df['Houle_deg'].apply(mistral)

# === SUPPRESSION DES VARIABLES INTERMÉDIAIRES OU REDONDANTES ===
df.drop(columns=[
    'AnnulationMotif',   # cible inutile
    'Vent', 'Vent_deg', 'Vent_rad', 'Vent_x', 'Vent_y',
    'Houle', 'Houle_deg', 'Houle_rad', 'Houle_x', 'Houle_y'
], errors='ignore', inplace=True)



nominal_features = ['Ligne', 'Bateau', 'Ciel', 'Capitaine']
# Initialise l’encodeur
encoder = OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore')
# Encoder les colonnes sélectionnées
encoded_array = encoder.fit_transform(df[nominal_features])
# Récupérer les noms des nouvelles colonnes
encoded_cols = encoder.get_feature_names_out(nominal_features)
# Créer un DataFrame avec les colonnes encodées
encoded_df = pd.DataFrame(encoded_array, columns=encoded_cols, index=df.index)
# Concaténer avec les autres colonnes non encodées
df = pd.concat([df.drop(columns=nominal_features), encoded_df], axis=1)


df_numeric = df.select_dtypes(include=['number'])
df_corr    = df.select_dtypes(include=['number', 'bool'])