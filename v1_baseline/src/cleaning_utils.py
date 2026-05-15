"""Nettoyage initial des donnees maritimes.

Responsabilite:
- charger le fichier source brut `consolidation_maritime.xlsx`
- nettoyer les colonnes horaires et meteo
- produire une base normalisee prete pour l'etape de selection de ligne

Entrees:
- fichier Excel brut contenant `Horaire`, `Ligne`, `Annulation`, `Meteo`, `Bateau`, `Capitaine`

Sorties:
- DataFrame nettoye avec colonnes `Date`, `Heure`, variables meteo et cible `Annulation`

Commande:
- importe comme module depuis `src/` ou depuis les notebooks de nettoyage
"""

import pandas as pd
import hashlib

def anonymize_capitaine(name, salt="marseille_2026"):
    """
    Transforme un nom de capitaine en ID unique anonyme.
    """
    if not isinstance(name, str):
        return "INCONNU"
    
    # Combine le nom avec un sel secret pour plus de sécurité
    hash_object = hashlib.sha256((name + salt).encode())
    # Ne garde que les 8 premiers caractères pour la lisibilité
    return hash_object.hexdigest()[:8]

    # Exemple d'application sur le DataFrame
    # df['Capitaine'] = df['Capitaine'].apply(anonymize_capitaine)


def load_raw_data(path):
    return pd.read_excel(
        path,
        header=0,
        skiprows=[1],
        usecols=['Horaire', 'Ligne', 'Annulation', 'Météo', 'Bateau', 'Capitaine']
    )




def clean_raw_data(df):
    '''
    nettoyage Horaire, Météo = ?, parsing des colonnes météo
    conversion des unités, nettoyage texte
    transformation des colonnes (float, datetime)
    annulation = 0/1
    '''
    df.dropna(subset=['Horaire'], inplace=True)
    df['Horaire'] = pd.to_datetime(df['Horaire'], format="%d/%m/%Y %H:%M", errors='coerce')
    df['Date'] = df['Horaire'].dt.date
    df['Heure'] = df['Horaire'].dt.time
    df = df[df['Météo'] != '?'].copy()

    # Séparation météo
    df['Meteo1'] = df['Météo'].str.extract(r'^(.*?)\b(Vent|Mer)\b', expand=False)[0]
    df['MeteoVent'] = df['Météo'].str.extract(r'(Vent.*?)(?=Mer\b)', expand=False)
    df['MeteoHoule'] = df['Météo'].str.extract(r'(Mer\s*:?.*)$', expand=False)

    df['Temperature'] = df['Meteo1'].str.extract(r'(?P<Temperature>\d+)°')
    df['Ciel'] = df['Meteo1'].str.extract(r'\d+°\s*(.*)')

    vent_regex = r'Vent\s*:?\s*(?P<Vent>[A-Z]{1,3})?\s*(?P<VentNoeud>\d+)\s*Nds/?(?P<VentBeaufort>\d+)\s*Bft'
    df = pd.concat([df, df['MeteoVent'].str.extract(vent_regex)], axis=1)

    df['MeteoHoule_clean'] = df['MeteoHoule'].str.replace(r'([a-zé])(\d)', r'\1 \2', regex=True)

    mer_regex = (
        r'Mer\s*:?\s*'
        r'(?P<Mer>[^\d]+)?\s*'
        r'(?P<HouleDominante>\d+[.,]?\d*)/?'
        r'(?P<HouleMax>\d+[.,]?\d*)?m?\s*'
        r'(?P<Houle>\d+)?°?\s*'
        r'(?P<HoulePeriode>\d+)?s?'
    )
    df = pd.concat([df, df['MeteoHoule'].str.extract(mer_regex)], axis=1)

    cols_to_float = ['Temperature', 'VentNoeud', 'VentBeaufort',
                     'HouleDominante', 'HouleMax', 'Houle', 'HoulePeriode']
    for col in cols_to_float:
        df[col] = df[col].str.replace(',', '.').astype(float)

    df.drop(['Météo', 'Meteo1', 'MeteoVent', 'MeteoHoule'], axis=1, inplace=True)
    df.dropna(subset=['Vent', 'Houle'], inplace=True)

    df.rename(columns={'Annulation': 'AnnulationMotif'}, inplace=True)
    df['Annulation'] = df['AnnulationMotif'].notna().astype(int)

    return df


def reorganize_columns(df):
    colonnes = ['Horaire', 'Annulation', 'AnnulationMotif', 'Ligne',
                'Vent', 'VentNoeud', 'HouleDominante', 'HouleMax',
                'Houle', 'HoulePeriode', 'Mer', 'Temperature', 'Ciel',
                'Bateau', 'Capitaine']
    return df[colonnes]

