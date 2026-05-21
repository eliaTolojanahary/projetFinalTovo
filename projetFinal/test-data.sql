-- =========================================================
-- WEATHER ANALYTICS MADAGASCAR
-- DONNÉES DE TEST COHÉRENTES
-- =========================================================

-- =========================================================
-- 1. climate_types
-- =========================================================

INSERT INTO climate_types (id, nom_climat, description) VALUES
(1, 'Tropical humide',     'Climat chaud et très pluvieux, côte est et nord-est'),
(2, 'Tropical sec',        'Climat chaud avec longue saison sèche, sud et ouest'),
(3, 'Tempéré d''altitude', 'Climat doux et frais, hautes terres centrales'),
(4, 'Semi-aride',          'Précipitations très faibles, extrême sud');

-- =========================================================
-- 2. regions (6 régions réelles de Madagascar)
-- =========================================================

INSERT INTO regions (id, nom_region, chef_lieu, latitude, longitude, altitude_moyenne, climate_type_id) VALUES
(1, 'Analamanga',        'Antananarivo', -18.910000,  47.536100, 1276.00, 3),
(2, 'Atsinanana',        'Toamasina',   -18.161100,  49.358200,   20.00, 1),
(3, 'Diana',             'Antsiranana', -12.353900,  49.291800,   50.00, 1),
(4, 'Atsimo-Andrefana',  'Toliara',     -23.356100,  43.668600,   15.00, 2),
(5, 'Boeny',             'Mahajanga',   -15.716800,  46.316900,   10.00, 2),
(6, 'Haute Matsiatra',   'Fianarantsoa',-21.453100,  47.085400, 1160.00, 3);

-- =========================================================
-- 3. api_sources
-- =========================================================

INSERT INTO api_sources (id, nom_source, base_url, description, api_type, is_active) VALUES
(1, 'Open-Meteo',       'https://api.open-meteo.com/v1/forecast',          'API météo open-source, sans clé requise',         'REST/JSON', TRUE),
(2, 'OpenWeatherMap',   'https://api.openweathermap.org/data/2.5/weather',  'API météo commerciale avec tier gratuit',         'REST/JSON', TRUE),
(3, 'NASA POWER',       'https://power.larc.nasa.gov/api/temporal/hourly',  'Données climatiques NASA, utile historique',      'REST/JSON', FALSE);

-- =========================================================
-- 4. units
-- =========================================================

INSERT INTO units (id, nom_unite, symbole, type_variable) VALUES
(1, 'Degré Celsius',        '°C',   'temperature'),
(2, 'Pourcentage',          '%',    'humidite'),
(3, 'Millimètre',           'mm',   'precipitation'),
(4, 'Kilomètre par heure',  'km/h', 'vent'),
(5, 'Hectopascal',          'hPa',  'pression'),
(6, 'Indice UV',            'UV',   'rayonnement'),
(7, 'Seconde',              's',    'duree');

-- =========================================================
-- 5. variables
-- =========================================================

INSERT INTO variables (id, code, nom_variable, unite_id, type_variable, description) VALUES
(1, 'temperature_2m',         'Température à 2m',             1, 'temperature',   'Température de l''air mesurée à 2 mètres du sol'),
(2, 'relative_humidity_2m',   'Humidité relative à 2m',       2, 'humidite',      'Humidité relative à 2 mètres du sol'),
(3, 'apparent_temperature',   'Température ressentie',        1, 'temperature',   'Température perçue selon vent et humidité'),
(4, 'precipitation',          'Précipitations totales',       3, 'precipitation', 'Cumul des précipitations sur la période'),
(5, 'rain',                   'Pluie',                        3, 'precipitation', 'Précipitations sous forme liquide uniquement'),
(6, 'wind_speed_10m',         'Vitesse vent à 10m',           4, 'vent',          'Vitesse du vent à 10 mètres du sol'),
(7, 'wind_direction_10m',     'Direction vent à 10m',         NULL, 'vent',       'Direction d''où vient le vent, en degrés'),
(8, 'surface_pressure',       'Pression de surface',          5, 'pression',      'Pression atmosphérique au niveau du sol'),
(9, 'uv_index',               'Indice UV',                    6, 'rayonnement',   'Indice UV solaire'),
(10,'sunshine_duration',      'Durée d''ensoleillement',      7, 'rayonnement',   'Durée d''ensoleillement en secondes sur la période');

