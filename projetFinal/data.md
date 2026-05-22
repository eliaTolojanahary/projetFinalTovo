# Weather Analytics Madagascar

## Description du projet

Plateforme de collecte, traitement et visualisation de données météorologiques pour Madagascar.

Le système récupère des données météo depuis plusieurs APIs comme [Open-Meteo](https://open-meteo.com/?utm_source=chatgpt.com), puis :

* nettoie les données,
* les stocke dans un Data Warehouse,
* génère des rapports météo,
* expose les résultats dans un dashboard.

Le pipeline ETL est automatisé avec Apache Airflow.

---

# Architecture globale

```text id="ec8a7l"
Open-Meteo API
        ↓
Python ETL
        ↓
Airflow Pipeline
        ↓
PostgreSQL Warehouse
        ↓
Weather Reports
        ↓
Dashboard / API
```

---

# Tables prévues

---

## 1. climate_types

### Description

Types de climat.

### Type

Statique

### Colonnes

| Colonne     | Type    | Clé |
| ----------- | ------- | --- |
| id          | INT     | PK  |
| nom_climat  | VARCHAR |     |
| description | TEXT    |     |

---

## 2. regions

### Description

Régions de Madagascar.

### Type

Statique

### Colonnes

| Colonne          | Type    | Clé |
| ---------------- | ------- | --- |
| id               | INT     | PK  |
| nom_region       | VARCHAR |     |
| chef_lieu        | VARCHAR |     |
| latitude         | DECIMAL |     |
| longitude        | DECIMAL |     |
| altitude_moyenne | DECIMAL |     |
| climate_type_id  | INT     | FK  |

### Relations

```text id="mjlwm0"
regions.climate_type_id
→ climate_types.id
```

---

## 4. timezones

### Description

Fuseaux horaires.

### Type

Statique

### Colonnes

| Colonne       | Type    | Clé |
| ------------- | ------- | --- |
| id            | INT     | PK  |
| timezone_name | VARCHAR |     |
| utc_offset    | VARCHAR |     |
| description   | TEXT    |     |

---

## 5. api_sources

### Description

Sources API utilisées.

### Type

Statique

### Colonnes

| Colonne     | Type    | Clé |
| ----------- | ------- | --- |
| id          | INT     | PK  |
| nom_source  | VARCHAR |     |
| base_url    | TEXT    |     |
| description | TEXT    |     |
| api_type    | VARCHAR |     |
| is_active   | BOOLEAN |     |

---

## 6. units

### Description

Unités des variables météo.

### Type

Statique

### Colonnes

| Colonne       | Type    | Clé |
| ------------- | ------- | --- |
| id            | INT     | PK  |
| nom_unite     | VARCHAR |     |
| symbole       | VARCHAR |     |
| type_variable | VARCHAR |     |

---

## 7. variables

### Description

Variables météo manipulées.

### Type

Statique

### Colonnes

| Colonne       | Type    | Clé |
| ------------- | ------- | --- |
| id            | INT     | PK  |
| code          | VARCHAR |     |
| nom_variable  | VARCHAR |     |
| unite_id      | INT     | FK  |
| type_variable | VARCHAR |     |
| description   | TEXT    |     |

### Relations

```text id="x7kl1p"
variables.unite_id
→ units.id
```

---

## 8. weather_locations

### Description

Points météo / stations météo.

### Type

Statique

### Colonnes

| Colonne     | Type    | Clé |
| ----------- | ------- | --- |
| id          | INT     | PK  |
| nom_station | VARCHAR |     |
| region_id   | INT     | FK  |
| district_id | INT     | FK  |
| latitude    | DECIMAL |     |
| longitude   | DECIMAL |     |
| altitude    | DECIMAL |     |
| timezone_id | INT     | FK  |

### Relations

```text id="kgbljr"
weather_locations.region_id
→ regions.id

weather_locations.district_id
→ districts.id

weather_locations.timezone_id
→ timezones.id
```

---

## 9. weather_raw

### Description

Données brutes venant des APIs.

### Type

API

### Colonnes

| Colonne       | Type      | Clé |
| ------------- | --------- | --- |
| id            | BIGINT    | PK  |
| location_id   | INT       | FK  |
| source_api_id | INT       | FK  |
| date_heure    | DATETIME  |     |
| raw_data      | JSON      |     |
| created_at    | TIMESTAMP |     |

### Relations

```text id="sux0oq"
weather_raw.location_id
→ weather_locations.id

weather_raw.source_api_id
→ api_sources.id
```

---

## 10. weather_clean

### Description

Données météo nettoyées.

### Type

API transformée

### Colonnes principales

| Colonne              | Type    |
| -------------------- | ------- |
| temperature_2m       | DECIMAL |
| relative_humidity_2m | DECIMAL |
| precipitation        | DECIMAL |
| rain                 | DECIMAL |
| wind_speed_10m       | DECIMAL |
| wind_direction_10m   | DECIMAL |
| surface_pressure     | DECIMAL |
| apparent_temperature | DECIMAL |
| uv_index             | DECIMAL |
| is_day               | BOOLEAN |

### Relations

```text id="fwq5l2"
weather_clean.raw_id
→ weather_raw.id

weather_clean.location_id
→ weather_locations.id
```

---

## 11. weather_hourly

### Description

Historique météo horaire.

### Type

API transformée

### Relations

```text id="7j74fr"
weather_hourly.location_id
→ weather_locations.id
```

---

## 12. weather_daily

### Description

Agrégations météo journalières.

### Type

API transformée

### Colonnes principales

| Colonne            |
| ------------------ |
| temperature_2m_max |
| temperature_2m_min |
| precipitation_sum  |
| rain_sum           |
| wind_speed_10m_max |
| uv_index_max       |

### Relations

```text id="8g8nzt"
weather_daily.location_id
→ weather_locations.id
```

---

## 13. weather_report

### Description

Rapports météo générés automatiquement.

### Type

Analytique

### Colonnes principales

| Colonne           |
| ----------------- |
| summary_text      |
| temperature_avg   |
| temperature_min   |
| temperature_max   |
| precipitation_sum |
| humidity_avg      |
| wind_speed_avg    |

### Relations

```text id="k3wpry"
weather_report.location_id
→ weather_locations.id
```

---

## 14. data_quality

### Description

Contrôle qualité des données.

### Type

Technique

### Relations

```text id="6nns7q"
data_quality.raw_id
→ weather_raw.id
```

---

## 15. alerts

### Description

Alertes météo simples.

### Type

Analytique

### Relations

```text id="v6j7ga"
alerts.location_id
→ weather_locations.id
```

---

# Données récupérées depuis Open-Meteo

## Current (temps réel)

```text id="31yx2p"
temperature_2m
relative_humidity_2m
wind_speed_10m
wind_direction_10m
surface_pressure
apparent_temperature
precipitation
rain
showers
uv_index
is_day
```

---

## Hourly (horaire)

```text id="5s71yw"
temperature_2m
relative_humidity_2m
precipitation
rain
wind_speed_10m
wind_direction_10m
surface_pressure
uv_index
apparent_temperature
```

---

## Daily (journalier)

```text id="hvsp6k"
temperature_2m_max
temperature_2m_min
precipitation_sum
rain_sum
wind_speed_10m_max
wind_gusts_10m_max
sunshine_duration
uv_index_max
```

---

## Métadonnées

```text id="rwn7mc"
latitude
longitude
timezone
elevation
```

---

# Données statiques à préparer

| Fichier                 | Description            |
| ----------------------- | ---------------------- |
| regions_madagascar.csv  | Régions                |
| districts.csv           | Districts              |
| weather_locations.csv   | Points météo           |
| climate_types.txt       | Types de climat        |
| api_sources.json        | APIs utilisées         |
| units.json              | Unités météo           |
| variables.json          | Variables météo        |
| timezones.csv           | Fuseaux horaires       |
| weather_thresholds.json | Seuils météo           |
| alerts_types.json       | Types alertes          |
| schema.sql              | Script SQL             |
| config.yaml             | Configuration pipeline |

---

# MVP (Minimum Viable Product)

## Objectif MVP

Version minimale capable de :

* récupérer météo temps réel,
* stocker les données,
* générer un simple rapport météo,
* afficher les informations dans un dashboard.

---

# Tables MVP

```text id="cq0b1i"
regions
weather_locations
weather_raw
weather_clean
weather_daily
weather_report
api_sources
```

---

# Variables API MVP

```text id="o44m6u"
temperature_2m
relative_humidity_2m
precipitation
wind_speed_10m
surface_pressure
```

---

# Fichiers statiques MVP

```text id="zt10i4"
regions_madagascar.csv
weather_locations.csv
api_sources.json
schema.sql
config.yaml
```

---

# Relations principales

```text id="34xghg"
regions
    ↓
districts
    ↓
weather_locations
    ↓
weather_raw
    ↓
weather_clean
    ↓
weather_daily
    ↓
weather_report
```

---

# Pipeline ETL prévu

```text id="5aajv9"
Open-Meteo API
    ↓
Extraction Python
    ↓
Airflow DAG
    ↓
weather_raw
    ↓
Nettoyage
    ↓
weather_clean
    ↓
Agrégations
    ↓
weather_daily
    ↓
Rapports météo
    ↓
Dashboard
```
