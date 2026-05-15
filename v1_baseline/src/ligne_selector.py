"""Selection des sous-ensembles de lignes maritimes.

Responsabilite:
- filtrer `maritime_clean.csv` par groupe de lignes
- generer les CSV specialises dans `data/lignes/`

Entrees:
- `data/maritime_clean.csv`

Sorties:
- fichiers CSV de lignes/trajets dans `data/lignes/`

Commande:
- `python src/ligne_selector.py`
"""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.paths import find_project_root, get_data_dir, get_lignes_dir


def ligne_selector(df, groupe):
    """
    Filtre le DataFrame selon des groupes de lignes prédéfinis.
    
    Paramètres :
    -----------
    df : pd.DataFrame
        DataFrame contenant les données avec colonne 'Ligne'
    groupe : str
        Nom du groupe parmi:
        - 'VP_frioul_if': Tous les trajets Vieux Port/Frioul/IF confondus
        - 'Frioul_if': Uniquement Frioul-IF
        - 'VP_frioul': Vieux Port-Frioul uniquement
        - 'VP_if': Vieux Port-IF uniquement
        - 'VP_PR': Vieux Port-Pointe Rouge uniquement
        - 'VP_estaque': Vieux Port-Estaque uniquement
        - 'PR_goudes': Pointe Rouge-Goudes uniquement
        - 'PointeRouge': Tous trajets Pointe Rouge confondus
        - 'Estaque': Tous trajets Estaque confondus
        - 'Departs': Tous les départs principaux
    
    Retour :
    --------
    pd.DataFrame
        DataFrame filtré contenant uniquement les lignes du groupe spécifié
    
    Lève :
    ------
    ValueError
        Si le groupe spécifié n'est pas reconnu
    """
    
    # Définition des groupes de lignes
    groupes = {
        # Toutes lignes confondues 
        'VP_frioul_if': ['Vieux Port-Frioul', 'Frioul-Vieux Port', 
                         'Vieux Port-IF', 'IF-Frioul', 'Frioul-IF', 'IF-Vieux Port'],
        
        'Frioul_if': ['Frioul-IF'],
        
        # Tous les départs pris individuellement
        'VP_frioul': ['Vieux Port-Frioul'],
        'VP_if': ['Vieux Port-IF'],
        'VP_PR': ['Vieux Port-Pointe Rouge'],
        'VP_estaque': ['Vieux Port-Estaque'],
        'PR_goudes': ['Pointe Rouge-Goudes'],
        
        # Tous les départs en bloc
        'Departs': [
            'Vieux Port-Frioul',
            'Vieux Port-IF',
            'Vieux Port-Pointe Rouge',
            'Vieux Port-Estaque',
            'Pointe Rouge-Goudes'
        ],
        
        'PointeRouge': ['Pointe Rouge-Vieux Port', 'Vieux Port-Pointe Rouge',
                        'Pointe Rouge-Goudes', 'Goudes-Pointe Rouge'],
        
        'Estaque': ['Estaque-Vieux Port', 'Vieux Port-Estaque']
    }
    
    # Vérification de la validité du groupe
    if groupe not in groupes:
        raise ValueError(f"Le groupe doit être l'un des suivants : {list(groupes.keys())}")
    
    # Filtrage du DataFrame
    return df[df['Ligne'].isin(groupes[groupe])]


if __name__ == "__main__":
    data_root = find_project_root(Path(__file__))
    data_dir = data_root / "data"
    lignes_dir = get_lignes_dir()

    if not data_dir.exists():
        raise FileNotFoundError(f"Le répertoire {data_dir} n'existe pas !")

    lignes_dir.mkdir(exist_ok=True, parents=True)
    print(f"Répertoire d'export: {lignes_dir}")
    
    # Configuration des exports
    export_config = [
        ('VP_frioul_if', 'VP_frioul_if.csv'),
        ('Frioul_if', 'Frioul_if.csv'),
        ('VP_frioul', 'VP_frioul.csv'),
        ('VP_if', 'VP_if.csv'),
        ('VP_PR', 'VP_PR.csv'),
        ('VP_estaque', 'VP_estaque.csv'),
        ('PR_goudes', 'PR_goudes.csv'),
    ]
    
    # Charger les données nettoyées
    source_file = data_dir / "maritime_clean.csv"
    print(f"Chargement de {source_file}...")
    
    if not source_file.exists():
        raise FileNotFoundError(f"Fichier source non trouvé: {source_file}")
    
    df = pd.read_csv(source_file, index_col=0)
    
    # Générer les fichiers de chaque ligne
    for groupe, filename in export_config:
        try:
            df_selected = ligne_selector(df, groupe)
            output_path = lignes_dir / filename
            df_selected.to_csv(output_path, index=True)
            print(f"✓ {filename} généré ({len(df_selected)} lignes)")
        except ValueError as e:
            print(f"✗ Erreur pour {groupe}: {e}")
        except Exception as e:
            print(f"✗ Erreur lors de l'export de {filename}: {e}")
    
    print("\nGénération des fichiers de lignes terminée !")