-- =========================================================
-- 6. weather_stations (1 par région)
-- =========================================================

INSERT INTO weather_stations (id, nom_station, region_id, latitude, longitude, altitude, timezone) VALUES
(1, 'Station Antananarivo', 1, -18.910000,  47.536100, 1276.00, 'Indian/Antananarivo'),
(2, 'Station Toamasina',    2, -18.161100,  49.358200,   15.00, 'Indian/Antananarivo'),
(3, 'Station Antsiranana',  3, -12.353900,  49.291800,   10.00, 'Indian/Antananarivo'),
(4, 'Station Toliara',      4, -23.356100,  43.668600,   10.00, 'Indian/Antananarivo'),
(5, 'Station Mahajanga',    5, -15.716800,  46.316900,    8.00, 'Indian/Antananarivo'),
(6, 'Station Fianarantsoa', 6, -21.453100,  47.085400, 1160.00, 'Indian/Antananarivo');

-- =========================================================
-- 7. weather_hourly
-- 24h de données : 2025-05-21 00:00 → 23:00
-- Station 1 (Antananarivo) + Station 2 (Toamasina)
-- =========================================================

-- Station 1 : Antananarivo (altitude 1276m → températures fraîches)
INSERT INTO weather_hourly (station_id, date_heure, temperature_2m, relative_humidity_2m, apparent_temperature, precipitation, rain, wind_speed_10m, wind_direction_10m, surface_pressure, uv_index, is_day, source_api_id) VALUES
(1, '2025-05-21 00:00:00', 14.2, 82.0, 12.8,  0.0, 0.0,  8.2, 120.0, 860.5, 0.0, FALSE, 1),
(1, '2025-05-21 01:00:00', 13.8, 84.0, 12.3,  0.0, 0.0,  7.5, 125.0, 860.2, 0.0, FALSE, 1),
(1, '2025-05-21 02:00:00', 13.5, 85.0, 12.0,  0.0, 0.0,  7.0, 130.0, 860.0, 0.0, FALSE, 1),
(1, '2025-05-21 03:00:00', 13.1, 86.0, 11.6,  0.0, 0.0,  6.8, 128.0, 859.8, 0.0, FALSE, 1),
(1, '2025-05-21 04:00:00', 12.8, 87.0, 11.2,  0.0, 0.0,  6.5, 130.0, 859.6, 0.0, FALSE, 1),
(1, '2025-05-21 05:00:00', 12.5, 88.0, 10.9,  0.0, 0.0,  6.2, 132.0, 859.5, 0.0, FALSE, 1),
(1, '2025-05-21 06:00:00', 12.3, 88.0, 10.7,  0.0, 0.0,  6.0, 130.0, 859.8, 0.1, TRUE,  1),
(1, '2025-05-21 07:00:00', 13.5, 85.0, 11.9,  0.0, 0.0,  7.2, 125.0, 860.5, 1.2, TRUE,  1),
(1, '2025-05-21 08:00:00', 15.2, 80.0, 13.7,  0.0, 0.0,  8.5, 118.0, 861.2, 2.5, TRUE,  1),
(1, '2025-05-21 09:00:00', 17.1, 75.0, 15.6,  0.0, 0.0,  9.1, 115.0, 861.8, 3.8, TRUE,  1),
(1, '2025-05-21 10:00:00', 18.8, 70.0, 17.2,  0.0, 0.0,  9.8, 112.0, 862.0, 5.0, TRUE,  1),
(1, '2025-05-21 11:00:00', 20.1, 65.0, 18.5,  0.0, 0.0, 10.5, 110.0, 861.8, 6.1, TRUE,  1),
(1, '2025-05-21 12:00:00', 21.3, 62.0, 19.7,  0.0, 0.0, 11.2, 108.0, 861.5, 6.8, TRUE,  1),
(1, '2025-05-21 13:00:00', 21.8, 60.0, 20.2,  0.0, 0.0, 11.8, 105.0, 861.0, 7.0, TRUE,  1),
(1, '2025-05-21 14:00:00', 21.5, 61.0, 19.9,  0.2, 0.2, 11.5, 108.0, 860.5, 6.5, TRUE,  1),
(1, '2025-05-21 15:00:00', 20.8, 65.0, 19.2,  0.5, 0.5, 10.8, 112.0, 860.2, 5.2, TRUE,  1),
(1, '2025-05-21 16:00:00', 19.5, 70.0, 18.0,  1.2, 1.2, 10.2, 115.0, 860.0, 3.8, TRUE,  1),
(1, '2025-05-21 17:00:00', 18.2, 75.0, 16.7,  0.8, 0.8,  9.5, 118.0, 860.2, 2.0, TRUE,  1),
(1, '2025-05-21 18:00:00', 17.0, 79.0, 15.5,  0.0, 0.0,  8.8, 122.0, 860.5, 0.5, TRUE,  1),
(1, '2025-05-21 19:00:00', 16.2, 81.0, 14.6,  0.0, 0.0,  8.2, 125.0, 860.8, 0.0, FALSE, 1),
(1, '2025-05-21 20:00:00', 15.8, 82.0, 14.2,  0.0, 0.0,  8.0, 122.0, 861.0, 0.0, FALSE, 1),
(1, '2025-05-21 21:00:00', 15.5, 83.0, 13.9,  0.0, 0.0,  7.8, 120.0, 861.2, 0.0, FALSE, 1),
(1, '2025-05-21 22:00:00', 15.2, 84.0, 13.6,  0.0, 0.0,  7.5, 120.0, 861.0, 0.0, FALSE, 1),
(1, '2025-05-21 23:00:00', 14.8, 84.0, 13.2,  0.0, 0.0,  7.2, 122.0, 860.8, 0.0, FALSE, 1),

