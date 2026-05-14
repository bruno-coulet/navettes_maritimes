"""
Stratégie A/B Testing : Maritime vs Meteo_Marine

Objectif : Remplacer consolidation_maritime.xlsx par Open-Meteo (source plus fiable)

=== PHASE 1 : BASELINE (Maritime + consolidation_maritime.xlsx) ===
- Données : consolidation_maritime.xlsx → maritime_clean.csv
- Features : Mer (texte ordinal), Vent (direction), Houle (numérique), Horaire
- Preprocessing : src/preprocessing_utils.py
- Model : RandomForest v1 → artifacts/model.pkl (v1)
- Métriques : à documenter
- Commande : python src/train_annulation.py

=== PHASE 2 : TEST (Meteo_Marine + Open-Meteo consolidé) ===
- Données : meteo_marine/data/processed/consolidated_*.parquet
- Features : hauteur vagues (float), direction (float), température, vent (float)
- Preprocessing : à créer (adapter preprocessing_utils pour Open-Meteo)
- Model : RandomForest v2 → meteo_marine/artifacts/model_openmeteo.pkl
- Métriques : comparer avec v1
- Commande : python -m src.train_openmeteo ou python -m src.train_annulation_v2

=== PHASE 3 : DÉCISION ===
Si v2 (Open-Meteo) meilleur (accuracy, f1) → migrer pipeline
Si v1 (Maritime) meilleur → rester sur consolidation_maritime.xlsx

=== DIVERGENCES À RÉSOUDRE ===

1. **Colonnes d'entrée** :
   - Maritime : Horaire, Mer, Vent, Houle, ... (texte + numérique mixte)
   - Open-Meteo : wave_height, wave_direction, wind_speed, temperature, ... (numérique pur)

2. **Cible (Annulation)** :
   - Maritime : existe dans consolidation_maritime.xlsx
   - Open-Meteo : ABSENTE ! Faut-il merger avec maritime_clean.csv sur date ?

3. **Temporalité** :
   - Maritime : données historiques (dates non spécifiées)
   - Open-Meteo : 2024-01-01 à 2026-04-30 (configurable)

=== BLOCAGE POTENTIEL ===

Open-Meteo produit des DONNÉES MÉTÉO uniquement, pas des étiquettes d'annulation.

Options :
A) Merger Open-Meteo + consolidation_maritime.xlsx par date/heure
   → Combiner 2 sources
B) Supposer que consolidation_maritime.xlsx représente la période couverte par Open-Meteo
   → Substituer colonnes météo, garder Annulation

=== PROCHAINES ACTIONS ===

1. Charger maritime_clean.csv actuel → inspirer les colonnes, la cible
2. Charger meteo_marine consolidated → inspirer les colonnes disponibles
3. Décider : option A (merge) ou B (substitution de colonnes)
4. Créer preprocessing adapter pour Open-Meteo
5. Entraîner, comparer, décider
"""
