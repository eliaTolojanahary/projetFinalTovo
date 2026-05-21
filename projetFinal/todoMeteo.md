# TODO — Weather Analytics Madagascar

> Projet : Plateforme météo Madagascar (collecte → stockage → rapport → dashboard)
> Équipe : **Elia** (ETL & Airflow) · **Jemima** (Django & Affichage)

---

## Fichiers statiques à préparer (données fixes Madagascar)

Ces fichiers sont créés une seule fois et chargés en base au démarrage.

| Fichier | Format | Contenu |
|---|---|---|
| `regions_madagascar.csv & weather_locations.csv` | CSV | id, nom_region, chef_lieu, latitude, longitude, altitude_moyenne, climate_type_id | id_timezone (en dure)
| `climate_types.txt` | TXT | Liste des types de climat (Tropical humide, Semi-aride, Tempéré…) |
| `timezones.csv` : en dur
| `api_sources.json` | JSON | id, nom_source, base_url, api_type, is_active (ex: Open-Meteo) |
| `units.json & variables.json` | JSON | id, nom_unite, symbole, type_variable (ex: °C, %, mm, km/h…) &  id, code, nom_variable, unite_id, description (ex: temperature_2m, precipitation…) |
| `` | JSON 
| `alerts_types.json` (en dur) Types d'alertes météo (chaleur, pluie intense, vent fort…) |
===> fichier a generer postgreSQL| `schema.sql` | SQL | Script de création complète de la base de données |
| `config.yaml` | YAML | Configuration du pipeline (URLs API, intervalles, paramètres DAG) |

> **Données dynamiques** : tout le reste est récupéré depuis `api.open-meteo.com` (current, hourly, daily).

---

## Elia — ETL & Airflow

### Phase 1 — Mise en place de l'environnement

- [ ] Créer le dépôt Git et la structure du projet
- [ ] Configurer l'environnement Python (virtualenv / requirements.txt)
- [ ] Installer et configurer Apache Airflow (local)
- [ ] Installer PostgreSQL et créer la base `weather_madagascar`
- [ ] Rédiger `schema.sql` — création de toutes les tables MVP
- [ ] Rédiger `config.yaml` — paramètres du pipeline

### Phase 2 — Données statiques

- [ ] Préparer `regions_madagascar.csv`  (22 régions de Madagascar) & `weather_locations.csv`  pas de district (stations météo / points clés) =>  1 region = 1 station
- [ ] Préparer `climate_types.txt`
- [ ] Préparer `timezones (en dur)`
- [ ] Préparer `api_sources.json` (Open-Meteo)
- [ ] Préparer `units.json` & `variables.json` : meme fichier 
- [ ] Préparer `weather_thresholds (en dur)`
- [ ] Préparer `alerts_types (en dur)`
- [ ] Écrire le script de seed : chargement de tous les fichiers statiques en base

### Phase 3 — Extraction (Open-Meteo)

- [ ] Écrire le module `extractor.py`
  - [ ] Appel API `current` : temperature_2m, relative_humidity_2m, precipitation, wind_speed_10m, surface_pressure
  - [ ] Appel API `hourly` : même variables
  - [ ] Appel API `daily` : temperature_2m_max/min, precipitation_sum, wind_speed_10m_max, uv_index_max
  - [ ] Récupérer les métadonnées (latitude, longitude, timezone, elevation)
  - [ ] Stocker la réponse brute JSON dans `weather_raw`

### Phase 4 — Transformation & Nettoyage

- [ ] Écrire le module `transformer.py`
  - [ ] Parser le JSON brut depuis `weather_raw`
  - [ ] Valider et nettoyer les valeurs (nulls, unités, types)
  - [ ] Insérer dans `weather_clean`
  - [ ] Calculer les agrégations journalières → `weather_daily`

### Phase 5 — Génération des rapports

- [ ] Écrire le module `reporter.py`
  - [ ] Générer un rapport météo synthétique par location et par jour
  - [ ] Remplir la table `weather_report` (summary_text, temp avg/min/max, precipitation_sum, humidity_avg, wind_speed_avg)
  - [ ] Implémenter la logique d'alertes simples → `alerts` (array)

### Phase 6 — Contrôle qualité