-- Station 2 : Toamasina (côte est, tropical humide → chaud et très pluvieux)
(2, '2025-05-21 00:00:00', 24.5, 88.0, 26.2,  0.8, 0.8,  12.5,  85.0, 1010.2, 0.0, FALSE, 1),
(2, '2025-05-21 01:00:00', 24.2, 89.0, 25.9,  1.2, 1.2,  11.8,  88.0, 1010.0, 0.0, FALSE, 1),
(2, '2025-05-21 02:00:00', 24.0, 90.0, 25.7,  2.5, 2.5,  11.2,  90.0, 1009.8, 0.0, FALSE, 1),
(2, '2025-05-21 03:00:00', 23.8, 91.0, 25.4,  1.5, 1.5,  10.5,  92.0, 1009.5, 0.0, FALSE, 1),
(2, '2025-05-21 04:00:00', 23.6, 91.0, 25.2,  0.5, 0.5,  10.2,  90.0, 1009.5, 0.0, FALSE, 1),
(2, '2025-05-21 05:00:00', 23.5, 92.0, 25.1,  0.0, 0.0,   9.8,  88.0, 1009.8, 0.0, FALSE, 1),
(2, '2025-05-21 06:00:00', 23.8, 91.0, 25.4,  0.0, 0.0,  10.2,  85.0, 1010.2, 0.3, TRUE,  1),
(2, '2025-05-21 07:00:00', 25.2, 88.0, 26.9,  0.0, 0.0,  11.5,  80.0, 1010.8, 2.0, TRUE,  1),
(2, '2025-05-21 08:00:00', 26.8, 85.0, 28.6,  0.0, 0.0,  12.8,  78.0, 1011.2, 4.5, TRUE,  1),
(2, '2025-05-21 09:00:00', 28.2, 82.0, 30.1,  0.0, 0.0,  13.5,  75.0, 1011.5, 6.2, TRUE,  1),
(2, '2025-05-21 10:00:00', 29.5, 78.0, 31.5,  0.0, 0.0,  14.2,  72.0, 1011.8, 8.0, TRUE,  1),
(2, '2025-05-21 11:00:00', 30.8, 75.0, 32.9,  0.0, 0.0,  15.0,  70.0, 1011.5, 9.5, TRUE,  1),
(2, '2025-05-21 12:00:00', 31.5, 73.0, 33.7,  0.0, 0.0,  15.8,  68.0, 1011.0, 10.2,TRUE,  1),
(2, '2025-05-21 13:00:00', 31.8, 72.0, 34.1,  0.0, 0.0,  16.2,  65.0, 1010.5, 10.5,TRUE,  1),
(2, '2025-05-21 14:00:00', 31.5, 73.0, 33.8,  0.5, 0.5,  15.8,  68.0, 1010.2, 9.8, TRUE,  1),
(2, '2025-05-21 15:00:00', 30.8, 76.0, 33.0,  3.2, 3.2,  15.0,  72.0, 1010.0, 8.0, TRUE,  1),
(2, '2025-05-21 16:00:00', 29.5, 80.0, 31.5,  5.8, 5.8,  14.2,  75.0, 1009.8, 5.5, TRUE,  1),
(2, '2025-05-21 17:00:00', 28.2, 84.0, 30.1,  4.2, 4.2,  13.5,  78.0, 1009.8, 3.0, TRUE,  1),
(2, '2025-05-21 18:00:00', 27.0, 87.0, 28.8,  1.8, 1.8,  12.8,  82.0, 1010.0, 0.8, TRUE,  1),
(2, '2025-05-21 19:00:00', 26.2, 88.0, 27.9,  0.8, 0.8,  12.2,  84.0, 1010.2, 0.0, FALSE, 1),
(2, '2025-05-21 20:00:00', 25.8, 89.0, 27.5,  0.5, 0.5,  11.8,  85.0, 1010.5, 0.0, FALSE, 1),
(2, '2025-05-21 21:00:00', 25.5, 89.0, 27.2,  0.2, 0.2,  11.5,  86.0, 1010.5, 0.0, FALSE, 1),
(2, '2025-05-21 22:00:00', 25.2, 90.0, 26.9,  0.0, 0.0,  11.2,  86.0, 1010.2, 0.0, FALSE, 1),
(2, '2025-05-21 23:00:00', 24.8, 90.0, 26.5,  0.0, 0.0,  11.0,  85.0, 1010.0, 0.0, FALSE, 1);

