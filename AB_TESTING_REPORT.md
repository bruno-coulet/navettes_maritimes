# 📊 Rapport A/B Testing CORRIGÉ : Maritime vs Open-Meteo

**Date** : 2026-05-13  
**Status** : ✅ ANNULATION DÉCOUVERTE ET RÉSOLUE

---

## 🔴 DÉCOUVERTE CRITIQUE

### Problème identifié dans v2 initial

En comparant les distributions d'annulation, nous avons découvert une **incohérence statistique** :

- **v1 Maritime** : 16.6% annulations (79,285 horaires)
- **v2 Open-Meteo initial** : 65.6% annulations (719 jours)

**Raison** : Erreur d'agrégation. J'utilisais `Annulation='max'` qui signifie :
```python
# ❌ INCORRECT
if aucune_annulation_ce_jour == False:  # >= 1 annulation
    journee = 'ANNULÉE'  # 100%
```

Avec ~80 traversées/jour, presque chaque jour a ≥1 annulation → **65% de jours "annulés"**

### Solution appliquée

Changement vers `Annulation='mean'` :
```python
# ✅ CORRECT
journee_pct_annulation = (nombre_annulations_ce_jour / nombre_total_traversees)
# Si 80 traversées, 13 annulées → 16.25% ce jour
```

---

## 📈 Résultats CORRIGÉS

### v1 - Maritime (Baseline)

**Source** : `consolidation_maritime.xlsx` → `maritime_clean.csv`

- Granularité : Horaire (79,285 observations)
- Période : 2023-2026
- Cible : Annulation binaire
- Distribution : 16.6% annulations

**Métriques** :
```
Accuracy  : 0.9405
Precision : 0.9300
Recall    : 0.6929
F1-Score  : 0.7942
```

### v2 - Open-Meteo ORIGINAL (❌ Biaisé)

Avec erreur d'agrégation `max()` :

- Distribution d'annulation : **65.6%** (incorrect)
- Métriques : F1=0.7912 (comparaison invalide)
- **❌ Résultats à ignorer** (distribution biaiseé)

### v2 - Open-Meteo CORRIGÉ (✅ Valide)

Avec agrégation corrigée `mean()` :

- **Granularité** : Quotidienne (719 jours agrégés)
- **Période** : 2024-2026 (intersection avec Open-Meteo)
- **Cible** : Annulation binaire (threshold 16.6%)
- **Distribution** : 18.5% annulations → **cohérente avec v1** ✓

**Métriques** :
```
Accuracy  : 0.8056
Precision : 0.7927
Recall    : 0.8553
F1-Score  : 0.8228  ✅ SUPÉRIEUR À v1
```

---

## 🏆 Comparaison FINALE

| Métrique | v1 Maritime | v2 Open-Meteo Corrigé | Δ | Gagnant |
|----------|-------------|----------------------|---|---------|
| Accuracy | 0.9405 | 0.8056 | -0.1349 | Maritime |
| Precision | 0.9300 | 0.7927 | -0.1373 | Maritime |
| **Recall** | 0.6929 | **0.8553** | **+0.1624** | **Open-Meteo** ⭐ |
| **F1-Score** | 0.7942 | **0.8228** | **+0.0286** | **Open-Meteo** ⭐ |

---

## 📊 Analyse détaillée

### Avantages Maritime v1
✅ **Accuracy très élevée** (94.1%) → modèle confiant globalement  
✅ **Precision élevée** (93%) → peu de faux positifs (évite d'annuler à tort)  
✅ **Plus de données** (79k vs 719)  
✅ **Granularité horaire** → capture patterns intra-jour  
✅ **136 features** → riche contexte (Ligne, Bateau, Capitaine)

### Avantages Open-Meteo v2 Corrigé
✅ **F1-Score supérieur** (0.8228 vs 0.7942) → meilleur équilibre  
✅ **Recall nettement meilleur** (85.5% vs 69.3%) → **détecte 85% des annulations**  
→ Important pour la sécurité : mieux détecter les risques  
✅ **Automatisé** → API sans maintenance manuelle Excel  
✅ **Features numériques pures** → 13 features significatives  
✅ **Perspective intéressante** : données météo objectives (vs historiques)

---

## 🎯 Interprétation

### Pourquoi Maritime a meilleure Accuracy ?
- 79k points d'entraînement vs 719
- Features métier très discriminantes (Ligne, Bateau, Capitaine)
- Patterns historiques bien appris

### Pourquoi Open-Meteo a meilleur F1 et Recall ?
- **Recall 85.5%** = détecte presque tous les jours à risque
- Maritime Recall 69.3% = manque 31% des annulations (risqué !)
- F1 corrige pour l'imbalance : penalize moins l'Accuracy basse si Recall excellent

**Interprétation** : Open-Meteo est **plus sensible au risque**, Maritime est **plus spécifique**.

---

## 💡 Recommandations

### Court terme (Immédiat)
**Option A** : **Rester sur v1 Maritime** pour production  
*Raison* : Accuracy très élevée, risque minimal de faux positifs

**Option B (RECOMMANDÉE)** : **Basculer vers v2 Open-Meteo**  
*Raison* : Recall 85.5% = détecte 85% des annulations réelles  
→ Plus sûr pour la sécurité des usagers (mieux vaut sur-prédire que sous-prédire)

### Moyen terme (2-4 semaines)
**Approche hybride** : Combiner les deux
```python
# Ensemble voting
if v1_pred == 1 OR v2_pred == 1:
    predict_ANNULATION = 1
else:
    predict_OK = 0
```
→ Combine Precision (v1) + Recall (v2)

### Long terme (3+ mois)
1. **Ajouter features Open-Meteo à v1 Maritime**
   - Garder Ligne, Bateau, Capitaine
   - Ajouter wave_height, temperature, wind
   - Réentraîner : combiner forces des deux

2. **Mettre en place monitoring**
   - Data drift detection (distribution annulation change ?)
   - Réentraînement mensuel automatisé

3. **Collecte continue**
   - Open-Meteo : automatisé ✓
   - Maritime : intégrer API pour éviter Excel

---

## 📌 Enseignements

1. **Agrégation statistique critique** : `max()` vs `mean()` change complètement les résultats
2. **Distribution importante** : 16.6% vs 65.6% invalide toute comparaison
3. **Recall vs Precision** : Tradeoff fondamental en classification
4. **Automatisation** : Open-Meteo + Maritime est combinaison puissante

---

## 📁 Fichiers générés

✅ `maritime/artifacts/features.json` → v1 Maritime (production actuelle)  
✅ `meteo_marine/artifacts/features_openmeteo_v2_corrected.json` → v2 Open-Meteo (corrigé)  
✅ `meteo_marine/data/processed/training_merged_corrected.parquet` → données fusionnées correctes  

---

## ✅ Conclusion

**L'erreur d'agrégation a été découverte et corrigée.**

Maintenant les deux modèles sont **comparables statistiquement**. Open-Meteo v2 montre un **F1-Score supérieur et un Recall meilleur**, ce qui la rend intéressante pour un basculement progressif, surtout combinée avec Maritime pour robustesse.

**Prochaine étape** : Décision sur v1 vs v2 (ou hybride) basée sur les risques métier.
