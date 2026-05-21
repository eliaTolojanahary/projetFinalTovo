import os
import json
from pathlib import Path
from dotenv import load_dotenv
import requests
import psycopg2

BASE = Path(__file__).parent
load_dotenv(BASE / '.env')

DB = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'dbname': os.getenv('DB_NAME', 'weather_madagascar'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

OPEN_METEO = os.getenv('OPEN_METEO_BASE', 'https://api.open-meteo.com/v1/forecast')
TIMEZONE = 'Indian/Antananarivo'

# Variables à récupérer selon le todo
CURRENT_VARS = 'temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,surface_pressure'
HOURLY_VARS  = 'temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,surface_pressure'
DAILY_VARS   = 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,uv_index_max'


def get_conn():
    conn = psycopg2.connect(**DB)
    conn.autocommit = True
    return conn


def fetch_locations(conn):
    cur = conn.cursor()
    cur.execute('SELECT id, latitude, longitude FROM weather_locations')
    rows = cur.fetchall()
    cur.close()
    return rows


def insert_raw(conn, location_id, api_type, raw_json):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO weather_raw(location_id, api_source_id, api_type, raw_json) VALUES (%s, %s, %s, %s)",
        (location_id, 1, api_type, json.dumps(raw_json))
    )
    cur.close()


def call_open_meteo(lat, lon, extra_params):
    """Appelle l'API Open-Meteo avec les paramètres donnés."""
    params = {'latitude': lat, 'longitude': lon, 'timezone': TIMEZONE}
    params.update(extra_params)
    r = requests.get(OPEN_METEO, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def run_current():
    """
    Phase 3 — Extraction current (toutes les heures via Airflow).
    Utilise le paramètre 'current' de l'API Open-Meteo (v1).
    """
    conn = get_conn()
    locations = fetch_locations(conn)
    for loc_id, lat, lon in locations:
        try:
            data = call_open_meteo(lat, lon, {'current': CURRENT_VARS})
            insert_raw(conn, loc_id, 'current', data)
            print(f'[current] location {loc_id} OK')
        except Exception as e:
            print(f'[current] location {loc_id} ERREUR: {e}')
    conn.close()


def run_hourly_daily():
    """
    Phase 3 — Extraction hourly + daily (une fois par jour via Airflow).
    """
    conn = get_conn()
    locations = fetch_locations(conn)
    for loc_id, lat, lon in locations:
        # hourly
        try:
            data = call_open_meteo(lat, lon, {'hourly': HOURLY_VARS})
            insert_raw(conn, loc_id, 'hourly', data)
            print(f'[hourly] location {loc_id} OK')
        except Exception as e:
            print(f'[hourly] location {loc_id} ERREUR: {e}')

        # daily
        try:
            data = call_open_meteo(lat, lon, {'daily': DAILY_VARS})
            insert_raw(conn, loc_id, 'daily', data)
            print(f'[daily] location {loc_id} OK')
        except Exception as e:
            print(f'[daily] location {loc_id} ERREUR: {e}')

    conn.close()


def run_all():
    """Lance current + hourly + daily (utilisé pour les tests manuels)."""
    run_current()
    run_hourly_daily()


if __name__ == '__main__':
    run_all()
