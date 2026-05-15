# ⚓ Rapport de Performance Final - Navettes Maritimes

Ce rapport compare les itérations successives du modèle de prédiction.

| Métrique | V1 (Maritime Pur) | V2 (Météo Seule) | V3 (Hybride) |
| :--- |  :---: | :---: | :---: |
| **accuracy** | 0.9398 | 0.8056 | 0.9782 |
| **precision** | 0.9147 | 0.7927 | 0.9544 |
| **recall** | 0.7021 | 0.8553 | 0.9119 |
| **f1** | 0.7944 | 0.8228 | 0.9327 |
| **Features** | 136 | 13 | 146 |

## 💡 Analyse
- **V1** : Modèle historique, solide mais manque de sensibilité sur les annulations.
- **V2** : Preuve que la météo Open-Meteo est un puissant moteur de prédiction.
- **V3** : Meilleur compromis. L'ajout des données métiers (bateaux/capitaines) stabilise la précision.