- [ ] Écrire le module `quality.py`
  - [ ] Vérifier les valeurs hors plage (température, humidité, etc.)
  - [ ] Logger les anomalies dans `data_quality`

### Phase 7 — Airflow DAG

- [ ] Créer le DAG principal `weather_etl_dag.py`
  - [ ] Tâche : extraction current (toutes les heures)
  - [ ] Tâche : extraction hourly / daily (une fois par jour)
  - [ ] Tâche : transformation & nettoyage
  - [ ] Tâche : agrégations journalières
  - [ ] Tâche : génération rapports
  - [ ] Tâche : contrôle qualité
  - [ ] Gérer les dépendances entre tâches
  - [ ] Configurer les retries et alertes d'échec


## Jemima — Django & Affichage

### Phase 1 — Mise en place du projet Django

- [ ] Créer le projet Django `weather_dashboard`
- [ ] Configurer la connexion à la base PostgreSQL partagée
- [ ] Définir les modèles Django (refléter les tables : `regions`, `weather_locations`, `weather_clean`, `weather_daily`, `weather_report`, `alerts`)
- [ ] Configurer les settings (DEBUG, ALLOWED_HOSTS, static files)

### Phase 2 — API / Vues de données

- [ ] Créer les vues (ou viewsets DRF) pour exposer :
  - [ ] Liste des régions et stations
  - [ ] Données météo current par location
  - [ ] Historique hourly par location
  - [ ] Données daily (7 derniers jours)
  - [ ] Rapport météo du jour
  - [ ] Alertes actives

### Phase 3 — Dashboard principal

- [ ] Page d'accueil : carte de Madagascar avec les stations météo
- [ ] Sélecteur de région / station
- [ ] Bloc **météo actuelle** : température, humidité, précipitations, vent, pression
- [ ] Bloc **rapport du jour** : texte de synthèse + indicateurs clés
- [ ] Bloc **alertes** : alertes météo actives avec niveau de sévérité

### Phase 4 — Pages de visualisation

- [ ] Page **historique** : graphiques horaires sur 24h (température, pluie, humidité)
- [ ] Page **tendances** : graphiques journaliers sur 7 jours
- [ ] Composant graphiques (Chart.js ou Plotly) :
  - [ ] Courbe de température (min / moy / max)
  - [ ] Barres de précipitations
  - [ ] Courbe d'humidité
  - [ ] Jauge de vent

### Phase 5 — Pages de rapports

- [ ] Page **rapports météo** : liste des rapports générés par date et par région
- [ ] Vue détail d'un rapport : tous les indicateurs + résumé textuel
- [ ] Export PDF du rapport (optionnel)

### Phase 6 — Rafraîchissement des données

- [ ] Mettre en place un polling automatique (AJAX / HTMX) pour la météo actuelle
- [ ] Afficher la date/heure de dernière mise à jour
- [ ] Indicateur de statut du pipeline (dernière exécution Airflow)

### Phase 7 — UI / UX

- [ ] Responsive design (mobile-friendly)
- [ ] Thème sobre et lisible (Tailwind CSS ou Bootstrap)
- [ ] Gestion des états : chargement, erreur API, données manquantes
- [ ] Messages d'alerte visuels (couleur selon sévérité)



## Coordination Elia ↔ Jemima

- [ ] Définir ensemble le schéma SQL final avant de commencer (`schema.sql`)
- [ ] Aligner les noms de tables et colonnes entre les modèles Django et le schéma ETL
- [ ] Tester l'intégration : Elia alimente la base → Jemima affiche les données
- [ ] Mettre en place un fichier `.env` commun (DB host, port, credentials)
- [ ] Code review croisé avant livraison finale

---

## Ordre recommandé

```
Elia                              Jemima
──────────────────────          ──────────────────────
1. schema.sql ──────────────→  1. Modèles Django (basés sur schema.sql)
2. seed statiques              2. Vues + API endpoints
3. extractor.py                3. Page accueil + météo actuelle
4. transformer.py              4. Graphiques historique / tendances
5. reporter.py                 5. Page rapports
6. DAG Airflow complet         6. Rafraîchissement auto + alertes
7. Tests pipeline              7. Tests UI + intégration finale
```