# Projet Maritime

Projet d'analyse de donnees meteorologiques et d'exploitation des donnees liees aux lignes maritimes entre Marseille, le Frioul, l'Ile d'If, la Pointe Rouge et l'Estaque. Le depot contient surtout un pipeline de preparation des donnees, plusieurs notebooks d'exploration, quelques scripts utilitaires et des exports CSV issus des differentes etapes.

## Objectif

Le but principal est de partir d'un fichier source brut, de le nettoyer, d'en extraire des variables exploitables puis de comparer plusieurs approches de modelisation sur des donnees deja structurees.

Le projet couvre trois blocs :

1. nettoyage et mise en forme des donnees brutes,
2. selection d'un sous-ensemble par ligne / trajet,
3. pretraitement avance et comparaison de modeles.

## Demarrage rapide

Ordre recommande pour travailler sur les donnees :

1. ouvrir et executer `01_cleaning.ipynb` depuis la racine du depot,
2. verifier que `data/maritime_clean.csv` est bien généré,
3. lancer `02_ligne_selector.ipynb` pour produire le sous-ensemble voulu,
4. utiliser `src/preprocessing_utils.py` ou `03_processing_v1.ipynb` pour fabriquer les variables d'analyse,
5. ouvrir `04_model_comparison.ipynb` pour comparer les modeles.

Important : plusieurs chemins sont relatifs et supposent une execution depuis la racine du projet.

## Fonctionnement general

Le flux de travail actuel est le suivant :

1. Le fichier source principal est `data/consolidation_maritime.xlsx`.
2. Le notebook `notebooks/01_cleaning.ipynb` applique le nettoyage initial et exporte `data/maritime_clean.csv`.
3. Le notebook `notebooks/02_ligne_selector.ipynb` isole des sous-ensembles par ligne et peut generer des fichiers comme `VP_if.csv`, `VP_frioul.csv`, `VP_PointeRouge.csv` ou `VP_estaque.csv`.
4. Le module `src/preprocessing_utils.py` transforme ensuite ces donnees en variables utilisables pour l'analyse et la modelisation.
5. Les notebooks `03_processing_v0.ipynb` et `03_processing_v1.ipynb` servent a l'exploration, la visualisation et aux essais de pretraitement.
6. `04_model_comparison.ipynb` charge les donnees pretraitees et compare plusieurs modeles.

En pratique, `data/maritime_clean.csv` est le fichier pivot du projet. Les autres CSV dans `data/` sont des exports intermediaires ou specialises.

## Structure du depot

```text
.
├── data/
│   ├── consolidation_maritime.xlsx
│   ├── maritime_clean.csv
│   ├── VP_if.csv
│   ├── VP_frioul.csv
│   ├── VP_frioul_if.csv
│   ├── VP_If_reduit.csv
│   ├── VP_PointeRouge.csv
│   └── VP_estaque.csv
├── notebooks/
│   ├── 01_cleaning.ipynb
│   ├── 02_ligne_selector.ipynb
│   ├── 03_processing_v0.ipynb
│   ├── 03_processing_v1.ipynb
│   ├── 04_model_comparison.ipynb
│   └── cleanning_old.ipynb
└── src/
    ├── cleaning_utils.py
    └── preprocessing_utils.py

```

## Entrées et sorties par fichier

### Scripts et modules

| Fichier | Entrée | Sortie |
| --- | --- | --- |
| `src/cleaning_utils.py` | Fichier Excel brut, en pratique `data/consolidation_maritime.xlsx`, avec les colonnes `Horaire`, `Ligne`, `Annulation`, `Météo`, `Bateau`, `Capitaine` | DataFrame nettoyé avec `Date`, `Heure`, les sous-colonnes météo, `AnnulationMotif`, `Annulation`, puis colonnes réorganisées prêtes à export |
| `src/preprocessing_utils.py` | CSV ou DataFrame déjà nettoyé, par exemple `data/maritime_clean.csv` ou un sous-ensemble comme `data/frioul_if.csv` | DataFrame transformé pour la modélisation avec `Mois`, `Heure_num`, `JourNuit`, encodages de `Mer`, `Vent`, `Houle`, indicateurs `Mistral` et one-hot encoding des variables nominales |


