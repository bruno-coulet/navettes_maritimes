"""
Comparaison finale v1 vs v2_original (biaisé) vs v2_corrected
"""

import json
from pathlib import Path

print("="*80)
print("COMPARAISON FINALE : v1 Maritime vs v2 Open-Meteo (original ET corrigé)")
print("="*80)

# Charger les 3 versions
v1_path = Path("maritime/artifacts/features.json")
v2_orig_path = Path("meteo_marine/artifacts/features_openmeteo.json")
v2_corr_path = Path("meteo_marine/artifacts/features_openmeteo_v2_corrected.json")

with open(v1_path) as f:
    v1 = json.load(f)
with open(v2_orig_path) as f:
    v2_orig = json.load(f)
with open(v2_corr_path) as f:
    v2_corr = json.load(f)

m1 = v1["metrics"]
m2o = v2_orig["metrics"]
m2c = v2_corr["metrics"]

print("\n" + "="*80)
print("MÉTRIQUES")
print("="*80)

print(f"\n{'Métrique':<15} {'v1 Maritime':<20} {'v2 Original (❌)':<20} {'v2 Corrigé (✅)':<20}")
print("-" * 80)

for key in ["accuracy", "precision", "recall", "f1"]:
    v1_val = m1.get(key, 0)
    v2o_val = m2o.get(key, 0)
    v2c_val = m2c.get(key, 0)
    print(f"{key:<15} {v1_val:<20.4f} {v2o_val:<20.4f} {v2c_val:<20.4f}")

print("\n" + "="*80)
print("DONNÉES & FEATURES")
print("="*80)

print(f"\n{'Aspect':<25} {'v1 Maritime':<25} {'v2 Original':<25} {'v2 Corrigé':<25}")
print("-" * 80)
print(f"{'Samples':<25} {'79,285 (horaires)':<25} {'719 jours':<25} {'719 jours':<25}")
print(f"{'Distribution Annulation':<25} {'16.6%':<25} {'65.6% (BIAISÉE)':<25} {'18.5% ✅':<25}")
print(f"{'Features':<25} {'136':<25} {'13':<25} {'13':<25}")
print(f"{'Agrégation':<25} {'N/A (horaire)':<25} {'max() ❌':<25} {'mean() ✅':<25}")

print("\n" + "="*80)
print("RÉSULTAT DU TEST")
print("="*80)

print(f"""
v1 Maritime :
  ✓ Accuracy : {m1['accuracy']:.4f}
  ✓ F1-Score : {m1['f1']:.4f}
  ✓ Données : 79,285 horaires (3 ans)
  ✓ Status : Production actuelle
  ⚠ Issue : Recall bas (69%), détecte 2/3 des annulations

v2 Open-Meteo ORIGINAL (INVALIDE) :
  ❌ Distribution : 65.6% (ERREUR AGRÉGATION)
  ❌ Annulation='max' → exagère les annulations
  ❌ Comparaison invalide avec v1
  ⚠ Résultats à ignorer

v2 Open-Meteo CORRIGÉ (VALIDE) :
  ✓ F1-Score : {m2c['f1']:.4f} (+{m2c['f1']-m1['f1']:.4f} vs v1)
  ✓ Recall : {m2c['recall']:.4f} (+{m2c['recall']-m1['recall']:.4f} vs v1)
  ✓ Distribution : 18.5% (cohérente avec v1)
  ✓ Annulation='mean' → distribution réelle
  ✓ Comparaison valide
  ✅ RECOMMANDÉ : Considérer pour basculement (meilleur Recall)
""")

print("="*80)
print("CONCLUSION")
print("="*80)

print(f"""
1. ERREUR DÉCOUVERTE ✅
   L'écart 16.6% → 65.6% venait d'une erreur d'agrégation (max vs mean)
   
2. CORRECTION APPLIQUÉE ✅
   Fichiers régénérés avec agrégation correcte (mean)
   
3. COMPARAISON MAINTENANT VALIDE ✅
   v2 Corrigé F1=0.8228 > v1 F1=0.7942
   v2 Corrigé Recall=0.8553 > v1 Recall=0.6929
   
4. RECOMMANDATION
   v2 Open-Meteo meilleur pour RECALL (détecte 85% des annulations)
   v1 Maritime meilleur pour PRECISION (peu de faux positifs)
   → Hybride (voting) recommandé pour robustesse maximale

5. PROCHAINES ÉTAPES
   [ ] Choisir : v1, v2, ou hybrid
   [ ] Déployer en staging
   [ ] Monitorer en production
   [ ] Réentraîner mensuellement
""")

print("="*80)
