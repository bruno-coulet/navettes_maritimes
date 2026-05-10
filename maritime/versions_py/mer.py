import pandas as pd
import re

# Charger le fichier Excel
df = pd.read_excel('data/consolidation_maritime.xlsx')

# Fonction d'extraction avec regex
def extraire_infos(texte):
    # Initialiser les valeurs par défaut
    vent_direction = vent_noeuds = Bft = mer = vagues_1 = vagues_2 = vagues_3 = None

    # Vent : direction, noeuds, Bft
    vent_match = re.search(r'Vent\s*:\s*([A-Z]+)\s*(\d+)\s*Nds/(\d+)\s*Bft', str(texte))
    if vent_match:
        vent_direction = vent_match.group(1)
        vent_noeuds = int(vent_match.group(2))
        Bft = int(vent_match.group(3))
    
    # Mer : état, vagues_1, vagues_2, vagues_3
    mer_match = re.search(r'Mer\s*:\s*([^\d]+?)(\d+,\d+)/(\d+,\d+)m\s+(\d+°\s*\d+s)', str(texte))
    if mer_match:
        mer = mer_match.group(1).strip()
        vagues_1 = float(mer_match.group(2).replace(',', '.'))
        vagues_2 = float(mer_match.group(3).replace(',', '.'))
        vagues_3 = mer_match.group(4).strip()
    else:
        # Cas où il n'y a pas toutes les infos sur les vagues
        mer_simple = re.search(r'Mer\s*:\s*([^\d]+)', str(texte))
        if mer_simple:
            mer = mer_simple.group(1).strip()
    
    return pd.Series([vent_direction, vent_noeuds, Bft, mer, vagues_1, vagues_2, vagues_3],
                    index=['vent_direction', 'vent_noeuds', 'Bft', 'mer', 'vagues_1', 'vagues_2', 'vagues_3'])

# Appliquer la fonction à la colonne G (remplacez 'G' par le nom réel de la colonne si besoin)
df[['vent_direction', 'vent_noeuds', 'Bft', 'mer', 'vagues_1', 'vagues_2', 'vagues_3']] = df['G'].apply(extraire_infos)

# Sauvegarder le résultat
df.to_excel('consolidation_maritime_extrait.xlsx', index=False)
