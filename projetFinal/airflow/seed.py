import os
import csv
import json
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

BASE = Path(__file__).parent
STATIC = BASE / 'static_data'

load_dotenv(BASE / '.env')

DB = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'dbname': os.getenv('DB_NAME', 'weather_madagascar'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}


def get_conn():
    conn = psycopg2.connect(**DB)
    conn.autocommit = True
    return conn


def load_climate_types(conn):
    path = STATIC / 'climate_types.txt'
    with path.open(encoding='utf-8') as f:
        cur = conn.cursor()
        for line in f:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.strip().split(',', 2)]
            if len(parts) < 2:
                continue
            id_, nom, desc = (parts + [None, None])[:3]
            cur.execute(
                """
                INSERT INTO climate_types(id, nom, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (int(id_), nom, desc)
            )
        cur.close()


def load_timezones(conn):
    path = STATIC / 'timezones.csv'
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cur = conn.cursor()
        for r in reader:
            cur.execute(
                """
                INSERT INTO timezones(id, nom, offset_utc)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (int(r['id']), r['nom'], r['offset_utc'])
            )
        cur.close()


def load_regions(conn):
    path = STATIC / 'regions_madagascar.csv'
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cur = conn.cursor()
        for r in reader:
            cur.execute(
                """
                INSERT INTO regions(id, nom_region, chef_lieu, latitude, longitude, altitude_moyenne, climate_type_id, timezone_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    int(r['id']), r['nom_region'], r.get('chef_lieu'), float(r['latitude']), float(r['longitude']),
                    float(r['altitude_moyenne']) if r.get('altitude_moyenne') else None,
                    int(r['climate_type_id']) if r.get('climate_type_id') else None,
                    int(r['timezone_id']) if r.get('timezone_id') else None
                )
            )
        cur.close()


def load_weather_locations(conn):
    path = STATIC / 'weather_locations.csv'
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cur = conn.cursor()
        for r in reader:
            cur.execute(
                """
                INSERT INTO weather_locations(id, region_id, nom_station, latitude, longitude, elevation)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (int(r['id']), int(r['region_id']), r['nom_station'], float(r['latitude']), float(r['longitude']), float(r['elevation']) if r.get('elevation') else None)
            )
        cur.close()


def load_api_sources(conn):
    path = STATIC / 'api_sources.json'
    with path.open(encoding='utf-8') as f:
        arr = json.load(f)
        cur = conn.cursor()
        for r in arr:
            cur.execute(
                """
                INSERT INTO api_sources(id, nom_source, base_url, api_type, is_active)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (int(r['id']), r['nom_source'], r['base_url'], r.get('api_type'), bool(r.get('is_active')))
            )
        cur.close()


def load_units_and_variables(conn):
    path = STATIC / 'units_and_variables.json'
    with path.open(encoding='utf-8') as f:
        data = json.load(f)
        cur = conn.cursor()
        for u in data.get('units', []):
            cur.execute(
                """
                INSERT INTO units(id, nom_unite, symbole, type_variable)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (int(u['id']), u['nom_unite'], u.get('symbole'), u.get('type_variable'))
            )
        for v in data.get('variables', []):
            cur.execute(
                """
                INSERT INTO variables(id, code, nom_variable, unite_id, description)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (int(v['id']), v['code'], v.get('nom_variable'), int(v['unite_id']) if v.get('unite_id') else None, v.get('description'))
            )
        cur.close()


def load_weather_thresholds(conn):
    path = STATIC / 'weather_thresholds.json'
    with path.open(encoding='utf-8') as f:
        arr = json.load(f)
        cur = conn.cursor()
        for r in arr:
            cur.execute(
                """
                INSERT INTO weather_thresholds(id, variable_id, seuil_min, seuil_max, severite)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (int(r['id']), int(r['variable_id']), r.get('seuil_min'), r.get('seuil_max'), r.get('severite'))
            )
        cur.close()


def load_alert_types(conn):
    path = STATIC / 'alert_types.json'
    with path.open(encoding='utf-8') as f:
        arr = json.load(f)
        cur = conn.cursor()
        for r in arr:
            cur.execute(
                """
                INSERT INTO alert_types(id, code, nom, description, severite_defaut)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (int(r['id']), r['code'], r.get('nom'), r.get('description'), r.get('severite_defaut'))
            )
        cur.close()


def main():
    conn = get_conn()
    load_climate_types(conn)
    load_timezones(conn)
    load_regions(conn)
    load_weather_locations(conn)
    load_api_sources(conn)
    load_units_and_variables(conn)
    load_weather_thresholds(conn)
    load_alert_types(conn)
    conn.close()


if __name__ == '__main__':
    main()