### Notebooks

| Fichier | Entrée | Sortie |
| --- | --- | --- |
| `notebooks/01_cleaning.ipynb` | Fichier source brut, puis colonnes de nettoyage de type Excel | `data/maritime_clean.csv` |
| `notebooks/02_ligne_selector.ipynb` | `data/maritime_clean.csv` | Sous-ensembles par ligne ou trajet, comme `data/VP_if.csv`, `data/VP_frioul.csv`, `data/VP_PointeRouge.csv`, `data/VP_estaque.csv`, `data/VP_frioul_if.csv`, `data/VP_If_reduit.csv` |
| `notebooks/03_processing_v0.ipynb` | Sous-ensemble CSV, souvent `data/frioul_if.csv` | Données transformées et graphiques ou tableaux d'exploration dans le notebook |
| `notebooks/03_processing_v1.ipynb` | Même type de sous-ensemble nettoyé | Variante de prétraitement, visualisation et essais de features dans le notebook |
| `notebooks/04_model_comparison.ipynb` | Données déjà prétraitées | Comparaison de modèles, scores et graphiques dans le notebook |
| `notebooks/cleanning_old.ipynb` | Ancienne version du flux de nettoyage | Ancienne base nettoyée, conservée à titre d'historique |

### Donnees et artefacts

| Fichier ou dossier | Entrée | Sortie |
| --- | --- | --- |
| `data/maritime_clean.csv` | Produit par `notebooks/01_cleaning.ipynb` ou par les fonctions de `src/cleaning_utils.py` | Base propre utilisée comme point de départ pour les autres étapes |
| `data/VP_if.csv`, `data/VP_frioul.csv`, `data/VP_PointeRouge.csv`, `data/VP_estaque.csv` | Extraits de `data/maritime_clean.csv` filtrés par ligne | Jeux de données spécialisés pour une ligne ou un trajet |
| `data/VP_frioul_if.csv`, `data/VP_If_reduit.csv` | Variantes intermédiaires ou réduites des données de trajet | Jeux de données intermédiaires pour essais de prétraitement ou de modèle |
| `data/old/frioul_if_reduit.csv`, `data/old/frioul_if.csv`, `data/old/maritime_clean.csv`, `data/old/VP_frioul.csv`, `data/old/VP_if.csv` | Anciennes versions des CSV de travail | Archive de comparaison et d'historique |
| `exports/` | Export manuel de travaux de notebook ou de script | Fichiers de sortie ponctuels, à usage de partage ou d'archivage |


Les notebooks et les scripts ci-dessus sont des artefacts de travail et non un pipeline automatise complet.


## Etat actuel du projet

Le depot est dans un etat de travail exploratoire, avec plusieurs elements deja en place mais encore peu industrialises :

- le pipeline de nettoyage et de pretraitement existe et est lisible,
- les donnees intermediaires sont deja exportees en CSV,
- la logique de modelisation est presente dans les notebooks, mais elle reste experimentale,
- il n'y a pas encore de packaging, de CI, ni de suite de tests formalisee,
- plusieurs notebooks et scripts sont des versions de travail ou des archives,

En l'etat, le projet est donc utilisable pour l'exploration et la recherche de features, mais pas encore comme application finale ou bibliotheque stabilisee.

## A faire ensuite

Les prochaines ameliorations naturelles seraient :

1. ajouter un fichier de dependances explicite,
2. factoriser le pipeline dans un vrai point d'entree Python,
3. documenter les formats de fichiers attendus et produits,
4. supprimer les secrets ou jetons hardcodes dans les scripts API,
5. ajouter des tests sur les fonctions de nettoyage et de pretraitement.