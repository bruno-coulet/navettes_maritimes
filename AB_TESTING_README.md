# 🔄 Stratégie A/B Testing : Maritime vs Open-Meteo

## Objectif

Remplacer `consolidation_maritime.xlsx` par **Open-Meteo** (source plus fiable et automatisée).

Avant de faire la migration complète, on teste les deux sources sur **métriques**.

---

## 📋 Plan d'exécution

### **Étape 1 : Baseline Maritime (v1)**

Réentraîner le modèle actuel avec données existantes :

```bash
cd maritime
python -m src.retrain --version v1 --data-source maritime
```

**Résultat** :
- Modèle sauvegardé dans `artifacts/models_v1_YYYYMMDD_HHMMSS/`
- Fichiers : `model.pkl`, `features.json`, `version.json`
- Métriques enregistrées pour comparaison

**Données utilisées** :
- Source : `data/maritime_clean.csv`
- Features : Mer (ordinal), Vent (direction), Houle, Horaire
- Cible : Annulation

---

### **Étape 2 : Test Open-Meteo (v2)**

Avant d'entraîner sur Open-Meteo, il faut :

#### 2a) Générer les données Open-Meteo consolidées

```bash
cd meteo_marine
python -m src.pipeline  # Collecte → consolidation → split
# OU pas à pas :
python -m src.collect
python -m src.consolidate
python -m src.split
```

**Résultat** :
- Fichiers consolidés dans `data/processed/consolidated_*.parquet`
- Splits train/val/test générés

#### 2b) Adapter le preprocessing pour Open-Meteo

**Problème** : Open-Meteo donne des données MÉTÉO uniquement, pas d'étiquette "Annulation".

**Solution** :
- Merger `consolidated.parquet` avec `maritime_clean.csv` sur la date
- OU supposer que maritime_clean.csv couvre la même période et remplacer colonnes météo

**Créer** `meteo_marine/src/train_openmeteo.py` (copie de `maritime/train_annulation.py` adapté)

#### 2c) Entraîner sur Open-Meteo

```bash
cd meteo_marine
python -m src.train_openmeteo  # À créer
# OU depuis maritime avec option :
cd maritime
python -m src.retrain --version v2_openmeteo --data-source openmeteo --csv-path ../meteo_marine/data/processed/consolidated_*.parquet
```

---

### **Étape 3 : Comparer les modèles**

```bash
cd maritime
python -m src.retrain --compare artifacts/models_v1_YYYYMMDD_HHMMSS artifacts/models_v2_YYYYMMDD_HHMMSS
```

**Résultat** :
```
Métrique       Version 1       Version 2       Δ
accuracy       0.7850          0.8120          +0.0270
precision      0.8100          0.8350          +0.0250
recall         0.7200          0.7650          +0.0450
f1             0.7640          0.7990          +0.0350

✓ Meilleur modèle (F1) : Version 2
```

---

### **Étape 4 : Décision et Migration**

#### Si v2 (Open-Meteo) **meilleur** :
- Copier `models_v2_*/model.pkl` → `artifacts/model.pkl`
- Mettre à jour `navettes/src/predict_annulation.py` si features changent
- Documenter changement dans CHANGELOG

#### Si v1 (Maritime) **meilleur** :
- Rester sur consolidation_maritime.xlsx
- Archiver approche Open-Meteo pour référence future

---

## 🔍 Points d'attention

### Divergences à résoudre avant entraînement

| Aspect | Maritime (v1) | Open-Meteo (v2) |
|--------|--------|--------|
| **Source** | consolidation_maritime.xlsx | Open-Meteo API |
| **Format données** | CSV texte/numérique mixte | Parquet numérique pur |
| **Colonnes météo** | Mer (texte ordinal), Vent (direction°), Houle | wave_height, wind_speed, temperature, ... |
| **Cible (Annulation)** | ✓ Présente dans xlsx | ✗ ABSENT : faut-il merger avec maritime ? |
| **Temporalité** | Historique (dates ?) | 2024-01-01 → 2026-04-30 |

### Décision critique

**Comment obtenir l'étiquette "Annulation" pour Open-Meteo ?**

Option A) **Merger par date** :
```python
# Charger Open-Meteo + maritime_clean
open_meteo_df = pd.read_parquet("meteo_marine/data/processed/consolidated.parquet")
maritime_df = pd.read_csv("maritime/data/maritime_clean.csv")

# Merger sur Date
merged = open_meteo_df.merge(
    maritime_df[["Date", "Annulation"]],
    on="Date",
    how="inner"
)
```

Option B) **Substitution de colonnes** :
```python
# Supposer que maritime_clean.csv couvre la période Open-Meteo
# Remplacer colonnes météo maritimes par colonnes Open-Meteo
```

→ **À décider avant étape 2c**

---

## 📊 Résultat attendu

Après 3 semaines environ (collecte + entraînement) :
- **2 modèles versionnés** comparables
- **Métriques side-by-side**
- **Décision documentée** pour migration

---

## 🚀 Commandes résumées

```bash
# Phase 1 : Baseline Maritime
cd maritime && python -m src.retrain --version v1 --data-source maritime

# Phase 2 : Préparer Open-Meteo
cd meteo_marine && python -m src.pipeline

# Phase 2b : Adapter preprocessing (manuel)
# Créer meteo_marine/src/train_openmeteo.py

# Phase 2c : Entraîner v2
cd maritime && python -m src.retrain --version v2_openmeteo --data-source openmeteo

# Phase 3 : Comparer
cd maritime && python -m src.retrain --compare <v1_path> <v2_path>
```

---

## 📝 Notes

- Script `maritime/src/retrain.py` gère versioning et comparaison
- Chaque version sauvegarde timestamp + metadata pour traçabilité
- Format de sauvegarde : `artifacts/models_<version>_<timestamp>/`