-- =========================================================
-- 8. weather_daily
-- 3 jours : 19, 20, 21 mai 2025
-- Toutes les 6 stations
-- =========================================================

INSERT INTO weather_daily (station_id, date, temperature_2m_max, temperature_2m_min, temperature_avg, relative_humidity_avg, precipitation_sum, rain_sum, wind_speed_10m_max, wind_speed_avg, wind_gusts_10m_max, sunshine_duration, uv_index_max, source_api_id) VALUES

-- Station 1 : Antananarivo
(1, '2025-05-19', 22.1, 11.8, 16.8, 75.0,  0.0,  0.0, 12.5, 8.5, 18.2, 28800.0, 6.8, 1),
(1, '2025-05-20', 20.5, 12.2, 16.2, 78.0,  3.5,  3.5, 13.2, 9.0, 20.1, 18000.0, 5.2, 1),
(1, '2025-05-21', 21.8, 12.3, 17.0, 77.0,  2.7,  2.7, 11.8, 8.8, 17.5, 21600.0, 7.0, 1),

-- Station 2 : Toamasina
(2, '2025-05-19', 32.2, 23.5, 27.8, 84.0, 18.5, 18.5, 17.5, 13.2, 28.0, 14400.0, 9.8, 1),
(2, '2025-05-20', 31.5, 23.8, 27.5, 86.0, 28.2, 28.2, 18.2, 13.8, 30.5, 10800.0, 8.5, 1),
(2, '2025-05-21', 31.8, 23.5, 27.6, 85.0, 21.5, 21.5, 16.2, 13.0, 26.8, 14400.0, 10.5,1),

