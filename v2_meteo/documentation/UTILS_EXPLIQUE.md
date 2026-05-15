# Documentation utils.py

## 📊 Architecture

### Sources de données:

#### 1. open_meteo Marine API ✅ UTILISÉ
```
URL: https://marine-api.open_meteo.com/v1/marine
Fonction: get_marine_weather_open_meteo()
Données:
  - Hauteur max des vagues (m)
  - Direction des vagues (°)
  - Période des vagues (s)
  - Houle (swell) vs vagues de vent
Avantages: Gratuit, pas d'authentification
```

#### 2. open_meteo ERA5 Archive ✅ UTILISÉ
```
URL: https://archive-api.open_meteo.com/v1/era5
Fonction: get_weather_data_open_meteo()
Données:
  - Température (min/max) (°C)
  - Vitesse vent max (km/h)
  - Rafales max (km/h)
  - Direction vent dominant (°)
  - Pression, humidité, nuages
Avantages: Gratuit, pas d'authentification, réanalyse fiable
```

#### 3. Météo-France API ❌ NON UTILISÉ
```
URL: https://portail-api.meteofrance.fr
Fonctions: get_meteofrance_bulletins_bms(), scrape_meteofrance_bms_web()
Status: Code legacy conservé pour référence
Raison: Payant, authentification requise, endpoints instables
```

---

## 🔄 Flux de données

```
collect.py
  │
  ├─ collect_historical_data_batch(start, end)
  │   │
  │   ├─ get_marine_weather_open_meteo() ──► open_meteo Marine API
  │   │   └─ Vagues + houle
  │   │
  │   └─ get_weather_data_open_meteo() ──► open_meteo ERA5 API
  │       └─ Météo générale
  │
  ├─ process_to_daily_summary(batch_data)
  │   └─ Fusionne marine_data + weather_data par date
  │       └─ DataFrame quotidien prêt
  │
  └─ save_data(daily_df, start, end, save_json)
      └─ Exporte en CSV (optionnellement JSON)
```

---

## 📦 Fonctions par API

### open_meteo Marine (Vagues)

| Fonction | Utilisé | Données |
|----------|---------|---------|
| `get_marine_weather_open_meteo()` | ✅ OUI | Vagues, houle, période |

**Appelée par:** `collect_historical_data_batch()`

---

### open_meteo ERA5 (Météo générale)

| Fonction | Utilisé | Données |
|----------|---------|---------|
| `get_weather_data_open_meteo()` | ✅ OUI | Temp, vent, pression, humidité |

**Appelée par:** `collect_historical_data_batch()`

---

### Méteo-France (Legacy - Inactif)

| Fonction | Utilisé | Raison |
|----------|---------|--------|
| `get_meteofrance_bulletins_bms()` | ❌ NON | Endpoints instables, payant |
| `scrape_meteofrance_bms_web()` | ❌ NON | Scraping fragile |

**Appelée par:** Aucune (code legacy)

---

## 🏗️ Organisation des fonctions

### Groupe 1: open_meteo Marine
```python
def get_marine_weather_open_meteo(self, start_date, end_date):
    """[open_meteo MARINE] Récupère les données de vagues"""
    # Appelle: https://marine-api.open_meteo.com/v1/marine
```

### Groupe 2: open_meteo ERA5
```python
def get_weather_data_open_meteo(self, start_date, end_date):
    """[open_meteo ERA5] Récupère les données météo générale"""
    # Appelle: https://archive-api.open_meteo.com/v1/era5
```

### Groupe 3: Orchestration
```python
def collect_historical_data_batch(self, start_date, end_date, batch_days=30):
    """Orchestration: appelle les 2 APIs open_meteo"""
    # Appelle: get_marine_weather_open_meteo()
    # Appelle: get_weather_data_open_meteo()

def process_to_daily_summary(self, batch_data_list):
    """Fusion: combine données marines + météo"""
    # Utilise: batch_data contenant marine_data + weather_data

def save_data(self, data, start_date, end_date, save_json=False):
    """Sortie: exporte en CSV/JSON"""
    # Écrit: data/raw/YYYY/meteo_YYYY_MM_DD-au-MM_DD.csv
```

---

## 💡 Points clés

✅ **Utilisation d'APIs fiables**
- open_meteo: API stable, gratuit, documenté
- Données ERA5: Réanalyse scientifique, précise

✅ **Code organisé par API**
- Chaque API a sa section avec commentaires
- Facile d'ajouter une nouvelle API
- Facile de désactiver une API

✅ **Pas de dépendance Météo-France**
- Le projet fonctionne 100% sans API Météo-France
- Code legacy conservé pour futur mais inactif

---

## 🔧 Amélioration future

Si vous voulez activer Météo-France un jour:
1. S'inscrire et obtenir clé API (payant)
2. Décommenter les fonctions `get_meteofrance_bulletins_bms()`
3. Appeler dans `collect_historical_data_batch()`:
   ```python
   meteofrance_data = self.get_meteofrance_bulletins_bms(current_date)
   ```
4. Fusionner dans `process_to_daily_summary()`

Mais **ce n'est pas nécessaire** - open_meteo suffit!
