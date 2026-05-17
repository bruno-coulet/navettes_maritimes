# 🚢 Navettes Maritimes - Système d'Aide à la Décision (V3 Hybride)

Ce projet est une solution complète d'aide à la décision pour l'exploitation des navettes maritimes à Marseille (liaisons Vieux-Port, Frioul, If, Estaque). Basé sur un historique d'exploitation réel croisé avec des données environnementales, il implémente un modèle de Machine Learning permettant de prédire le risque d'annulation des traversées.

Le projet retrace une démarche d'ingénierie rigoureuse passant d'une approche Baseline simple à un modèle hybride industrialisé et résilient.

---

## Guide de Reproduction (Pipeline de A à Z)

Pour réentraîner les modèles et relancer l'intégralité de la chaîne de traitement depuis la racine du projet, exécutez les commandes suivantes dans l'ordre chronologique :

### 1. Étape V1 : Entraînement de la Baseline historique
Génère le premier modèle de référence et isole ses métriques dans son module.
```bash
uv run python -m v1_baseline.src.train_v1
```
2. Étape V2 : Collecte et mise à jour de l'historique Météo
Interroge les API Open-Meteo (Marine et Archive) pour reconstituer les fichiers CSV mensuels de référence.

```Bash
uv run python v2_meteo/src/collect_meteo.py
```
3. Étape V3 : Réentraînement du Modèle Hybride Final
Fusionne les registres maritimes et les données météo de la V2 pour entraîner le Random Forest final à 146 features.

```Bash
uv run python -m v3_hybride.src.train_v3
````

4. Déploiement des artefacts vers la Production.  
Avant de lancer l'application, copiez le modèle et ses métadonnées fraîchement générés dans la couche d'inférence :

```Bash
cp v3_hybride/artifacts/model.pkl predict/api/src/
cp v3_hybride/artifacts/metrics_v3.json predict/api/src/
````

---

## Architecture du Projet

Le projet est découpé en quatre modules majeurs représentant les grandes étapes du cycle de vie de la donnée :

```text
├── v1_baseline/             # Approche initiale basée sur les règles métiers simples
│   └── artifacts/           # Modèle V1 et métriques associées (Baseline)
│
├── v2_meteo/                # Module d'acquisition et historique de données météo
│   ├── src/
│   │   └── collect.py       # Script d'extraction des données Open-Meteo (Historique)
│   └── data/                # CSV mensuels météo archivés (Août 2025 - Avril 2026)
│
├── v3_hybride/              # Pipeline d'entraînement du modèle final
│   ├── data/                # Datasets fusionnés et préparés
│   └── artifacts/           # Métadonnées d'alignement (metrics_v3.json) & modèle final
│
└── predict/                 # Couche d'inférence industrialisée (Déploiement)
    ├── api/src/             # Backend FastAPI (main.py, service météo temps réel)
    └── front/               # Interface utilisateur Streamlit d'exploitation

```

---

## Modules

### 1. `v1_baseline`

Première itération du modèle de prédiction. Elle a servi à établir un score de référence (Baseline) à battre en utilisant des features d'exploitation basiques.

### 2. `v2_meteo` (Acquisition Historique)

Ce module gère le stockage et l'acquisition des données environnementales passées. Le script `src/collect.py` (à vocation de script de collecte historique) a permis de constituer un référentiel complet de données marines (vagues) et horaires (vent, rafales) archivé mois par mois sous forme de fichiers CSV.

### 3. `v3_hybride` (Entraînement Avancé)

C'est le cœur de l'intelligence du projet. Il fusionne les données d'exploitation maritimes et l'historique météo récolté. Le modèle entraîné (Random Forest) réalise une analyse croisée complexe : variables physiques (hauteur/période des vagues, force/rafales du vent) et contraintes logistiques (spécificités de comportement des navires, habitudes des capitaines et particularités des lignes).

### 4. `predict` (Inférence & Application Opérationnelle)

Le module prêt pour la production. Il s'affranchit des scripts lourds d'entraînement pour ne proposer que l'usage pratique :

* **API Backend (FastAPI)** : Charge le modèle final, intègre un mécanisme de **Dictionnaire Zéro** pour immuniser le système contre les champs manquants, gère l'encodage One-Hot des roses des vents et intègre un client Open-Meteo temps réel.
* **Frontend UI (Streamlit)** : Interface graphique épurée affichant un simulateur de traversée en temps réel et un générateur de bulletin automatique pour le lendemain à destination des agents de quai.

---

## Lancement Rapide (Mode Développement)

Le projet intègre un gestionnaire d'environnement moderne basé sur `uv` ou `pip`.

### 1. Démarrer l'API de Prédiction

```bash
cd predict/api/src
uv run uvicorn main:app --reload --port 8000

```

*L'interface Swagger interactive est alors documentée et accessible sur `http://localhost:8000/docs`.*

### 2. Démarrer l'Interface d'Exploitation

```bash
cd predict/front
uv run streamlit run app.py

```

---

## Alignement des Métadonnées & Industrialisation

Le fichier contractuel `metrics_v3.json` (généré par la V3 et exploité par l'API) garantit la cohérence mathématique du système. Il liste de manière stricte l'ordre et le nom des **136+ features** (incluant le One-Hot encoding des capitaines, navires, et orientations du vent comme `Vent_NW`, `Vent_ENE`). L'API s'appuie dessus pour reconstruire à la volée le DataFrame exact attendu par Scikit-Learn.

---

**Développé par Bruno Coulet** — [bruno.coulet@laplateforme.io](mailto:bruno.coulet@laplateforme.io)