-- Station 3 : Antsiranana (nord, tropical)
(3, '2025-05-19', 33.5, 25.2, 29.2, 72.0,  0.0,  0.0, 22.5, 15.8, 35.0, 36000.0, 11.2,1),
(3, '2025-05-20', 34.1, 25.8, 29.8, 70.0,  0.0,  0.0, 24.0, 16.5, 38.2, 36000.0, 11.5,1),
(3, '2025-05-21', 33.8, 25.5, 29.5, 71.0,  0.5,  0.5, 23.2, 16.0, 36.5, 32400.0, 11.0,1),

-- Station 4 : Toliara (sec, aride)
(4, '2025-05-19', 29.8, 18.5, 24.0, 55.0,  0.0,  0.0, 25.5, 18.2, 42.0, 39600.0, 10.8,1),
(4, '2025-05-20', 30.2, 18.2, 23.8, 53.0,  0.0,  0.0, 28.2, 19.5, 45.5, 39600.0, 11.0,1),
(4, '2025-05-21', 30.5, 18.8, 24.5, 52.0,  0.0,  0.0, 26.8, 18.8, 43.2, 39600.0, 11.2,1),

-- Station 5 : Mahajanga (nord-ouest)
(5, '2025-05-19', 35.2, 26.5, 30.8, 68.0,  0.0,  0.0, 20.5, 14.2, 32.0, 36000.0, 12.0,1),
(5, '2025-05-20', 35.8, 27.0, 31.2, 66.0,  0.0,  0.0, 22.0, 15.0, 35.5, 36000.0, 12.2,1),
(5, '2025-05-21', 35.5, 26.8, 31.0, 67.0,  0.0,  0.0, 21.2, 14.5, 33.8, 36000.0, 12.1,1),

-- Station 6 : Fianarantsoa (hautes terres)
(6, '2025-05-19', 20.5, 10.2, 15.2, 72.0,  1.5,  1.5, 10.5,  7.2, 15.8, 25200.0, 6.5, 1),
(6, '2025-05-20', 19.8, 10.8, 15.0, 75.0,  5.2,  5.2, 11.2,  7.8, 17.2, 18000.0, 5.0, 1),
(6, '2025-05-21', 21.2, 10.5, 15.8, 73.0,  0.8,  0.8, 10.8,  7.5, 16.5, 28800.0, 6.8, 1);

-- =========================================================
-- 9. weather_report
-- Rapports générés pour le 2025-05-21
-- =========================================================

INSERT INTO weather_report (station_id, date, summary_text, temperature_avg, temperature_min, temperature_max, precipitation_sum, humidity_avg, wind_speed_avg, feels_like_avg, weather_score) VALUES
(1, '2025-05-21',
 'Journée fraîche typique de la saison sèche sur les hautes terres. Matinée brumeuse avec dissipation en cours de matinée. Légères averses l''après-midi. Températures agréables.',
 17.0, 12.3, 21.8, 2.7, 77.0, 8.8, 15.5, 72.5),

(2, '2025-05-21',
 'Journée chaude et humide sur la côte est. Averses tropicales intenses en fin d''après-midi. Conditions typiques du climat tropical humide. Vigilance recommandée pour les crues.',
 27.6, 23.5, 31.8, 21.5, 85.0, 13.0, 29.2, 45.0),

