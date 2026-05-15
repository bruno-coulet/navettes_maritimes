# 🚢 Module Predict : API & Interface Utilisateur

Ce module constitue la couche "Inférence" du projet. Il transforme le modèle entraîné en un outil opérationnel utilisable par les équipes sur le terrain pour anticiper les annulations de navettes.

## 📂 Structure du dossier

```text
predict/
├── api/
│   └── src/
│       ├── main.py          # Serveur FastAPI (Le cerveau)
│       ├── meteo.py         # Service de récupération Open-Meteo
│       └── model.pkl        # Modèle Random Forest entraîné
├── front/
│   ├── app.py              # Interface Streamlit (Le visage)
│   └── img/                # Assets visuels (lebateau.jpg)
└── README.md               # Ce fichier

```

## 🧠 L'API (FastAPI)

L'API est le point central qui reçoit les données météo et logistiques, les formate, et interroge le modèle.

### Fonctionnalités avancées :

* **Dictionnaire Zéro** : L'API initialise systématiquement les 136+ colonnes attendues par le modèle à `0.0`. Cela permet au Front de n'envoyer que les variables importantes (Vent, Houle) sans faire planter le calcul.
* **Gestion des orientations** : Convertit les sélecteurs de texte (NW, SE, etc.) en colonnes binaires (One-Hot Encoding) pour le modèle.
* **Route Tomorrow** (`/predict/tomorrow`) : Route spéciale qui agrège les données d'Open-Meteo pour générer un bulletin complet de toutes les lignes pour le lendemain en un seul appel.

### Lancement :

```bash
cd api/src
uvicorn main:app --reload --port 8000

```

## 🎨 Le Frontend (Streamlit)

Une interface moderne et intuitive conçue pour les tablettes et ordinateurs des agents de quai.

### Fonctionnalités :

* **Prédiction Manuelle** : Saisie des conditions observées pour obtenir une probabilité immédiate.
* **Bulletin Automatique** : Bouton permettant de charger les prévisions Open-Meteo et d'afficher un tableau récapitulatif ✅/⚠️ pour toutes les destinations.
* **Visualisation des Risques** : Utilisation de barres de progression et de codes couleurs pour une lecture rapide du danger.

### Lancement :

```bash
cd front
streamlit run app.py

```

## 🔄 Flux de données

1. **Utilisateur** : Saisit une condition ou clique sur "Bulletin Automatique".
2. **Front** : Envoie une requête JSON à l'API.
3. **API** :
* Complète les données manquantes (températures, ciels par défaut).
* Aligne les colonnes selon `metrics_v3.json`.
* Prédit la probabilité via `model.pkl`.


4. **Front** : Affiche le résultat (ex: "Départ probable à 94%").

## 🛠 Variables d'environnement

L'application utilise la variable `API_URL` pour savoir où joindre le backend. Par défaut : `http://localhost:8000/predict`.