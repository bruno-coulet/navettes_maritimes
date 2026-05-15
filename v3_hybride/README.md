Entrée : maritime_clean.csv + consolidated_...parquet

Sortie : training_merged_v3.parquet

2. Entraînement du modèle
Le script transforme les catégories (Capitaine, Bateau, Ligne) en 146 features via le One-Hot Encoding et entraîne un RandomForest.

```Bash
uv run train_v3.py
````

Artifacts générés : model_v3.pkl, metrics_v3.json, features_v3.json dans le dossier artifacts/.

3. Comparaison Finale
Compare les performances de la V3 avec les versions précédentes (V1 Maritime et V2 Météo seule).

```Bash
uv run compare_v3.py
````

📊 Pourquoi la V3 ?
Expertise Humaine : Intègre le jugement des capitaines.

Granularité : Analyse chaque traversée individuellement (60k+ lignes).

Performance : F1-Score exceptionnel (~0.93) et Recall élevé (~0.91).



### 1. Pourquoi créer `compare_v3.py` au lieu de modifier l'ancien ?
L'ancien script `compare_final.py` était figé sur la correction de l'erreur V2. Plutôt que de "bricoler" dedans, je t'en ai créé un nouveau, **`compare_v3.py`**, qui est configuré spécifiquement pour afficher ton nouveau "Champion" (la V3 Hybride) face aux anciens modèles.

Tes fichiers sont prêts ici :
[file-tag: code-generated-file-1-1778763365630716787]
[file-tag: code-generated-file-0-1778763365630711403]

---

### 📖 Le nouveau Workflow V3 résumé

Voici comment s'enchaînent tes scripts maintenant pour obtenir et valider ta V3 :

1.  **`uv run features_v3.py`** : 
    * *Rôle* : Fait la fusion (Merge) entre tes données de navigation et la météo.
    * *Résultat* : Crée le fichier `training_merged_v3.parquet`.

2.  **`uv run train_v3.py`** :
    * *Rôle* : C'est le moteur. Il transforme tes textes (Capitaines, Bateaux) en nombres (**One-Hot Encoding**) et entraîne l'IA.
    * *Résultat* : C'est lui qui t'a sorti tes super scores (F1: 0.93) et qui crée le fichier `metrics_v3.json`.

3.  **`uv run compare_v3.py`** (Le nouveau) :
    * *Rôle* : Il va lire les petits fichiers de résultats (`.json`) de toutes tes versions et te sortir le tableau comparatif final.


Entrée : maritime_clean.csv + consolidated_...parquet

Sortie : training_merged_v3.parquet

2. Entraînement du modèle
Le script transforme les catégories (Capitaine, Bateau, Ligne) en 146 features via le One-Hot Encoding et entraîne un RandomForest.

Bash
uv run train_v3.py
Artifacts générés : model_v3.pkl, metrics_v3.json, features_v3.json dans le dossier artifacts/.

3. Comparaison Finale
Compare les performances de la V3 avec les versions précédentes (V1 Maritime et V2 Météo seule).

Bash
uv run compare_v3.py
📊 Pourquoi la V3 ?
Expertise Humaine : Intègre le jugement des capitaines.

Granularité : Analyse chaque traversée individuellement (60k+ lignes).

Performance : F1-Score exceptionnel (~0.93) et Recall élevé (~0.91).