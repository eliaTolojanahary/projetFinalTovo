-- =========================================================
-- WEATHER ANALYTICS MADAGASCAR
-- FINAL POSTGRESQL SCHEMA
-- SIMPLIFIED VERSION
-- =========================================================

CREATE DATABASE IF NOT EXISTS weather;

-- =========================================================
-- TABLE : climate_types
-- =========================================================

CREATE TABLE climate_types (
    id SERIAL PRIMARY KEY,

    nom_climat VARCHAR(100) NOT NULL,

    description TEXT
);

-- =========================================================
-- TABLE : regions
-- =========================================================

CREATE TABLE regions (
    id SERIAL PRIMARY KEY,

    nom_region VARCHAR(150) NOT NULL UNIQUE,

    chef_lieu VARCHAR(150),

    latitude NUMERIC(10,6) NOT NULL,

    longitude NUMERIC(10,6) NOT NULL,

    altitude_moyenne NUMERIC(10,2),

    climate_type_id INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_regions_climate_type
        FOREIGN KEY (climate_type_id)
        REFERENCES climate_types(id)
        ON DELETE SET NULL
);

-- =========================================================
-- TABLE : api_sources
-- =========================================================

CREATE TABLE api_sources (
    id SERIAL PRIMARY KEY,

    nom_source VARCHAR(150) NOT NULL,

    base_url TEXT NOT NULL,

    description TEXT,

    api_type VARCHAR(100),

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- TABLE : units
-- =========================================================

CREATE TABLE units (
    id SERIAL PRIMARY KEY,

    nom_unite VARCHAR(100) NOT NULL,

    symbole VARCHAR(50),

    type_variable VARCHAR(100)
);

-- =========================================================
-- TABLE : variables
-- =========================================================

CREATE TABLE variables (
    id SERIAL PRIMARY KEY,

    code VARCHAR(100) NOT NULL UNIQUE,

    nom_variable VARCHAR(150) NOT NULL,

    unite_id INTEGER,

    type_variable VARCHAR(100),

    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_variables_unit
        FOREIGN KEY (unite_id)
        REFERENCES units(id)
        ON DELETE SET NULL
);

-- =========================================================
-- TABLE : weather_stations
-- 1 REGION = 1 STATION
-- =========================================================

CREATE TABLE weather_stations (
    id SERIAL PRIMARY KEY,

    nom_station VARCHAR(150) NOT NULL,

    region_id INTEGER NOT NULL UNIQUE,

    latitude NUMERIC(10,6) NOT NULL,

    longitude NUMERIC(10,6) NOT NULL,

    altitude NUMERIC(10,2),

    timezone VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_station_region
        FOREIGN KEY (region_id)
        REFERENCES regions(id)
        ON DELETE CASCADE
);

-- =========================================================
-- TABLE : weather_hourly
-- DONNEES METEO HORAIRES
-- =========================================================

CREATE TABLE weather_hourly (
    id BIGSERIAL PRIMARY KEY,

    station_id INTEGER NOT NULL,

    date_heure TIMESTAMP NOT NULL,

    temperature_2m NUMERIC(5,2),

    relative_humidity_2m NUMERIC(5,2),

    apparent_temperature NUMERIC(5,2),

    precipitation NUMERIC(6,2),

    rain NUMERIC(6,2),

    wind_speed_10m NUMERIC(6,2),

    wind_direction_10m NUMERIC(6,2),

    surface_pressure NUMERIC(8,2),

    uv_index NUMERIC(4,2),

    is_day BOOLEAN,

    source_api_id INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_hourly_station
        FOREIGN KEY (station_id)
        REFERENCES weather_stations(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_hourly_api
        FOREIGN KEY (source_api_id)
        REFERENCES api_sources(id)
        ON DELETE SET NULL
);

-- =========================================================
-- TABLE : weather_daily
-- AGREGATIONS JOURNALIERES
-- =========================================================

CREATE TABLE weather_daily (
    id BIGSERIAL PRIMARY KEY,

    station_id INTEGER NOT NULL,

    date DATE NOT NULL,

    temperature_2m_max NUMERIC(5,2),

    temperature_2m_min NUMERIC(5,2),

    temperature_avg NUMERIC(5,2),

    relative_humidity_avg NUMERIC(5,2),

    precipitation_sum NUMERIC(6,2),

    rain_sum NUMERIC(6,2),

    wind_speed_10m_max NUMERIC(6,2),

    wind_speed_avg NUMERIC(6,2),

    wind_gusts_10m_max NUMERIC(6,2),

    sunshine_duration NUMERIC(10,2),

    uv_index_max NUMERIC(5,2),

    source_api_id INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_daily_station
        FOREIGN KEY (station_id)
        REFERENCES weather_stations(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_daily_api
        FOREIGN KEY (source_api_id)
        REFERENCES api_sources(id)
        ON DELETE SET NULL
);

-- =========================================================
-- TABLE : weather_report
-- RAPPORTS METEO
-- =========================================================

CREATE TABLE weather_report (
    id BIGSERIAL PRIMARY KEY,

    station_id INTEGER NOT NULL,

    date DATE NOT NULL,

    summary_text TEXT,

    temperature_avg NUMERIC(5,2),

    temperature_min NUMERIC(5,2),

    temperature_max NUMERIC(5,2),

    precipitation_sum NUMERIC(6,2),

    humidity_avg NUMERIC(5,2),

    wind_speed_avg NUMERIC(6,2),

    feels_like_avg NUMERIC(5,2),

    weather_score NUMERIC(5,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_report_station
        FOREIGN KEY (station_id)
        REFERENCES weather_stations(id)
        ON DELETE CASCADE
);

-- =========================================================
-- TABLE : alerts
-- ALERTES METEO
-- =========================================================

CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,

    station_id INTEGER NOT NULL,

    date_heure TIMESTAMP NOT NULL,

    type_alerte VARCHAR(100),

    niveau VARCHAR(50),

    message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_alert_station
        FOREIGN KEY (station_id)
        REFERENCES weather_stations(id)
        ON DELETE CASCADE
);

-- =========================================================
-- INDEXES
-- =========================================================

CREATE INDEX idx_regions_nom
ON regions(nom_region);

CREATE INDEX idx_weather_hourly_station
ON weather_hourly(station_id);

CREATE INDEX idx_weather_hourly_datetime
ON weather_hourly(date_heure);

CREATE INDEX idx_weather_daily_station
ON weather_daily(station_id);

CREATE INDEX idx_weather_daily_date
ON weather_daily(date);

CREATE INDEX idx_weather_report_station
ON weather_report(station_id);

CREATE INDEX idx_weather_report_date
ON weather_report(date);

CREATE INDEX idx_alerts_station
ON alerts(station_id);

CREATE INDEX idx_alerts_datetime
ON alerts(date_heure);

-- =========================================================
-- COMMENTS
-- =========================================================

COMMENT ON TABLE regions IS
'Regions de Madagascar';

COMMENT ON TABLE weather_stations IS
'1 station meteo principale par region';

COMMENT ON TABLE weather_hourly IS
'Donnees meteo horaires venant des APIs';

COMMENT ON TABLE weather_daily IS
'Agregations et statistiques journalieres';

COMMENT ON TABLE weather_report IS
'Rapports meteo generes automatiquement';

COMMENT ON TABLE alerts IS
'Alertes meteo';

-- =========================================================
-- MVP TABLES
-- =========================================================
--
-- regions
-- weather_stations
-- weather_hourly
-- weather_daily
-- weather_report
-- api_sources
--
-- =========================================================

-- =========================================================
-- MVP VARIABLES OPEN-METEO
-- =========================================================
--
-- temperature_2m
-- relative_humidity_2m
-- precipitation
-- wind_speed_10m
-- surface_pressure
--
-- =========================================================