

# 🚢 Navettes Maritimes - Système de Prédiction V3

Ce projet est une solution complète d'aide à la décision pour l'exploitation des navettes maritimes à Marseille (Vieux-Port, Frioul, If, Estaque). Il utilise un modèle de Machine Learning Hybride pour prédire les risques d'annulation en fonction des conditions météo réelles et prévisionnelles.

## 📌 Architecture du Projet

Le projet est structuré en modules indépendants pour la collecte, l'entraînement et la prédiction :

- **`open_meteo/`** : Micro-service de collecte automatique des données météo (Marine & Horaires) via l'API Open-Meteo.
- **`maritime/`** : Pipeline d'entraînement du modèle (Random Forest) avec gestion des métadonnées (`metrics_v3.json`).
- **`predict/api/`** (anciennement `navettes/`) : API FastAPI exposant les routes de prédiction temps réel et les bulletins automatiques.
- **`predict/front/`** : Interface utilisateur Streamlit avec visualisation des risques, gestion de l'orientation du vent et chargement météo automatique.

## 🛠 Fonctionnalités Clés

### 1. Prédiction Intelligente
- **Prise en compte de l'orientation** : Analyse croisée de la direction du vent (Rose des vents) et de la houle.
- **Modèle Hybride** : Intègre les paramètres physiques (vagues, vent) et logistiques (spécificités des bateaux, habitudes des capitaines).
- **Dictionnaire Zéro** : L'API gère automatiquement les données manquantes (températures, ciels) pour garantir une prédiction stable même avec des formulaires simplifiés.

### 2. Bulletin Automatique pour le Lendemain
- Intégration directe avec **Open-Meteo** pour récupérer les prévisions à 24h (vagues, vent, rafales).
- Génération d'un tableau de bord complet simulant toutes les lignes de desserte en un seul clic.

### 3. Interface d'Exploitation (Streamlit)
- Visualisation claire du risque (Code couleur ✅/⚠️).
- Chargement automatique des prévisions météo.
- Support des images d'exploitation et détails techniques extensibles pour les administrateurs.

## 🚀 Installation et Lancement

### Prérequis
- Python 3.12+
- `uv` ou `pip`
- Docker & Docker Compose (pour l'orchestration)

### Lancement avec Docker
```bash
docker-compose -f docker-compose.orchestration.yml up --build

```

### Lancement en mode développement (Local)

1. **Lancer l'API :**

```bash
cd predict/api/src
uvicorn main:app --reload

```

2. **Lancer le Frontend :**

```bash
cd predict/front
streamlit run app.py

```

## 📊 Structure des Métadonnées (`metrics_v3.json`)

Le fichier de métadonnées est crucial pour l'alignement entre le modèle et l'API. Il contient :

* La liste ordonnée des **136+ features** (colonnes).
* Les scores de performance du modèle (Accuracy ~94%).
* Les noms des colonnes encodées (One-Hot) pour les capitaines, bateaux et orientations de vent.

## 🤝 Contact

**Bruno Coulet** - [bruno.coulet@laplateforme.io](mailto:bruno.coulet@laplateforme.io)
Projet développé dans le cadre du cursus IA à La Plateforme_.