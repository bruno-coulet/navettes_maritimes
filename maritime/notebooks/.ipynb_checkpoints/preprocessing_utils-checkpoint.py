import pandas as pd
import numpy as np
import datetime
import pytz
from astral import LocationInfo
from astral.sun import sun
from matplotlib.colors import LinearSegmentedColormap
from sklearn.preprocessing import OneHotEncoder




# === PARAMÈTRES GÉNÉRAUX ===
PARIS_TZ = pytz.timezone('Europe/Paris')
MARSEILLE = LocationInfo("Marseille", "France", "Europe/Paris", latitude=43.2965, longitude=5.3698)
CMAP = LinearSegmentedColormap.from_list("green_red", ["green", "lightgrey", "red"], N=256)




# === CONVERSION DES DATES/HEURES ===
def convert_datetime_columns(df):
    """
    Convertit les colonnes de dates et heures en objets datetime, et extrait des informations utiles.
    """
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Mois'] = df['Date'].dt.month
    if 'Heure' in df.columns:
        df['Heure'] = pd.to_datetime('2000-01-01 ' + df['Heure'].astype(str), errors='coerce')
        df['Heure_num'] = df['Heure'].dt.hour
    if 'Horaire' in df.columns:
        df['Horaire'] = pd.to_datetime(df['Horaire'], errors='coerce')
    return df
    

# === GESTION FUSEAU HORAIRE ET POSITION ===
def jour_nuit(horaire, location=MARSEILLE, tz=PARIS_TZ):
    """
    Calcule la différence en minutes entre l'horaire observé et le lever/coucher du soleil à Marseille.
    Retourne jour = 0, Nuit = Int (nombre de minute depuis/avant le levé/couché du soleil), np.nan si horaire manquant.
    """
    if pd.isna(horaire):
        return np.nan
    if horaire.tzinfo is None:
        dt_obs = tz.localize(horaire)
    else:
        dt_obs = horaire.astimezone(tz)
    date_obj = dt_obs.date()
    s = sun(location.observer, date=date_obj, tzinfo=tz)
    lever, coucher = s['sunrise'], s['sunset']
    if dt_obs < lever:
        delta = dt_obs - lever
    elif dt_obs > coucher:
        delta = dt_obs - coucher
    else:
        delta = datetime.timedelta(0)
    return round(delta.total_seconds() / 60)


# === ENCODAGE ORDINAL : état de la mer, de 'ridée' = 0 jusqu'à 'forte' = 4   ===
def encode_ordinal_mer(df):
    """
    Encode la colonne 'Mer' de façon ordinale selon l'état de la mer.
    """
    df['Mer'] = pd.Categorical(
        df['Mer'],
        categories=['ridée', 'belle', 'peu agitée', 'agitée', 'forte'],
        ordered=True
    ).codes
    return df



# === ENCODAGE DU VENT ET DE LA HOULE ===

def encode_direction(df, col, mapping=None):
    """
    Encode une direction cardinales en angle, puis en composantes x/y.   ( x = cosinus, y = sinus )
    Si mapping est None, suppose que la colonne est déjà en degrés.
    Retourne df avec colonnes _deg, _rad, _x, _y.
    
    """
    if mapping:
        df[f'{col}_deg'] = df[col].map(mapping)
    else:
        df[f'{col}_deg'] = df[col]
    df[f'{col}_rad'] = np.deg2rad(df[f'{col}_deg'])
    df[f'{col}_x'] = np.cos(df[f'{col}_rad'])
    df[f'{col}_y'] = np.sin(df[f'{col}_rad'])
    return df


# Détection des directions Mistraleuses (Mistral : 270°–360° + 0°)
def mistral(angle_deg):
    """
    Détecte si l'angle (en degrés) correspond à une direction de mistral (270°–360° ou 0°).
    """
    if angle_deg is None or np.isnan(angle_deg):
        return 0
    angle_deg = angle_deg % 360
    return int(270 <= angle_deg <= 360 or angle_deg == 0)



def add_mistral_flag(df, col_prefix):
    """
    Ajoute une colonne binaire '{col_prefix}_mistral' selon la logique mistral.
    """
    deg_col = f'{col_prefix}_deg'
    # Recalcule l'angle à partir des composantes pour robustesse
    df[deg_col] = np.rad2deg(np.arctan2(df[f'{col_prefix}_y'], df[f'{col_prefix}_x'])) % 360
    df[f'{col_prefix}Mistral'] = df[deg_col].apply(mistral)
    return df

def one_hot_encode(df, columns):
    """
    Applique un encodage one-hot sur les colonnes catégorielles spécifiées.
    """
    encoder = OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore')
    encoded_array = encoder.fit_transform(df[columns])
    encoded_cols = encoder.get_feature_names_out(columns)
    encoded_df = pd.DataFrame(encoded_array, columns=encoded_cols, index=df.index)
    df = pd.concat([df.drop(columns=columns), encoded_df], axis=1)
    return df



def preprocess_maritime_data(source):
    """
    Pipeline complet de prétraitement de source
    """
    # Import
    df = pd.read_csv(source, index_col=0)
    # Dates/heures
    df = convert_datetime_columns(df)
    # Jour/Nuit
    if 'Horaire' in df.columns:
        df['JourNuit'] = df['Horaire'].apply(jour_nuit)
    # Ordinal Mer
    if 'Mer' in df.columns:
        df = encode_ordinal_mer(df)
    # Directions
    directions = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    }
    if 'Vent' in df.columns:
        df = encode_direction(df, 'Vent', mapping=directions)
        df = add_mistral_flag(df, 'Vent')
    if 'Houle' in df.columns:
        df = encode_direction(df, 'Houle')
        df = add_mistral_flag(df, 'Houle')
    # Nettoyage
    df.drop(columns=[
        'AnnulationMotif', 'Vent', 'Vent_deg', 'Vent_rad', 'Vent_x', 'Vent_y',
        'Houle', 'Houle_deg', 'Houle_rad', 'Houle_x', 'Houle_y'
    ], errors='ignore', inplace=True)
    # One-hot encoding
    nominal_features = ['Ligne', 'Bateau', 'Ciel', 'Capitaine']
    df = one_hot_encode(df, [col for col in nominal_features if col in df.columns])
    return df