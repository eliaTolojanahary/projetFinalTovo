Oui. Pour TON projet orienté agriculture et élevage, il faut récupérer bien plus que juste :

```text id="d4zh3z"
température + pluie
```

Tu dois récupérer des données capables de produire :

* analyses agricoles,
* indicateurs climatiques,
* alertes,
* tendances,
* scores de risque.

Open-Meteo fournit déjà énormément de données utiles. ([Open Meteo][1])

---

# 1. Informations météo PRINCIPALES à récupérer

## Température

Très importante pour :

* cultures,
* élevage,
* sécheresse,
* stress thermique.

Variables :

```text id="7bw7hn"
temperature_2m
temperature_2m_max
temperature_2m_min
apparent_temperature
```

---

## Humidité

Utile pour :

* maladies agricoles,
* confort animal,
* irrigation.

Variables :

```text id="lnx37w"
relative_humidity_2m
dew_point_2m
```

---

## Précipitations

Très importantes pour l’agriculture.

Variables :

```text id="sz95a6"
precipitation
precipitation_sum
rain
rain_sum
showers
showers_sum
precipitation_probability
precipitation_hours
```

([Open Meteo][2])

---

## Vent

Important pour :

* cultures fragiles,
* dispersion maladies,
* évaporation.

Variables :

```text id="uyjlwm"
wind_speed_10m
wind_direction_10m
wind_gusts_10m
```

---

## Pression atmosphérique

Peut aider à détecter :

* changements météo,
* tempêtes.

Variables :

```text id="5el3pj"
surface_pressure
pressure_msl
```

---

## Rayonnement solaire

Très utile pour :

* croissance plantes,
* évaporation,
* sécheresse.

Variables :

```text id="g4n2th"
shortwave_radiation
direct_radiation
diffuse_radiation
sunshine_duration
```

---

## UV

Important pour :

* stress des plantes,
* élevage.

Variables :

```text id="n7gq0m"
uv_index
uv_index_clear_sky
```

---

# 2. Informations TEMPORELLES

Tu dois récupérer :

## Données actuelles

```text id="6wb2d6"
current
```

Pour :

* temps réel,
* dashboard live.

---

## Données horaires

```text id="rr7cyd"
hourly
```

Pour :

* évolution journée,
* graphiques,
* analyses fines.

---

## Données journalières

```text id="4j7j55"
daily
```

Pour :

* statistiques agricoles,
* tendances,
* rapports.

([Open Meteo][2])

---

# 3. Informations géographiques

Tu dois stocker :

| Donnée    | Utilité             |
| --------- | ------------------- |
| latitude  | géolocalisation     |
| longitude | carte               |
| région    | analyses régionales |
| altitude  | influence météo     |

---

# 4. Informations AGRICOLES dérivées (calculées par toi)

Ça sera la vraie valeur du projet.

Tu peux calculer :

---

## Indice sécheresse

Basé sur :

* pluie,
* chaleur,
* humidité.

---

## Risque maladie cultures

Basé sur :

* humidité élevée,
* chaleur,
* pluie.

---

## Stress thermique animal

Basé sur :

* température,
* humidité.

---

## Conditions irrigation

Basé sur :

* évaporation,
* pluie,
* température.

---

## Score agriculture

Exemple :

```text id="16t8gp"
0 → mauvaises conditions
100 → excellentes conditions
```

---

# 5. Historique météo

Très important.

Open-Meteo fournit aussi des données historiques. ([Open Meteo][1])

Tu pourras :

* comparer semaines,
* comparer saisons,
* détecter anomalies,
* faire tendances.

---

# 6. Régions de Madagascar à stocker

Tu peux créer une table :

```text id="hgt5xk"
regions_madagascar
```

avec :

| id | region | latitude | longitude |

Exemples :

* Analamanga
* Atsinanana
* Boeny
* Androy
* Diana
* Haute Matsiatra

---

# 7. Ce que je te conseille VRAIMENT de récupérer au début

Commence SIMPLE.

## MVP (Minimum Viable Product)

Récupère seulement :

```text id="uyx9bz"
temperature_2m
relative_humidity_2m
precipitation
wind_speed_10m
surface_pressure
```

---

Puis ajoute progressivement :

* UV,
* radiation,
* historiques,
* prédictions.

---

# 8. Structure idéale du Data Warehouse

## Table brute

```text id="6k6j8n"
weather_raw
```

---

## Table météo propre

```text id="cc0h3l"
weather_clean
```

---

## Table agriculture analytics

```text id="4ukm22"
agriculture_indicators
```

---

## Table élevage analytics

```text id="mjlwm5"
livestock_indicators
```

---

# 9. Très important : ne SCRAPE pas le site

Tu dois utiliser :

## l’API officielle Open-Meteo

[Open-Meteo API Documentation](https://open-meteo.com/en/docs?utm_source=chatgpt.com)

Parce que :

* plus stable,
* JSON propre,
* plus rapide,
* légal,
* parfait pour ETL.

---

# 10. Exemple de requête Open-Meteo

```bash id="6c7vma"
https://api.open-meteo.com/v1/forecast?
latitude=-18.8792&
longitude=47.5079&
current=temperature_2m,relative_humidity_2m,wind_speed_10m&
hourly=temperature_2m,precipitation,relative_humidity_2m&
daily=temperature_2m_max,temperature_2m_min,precipitation_sum&
timezone=auto
```

([Open Meteo][1])

[1]: https://open-meteo.com/?utm_source=chatgpt.com "🌤️ Free Open-Source Weather API | Open-Meteo.com"
[2]: https://open-meteo.com/en/docs?utm_source=chatgpt.com "🌦️ Docs | Open-Meteo.com"