(3, '2025-05-21',
 'Journée ensoleillée dans le nord. Vent fort caractéristique de la région. Chaleur intense en milieu de journée. Index UV élevé, protection solaire indispensable.',
 29.5, 25.5, 33.8, 0.5, 71.0, 16.0, 31.2, 62.0),

(4, '2025-05-21',
 'Journée très chaude et sèche dans le sud-ouest. Absence totale de précipitations. Vent fort générant de la poussière. Conditions arides typiques.',
 24.5, 18.8, 30.5, 0.0, 52.0, 18.8, 22.8, 58.0),

(5, '2025-05-21',
 'Chaleur intense à Mahajanga. Ciel dégagé toute la journée. Index UV maximal. Hydratation fortement conseillée. Vents de mer modérés en soirée.',
 31.0, 26.8, 35.5, 0.0, 67.0, 14.5, 32.5, 55.0),

(6, '2025-05-21',
 'Conditions douces à Fianarantsoa. Légère pluie en matinée. Après-midi ensoleillée. Nuits fraîches caractéristiques de l''altitude.',
 15.8, 10.5, 21.2, 0.8, 73.0, 7.5, 14.2, 70.0);

-- =========================================================
-- 10. alerts
-- =========================================================

INSERT INTO alerts (station_id, date_heure, type_alerte, niveau, message) VALUES
(2, '2025-05-21 15:00:00', 'PLUIE_FORTE',     'ORANGE',  'Précipitations intenses prévues : 5 à 10 mm/h. Risque de ruissellement et d''inondations localisées dans la région de Toamasina.'),
(2, '2025-05-20 12:00:00', 'PLUIE_FORTE',     'ROUGE',   'Cumul exceptionnel de 28 mm en 24h. Crues possibles. Éviter les zones basses et les traversées de cours d''eau.'),
(3, '2025-05-21 10:00:00', 'VENT_FORT',       'JAUNE',   'Rafales atteignant 38 km/h. Prudence pour les activités nautiques et les déplacements en moto.'),
(4, '2025-05-21 11:00:00', 'CHALEUR_EXTREME', 'ORANGE',  'Température maximale de 30.5°C combinée à un vent fort et une humidité faible. Risque de coup de chaleur. Hydratation impérative.'),
(5, '2025-05-20 13:00:00', 'UV_ELEVE',        'ORANGE',  'Index UV de 12.2 (extrême). Protection solaire indice 50+ obligatoire. Éviter l''exposition directe entre 10h et 16h.'),
(1, '2025-05-20 16:00:00', 'ORAGE',           'JAUNE',   'Orages locaux possibles en fin d''après-midi sur Antananarivo et ses environs. Rafales jusqu''à 20 km/h.');

-- =========================================================
-- Remise à jour des séquences SERIAL (PostgreSQL)
-- =========================================================

SELECT setval('climate_types_id_seq',   (SELECT MAX(id) FROM climate_types));
SELECT setval('regions_id_seq',         (SELECT MAX(id) FROM regions));
SELECT setval('api_sources_id_seq',     (SELECT MAX(id) FROM api_sources));
SELECT setval('units_id_seq',           (SELECT MAX(id) FROM units));
SELECT setval('variables_id_seq',       (SELECT MAX(id) FROM variables));
SELECT setval('weather_stations_id_seq',(SELECT MAX(id) FROM weather_stations));
SELECT setval('weather_hourly_id_seq',  (SELECT MAX(id) FROM weather_hourly));
SELECT setval('weather_daily_id_seq',   (SELECT MAX(id) FROM weather_daily));
SELECT setval('weather_report_id_seq',  (SELECT MAX(id) FROM weather_report));
SELECT setval('alerts_id_seq',          (SELECT MAX(id) FROM alerts));