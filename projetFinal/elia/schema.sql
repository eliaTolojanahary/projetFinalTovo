-- 1. climate_types
CREATE TABLE IF NOT EXISTS climate_types (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT
);

-- 2. timezones
CREATE TABLE IF NOT EXISTS timezones (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    offset_utc VARCHAR(10)
);

-- 3. regions
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    nom_region VARCHAR(100) NOT NULL,
    chef_lieu VARCHAR(100),
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    altitude_moyenne FLOAT,
    climate_type_id INT REFERENCES climate_types(id),
    timezone_id INT REFERENCES timezones(id)
);

-- 4. weather_locations (1 station par région)
CREATE TABLE IF NOT EXISTS weather_locations (
    id SERIAL PRIMARY KEY,
    region_id INT REFERENCES regions(id),
    nom_station VARCHAR(100) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    elevation FLOAT
);

-- 5. api_sources
CREATE TABLE IF NOT EXISTS api_sources (
    id SERIAL PRIMARY KEY,
    nom_source VARCHAR(100) NOT NULL,
    base_url TEXT NOT NULL,
    api_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

-- 6. units
CREATE TABLE IF NOT EXISTS units (
    id SERIAL PRIMARY KEY,
    nom_unite VARCHAR(50) NOT NULL,
    symbole VARCHAR(20),
    type_variable VARCHAR(50)
);

-- 7. variables
CREATE TABLE IF NOT EXISTS variables (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    nom_variable VARCHAR(100),
    unite_id INT REFERENCES units(id),
    description TEXT
);

-- 8. weather_thresholds
CREATE TABLE IF NOT EXISTS weather_thresholds (
    id SERIAL PRIMARY KEY,
    variable_id INT REFERENCES variables(id),
    seuil_min FLOAT,
    seuil_max FLOAT,
    severite VARCHAR(20)
);

-- 9. alert_types
CREATE TABLE IF NOT EXISTS alert_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    nom VARCHAR(100),
    description TEXT,
    severite_defaut VARCHAR(20)
);

-- 10. weather_raw
CREATE TABLE IF NOT EXISTS weather_raw (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES weather_locations(id),
    api_source_id INT REFERENCES api_sources(id),
    api_type VARCHAR(20) NOT NULL,
    raw_json JSONB NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- 11. weather_clean
CREATE TABLE IF NOT EXISTS weather_clean (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES weather_locations(id),
    variable_id INT REFERENCES variables(id),
    valeur FLOAT,
    timestamp TIMESTAMP NOT NULL,
    source_raw_id INT REFERENCES weather_raw(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 12. weather_daily
CREATE TABLE IF NOT EXISTS weather_daily (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES weather_locations(id),
    date DATE NOT NULL,
    temp_avg FLOAT,
    temp_min FLOAT,
    temp_max FLOAT,
    precipitation_sum FLOAT,
    humidity_avg FLOAT,
    wind_speed_avg FLOAT,
    uv_index_max FLOAT,
    UNIQUE(location_id, date)
);

-- 13. weather_report
CREATE TABLE IF NOT EXISTS weather_report (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES weather_locations(id),
    date DATE NOT NULL,
    summary_text TEXT,
    temp_avg FLOAT,
    temp_min FLOAT,
    temp_max FLOAT,
    precipitation_sum FLOAT,
    humidity_avg FLOAT,
    wind_speed_avg FLOAT,
    generated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(location_id, date)
);

-- 14. alerts
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES weather_locations(id),
    alert_type_id INT REFERENCES alert_types(id),
    severite VARCHAR(20),
    message TEXT,
    triggered_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- 15. data_quality
CREATE TABLE IF NOT EXISTS data_quality (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES weather_locations(id),
    variable_id INT REFERENCES variables(id),
    anomaly_type VARCHAR(100),
    valeur_detectee FLOAT,
    logged_at TIMESTAMP DEFAULT NOW()
);
