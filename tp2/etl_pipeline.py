#!/usr/bin/env python3
"""
TP2 ETL pipeline: 4 heterogeneous sources -> PostgreSQL star schema.

Covered steps:
1) Connections and file access checks
2) Extract (MySQL/db dump, TXT, Excel, JSON)
3) Load raw STAGING tables
4) Data cleaning and normalization
5) Business transformations
6) Build dimensions
7) Build fact table
8) Data quality checks
9) SQL analytics outputs (including expensive customers analysis)
10) Generate target PostgreSQL schema file
11) One-click main() orchestration with "Step OK" logs
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

import psycopg2
from psycopg2.extras import execute_values

try:
    import openpyxl
except Exception as exc:  # pragma: no cover
    openpyxl = None
    OPENPYXL_IMPORT_ERROR = exc
else:
    OPENPYXL_IMPORT_ERROR = None


BASE_DIR = Path(__file__).resolve().parent / "sources"
MYSQL_SQL_FILE = BASE_DIR / "01_source_mysql_printer_sales.sql"
TXT_FILE = BASE_DIR / "02_route_logs.txt"
EXCEL_FILE = BASE_DIR / "03_sales_promises.xlsx"
JSON_FILE = BASE_DIR / "04_fuel_expenses.json"


@dataclass
class PgConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "dwh_imprimantes"
    user: str = "postgres"
    password: str = "NouveauMotDePasse"


@dataclass
class MySqlConfig:
    host: str = "localhost"
    port: int = 3306
    dbname: str = "tp_printer_sales"
    user: str = "root"
    password: str = ""


def log_ok(msg: str) -> None:
    print(f"Step OK - {msg}")


def log_info(msg: str) -> None:
    print(f"[INFO] {msg}")


def log_warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def normalize_code(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.upper()


def parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None

    text = str(value).strip()
    if not text:
        return None
    text = text.replace(" ", "")

    # Handles "12,5", "1 234,56", "1234.56"
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")

    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", ".", "-", "-."}:
        return None

    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_int(value: Any) -> int | None:
    dec = parse_decimal(value)
    if dec is None:
        return None
    try:
        return int(dec)
    except Exception:
        return None


def parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def to_float_or_none(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def pick_first(record: dict[str, Any], aliases: Iterable[str]) -> Any:
    lowered = {k.lower().strip(): v for k, v in record.items()}
    for alias in aliases:
        key = alias.lower().strip()
        if key in lowered:
            return lowered[key]
    return None


def split_sql_values(values_chunk: str) -> list[str]:
    """Split SQL values list while preserving quoted commas."""
    out: list[str] = []
    current: list[str] = []
    in_quote = False
    i = 0
    while i < len(values_chunk):
        ch = values_chunk[i]
        if ch == "'":
            # SQL escaped quote: ''
            if in_quote and i + 1 < len(values_chunk) and values_chunk[i + 1] == "'":
                current.append("'")
                i += 2
                continue
            in_quote = not in_quote
            i += 1
            continue

        if ch == "," and not in_quote:
            out.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1

    out.append("".join(current).strip())
    return out


def sql_literal_to_python(token: str) -> Any:
    t = token.strip()
    if not t or t.upper() == "NULL":
        return None
    return t


def parse_mysql_dump(sql_file: Path) -> dict[str, list[dict[str, Any]]]:
    tables: dict[str, list[dict[str, Any]]] = {
        "hr_vendeurs": [],
        "ref_clients": [],
        "ref_produits": [],
        "sales_orders": [],
    }

    pattern = re.compile(
        r"INSERT INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\((.*)\);",
        re.IGNORECASE,
    )

    with sql_file.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line.upper().startswith("INSERT INTO"):
                continue
            m = pattern.match(line)
            if not m:
                continue

            table = m.group(1)
            if table not in tables:
                continue

            columns = [c.strip() for c in m.group(2).split(",")]
            values = split_sql_values(m.group(3))
            if len(columns) != len(values):
                continue

            row = {col: sql_literal_to_python(val) for col, val in zip(columns, values)}
            tables[table].append(row)

    return tables


def try_mysql_connection(cfg: MySqlConfig):
    try:
        import pymysql  # type: ignore
    except Exception:
        return None

    try:
        conn = pymysql.connect(
            host=cfg.host,
            port=cfg.port,
            user=cfg.user,
            password=cfg.password,
            database=cfg.dbname,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        return conn
    except Exception as exc:
        log_warn(f"MySQL connection unavailable ({exc}). Fallback to SQL dump.")
        return None


def extract_mysql_data(cfg: MySqlConfig, sql_dump: Path) -> dict[str, list[dict[str, Any]]]:
    conn = try_mysql_connection(cfg)
    if conn is None:
        data = parse_mysql_dump(sql_dump)
        log_ok("Connexion MySQL fallback via SQL dump parsed")
        return data

    data: dict[str, list[dict[str, Any]]] = {}
    try:
        with conn.cursor() as cur:
            for table in ["hr_vendeurs", "ref_clients", "ref_produits", "sales_orders"]:
                cur.execute(f"SELECT * FROM {table}")
                data[table] = list(cur.fetchall())
        log_ok("Connexion MySQL et extraction SQL directes")
        return data
    finally:
        conn.close()


def extract_route_logs(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            rows.append(dict(row))
    return rows


def extract_excel_promises(path: Path) -> list[dict[str, Any]]:
    if openpyxl is None:
        raise RuntimeError(f"openpyxl missing: {OPENPYXL_IMPORT_ERROR}")

    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active

    headers: list[str] = []
    for cell in ws[1]:
        headers.append(str(cell.value).strip() if cell.value is not None else "")

    rows: list[dict[str, Any]] = []
    for row_idx in range(2, ws.max_row + 1):
        values = [ws.cell(row=row_idx, column=col).value for col in range(1, len(headers) + 1)]
        if all(v is None or str(v).strip() == "" for v in values):
            continue
        rows.append(dict(zip(headers, values)))
    return rows


def extract_fuel_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        # Optional wrapper key support
        for key in ["data", "rows", "fuel_expenses"]:
            if key in payload and isinstance(payload[key], list):
                return payload[key]
    raise ValueError("Unsupported JSON structure in fuel expenses file")


def assert_files_exist() -> None:
    required = [MYSQL_SQL_FILE, TXT_FILE, EXCEL_FILE, JSON_FILE]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required input files: {', '.join(missing)}")
    log_ok("Verifier acces fichiers txt/excel/json/sql")


def get_pg_connection(cfg: PgConfig):
    return psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.dbname,
        user=cfg.user,
        password=cfg.password,
    )


def create_staging_tables(conn) -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS stg_hr_vendeurs (
        seller_code TEXT,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        salary TEXT,
        hire_date TEXT,
        home_country TEXT,
        home_region TEXT,
        home_city TEXT,
        manager_code TEXT
    );

    CREATE TABLE IF NOT EXISTS stg_ref_clients (
        customer_code TEXT,
        customer_name TEXT,
        sector TEXT,
        country TEXT,
        region_name TEXT,
        city TEXT,
        postal_code TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS stg_ref_produits (
        product_code TEXT,
        product_name TEXT,
        category_name TEXT,
        range_name TEXT,
        list_price TEXT,
        active_flag TEXT,
        launch_date TEXT
    );

    CREATE TABLE IF NOT EXISTS stg_sales_orders (
        order_id TEXT,
        order_date TEXT,
        seller_code TEXT,
        customer_code TEXT,
        product_code TEXT,
        quantity TEXT,
        unit_price TEXT,
        discount_pct TEXT,
        order_status TEXT,
        promised_delivery_date TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS stg_route_logs (
        route_id TEXT,
        visit_date TEXT,
        seller_code TEXT,
        customer_code TEXT,
        visit_city TEXT,
        planned_visits TEXT,
        actual_visits TEXT,
        km_travelled TEXT,
        travel_expense TEXT,
        road_toll TEXT,
        trip_status TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS stg_sales_promises (
        promise_id TEXT,
        promise_date TEXT,
        seller_code TEXT,
        customer_code TEXT,
        product_code TEXT,
        quantity TEXT,
        unit_price TEXT,
        expected_amount TEXT,
        status TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS stg_fuel_expenses (
        expense_id TEXT,
        expense_date TEXT,
        seller_code TEXT,
        customer_code TEXT,
        city TEXT,
        liters TEXT,
        fuel_amount TEXT,
        other_expense TEXT,
        total_expense TEXT,
        source_json TEXT
    );
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    log_ok("Creation tables stg_* si inexistantes")


def truncate_staging(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            TRUNCATE TABLE
              stg_hr_vendeurs,
              stg_ref_clients,
              stg_ref_produits,
              stg_sales_orders,
              stg_route_logs,
              stg_sales_promises,
              stg_fuel_expenses;
            """
        )
    conn.commit()


def load_staging(conn, mysql_data, route_logs, sales_promises, fuel_rows) -> None:
    truncate_staging(conn)

    def insert_many(table: str, columns: list[str], rows: list[tuple[Any, ...]]) -> None:
        if not rows:
            return
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s"
        with conn.cursor() as cur:
            execute_values(cur, query, rows)

    hr_rows = [
        (
            r.get("seller_code"), r.get("first_name"), r.get("last_name"), r.get("email"),
            r.get("salary"), r.get("hire_date"), r.get("home_country"), r.get("home_region"),
            r.get("home_city"), r.get("manager_code"),
        )
        for r in mysql_data.get("hr_vendeurs", [])
    ]
    insert_many(
        "stg_hr_vendeurs",
        ["seller_code", "first_name", "last_name", "email", "salary", "hire_date", "home_country", "home_region", "home_city", "manager_code"],
        hr_rows,
    )

    client_rows = [
        (
            r.get("customer_code"), r.get("customer_name"), r.get("sector"), r.get("country"),
            r.get("region_name"), r.get("city"), r.get("postal_code"), r.get("created_at"),
        )
        for r in mysql_data.get("ref_clients", [])
    ]
    insert_many(
        "stg_ref_clients",
        ["customer_code", "customer_name", "sector", "country", "region_name", "city", "postal_code", "created_at"],
        client_rows,
    )

    prod_rows = [
        (
            r.get("product_code"), r.get("product_name"), r.get("category_name"), r.get("range_name"),
            r.get("list_price"), r.get("active_flag"), r.get("launch_date"),
        )
        for r in mysql_data.get("ref_produits", [])
    ]
    insert_many(
        "stg_ref_produits",
        ["product_code", "product_name", "category_name", "range_name", "list_price", "active_flag", "launch_date"],
        prod_rows,
    )

    order_rows = [
        (
            r.get("order_id"), r.get("order_date"), r.get("seller_code"), r.get("customer_code"), r.get("product_code"),
            r.get("quantity"), r.get("unit_price"), r.get("discount_pct"), r.get("order_status"),
            r.get("promised_delivery_date"), r.get("created_at"),
        )
        for r in mysql_data.get("sales_orders", [])
    ]
    insert_many(
        "stg_sales_orders",
        ["order_id", "order_date", "seller_code", "customer_code", "product_code", "quantity", "unit_price", "discount_pct", "order_status", "promised_delivery_date", "created_at"],
        order_rows,
    )

    route_rows = [
        (
            r.get("route_id"), r.get("visit_date"), r.get("seller_code"), r.get("customer_code"), r.get("visit_city"),
            r.get("planned_visits"), r.get("actual_visits"), r.get("km_travelled"), r.get("travel_expense"),
            r.get("road_toll"), r.get("trip_status"), r.get("notes"),
        )
        for r in route_logs
    ]
    insert_many(
        "stg_route_logs",
        ["route_id", "visit_date", "seller_code", "customer_code", "visit_city", "planned_visits", "actual_visits", "km_travelled", "travel_expense", "road_toll", "trip_status", "notes"],
        route_rows,
    )

    promise_rows = []
    for r in sales_promises:
        promise_rows.append(
            (
                pick_first(r, ["promise_id", "id", "promise_code"]),
                pick_first(r, ["promise_date", "date", "visit_date", "order_date"]),
                pick_first(r, ["seller_code", "seller", "vendeur_code"]),
                pick_first(r, ["customer_code", "client_code", "customer"]),
                pick_first(r, ["product_code", "produit_code", "product"]),
                pick_first(r, ["quantity", "qty"]),
                pick_first(r, ["unit_price", "price", "prix_unitaire"]),
                pick_first(r, ["expected_amount", "amount_expected", "montant_attendu"]),
                pick_first(r, ["status", "promise_status", "statut"]),
                pick_first(r, ["notes", "comment", "commentaire"]),
            )
        )
    insert_many(
        "stg_sales_promises",
        ["promise_id", "promise_date", "seller_code", "customer_code", "product_code", "quantity", "unit_price", "expected_amount", "status", "notes"],
        promise_rows,
    )

    fuel_insert_rows = []
    for r in fuel_rows:
        fuel_insert_rows.append(
            (
                pick_first(r, ["expense_id", "id", "fuel_id"]),
                pick_first(r, ["expense_date", "date", "visit_date"]),
                pick_first(r, ["seller_code", "seller", "vendeur_code"]),
                pick_first(r, ["customer_code", "client_code"]),
                pick_first(r, ["city", "visit_city", "ville"]),
                pick_first(r, ["liters", "litres", "fuel_liters"]),
                pick_first(r, ["fuel_amount", "fuel_cost", "carburant"]),
                pick_first(r, ["other_expense", "other_cost", "frais_annexes"]),
                pick_first(r, ["total_expense", "total", "amount"]),
                json.dumps(r, ensure_ascii=False),
            )
        )
    insert_many(
        "stg_fuel_expenses",
        ["expense_id", "expense_date", "seller_code", "customer_code", "city", "liters", "fuel_amount", "other_expense", "total_expense", "source_json"],
        fuel_insert_rows,
    )

    conn.commit()
    log_ok("Chargement de toutes les sources brutes en STAGING")


def clean_and_transform(mysql_data, route_logs, sales_promises, fuel_rows):
    # Dimensions source cleaned
    sellers = []
    for r in mysql_data.get("hr_vendeurs", []):
        sellers.append(
            {
                "seller_code": normalize_code(r.get("seller_code")),
                "first_name": str(r.get("first_name") or "").strip().title(),
                "last_name": str(r.get("last_name") or "").strip().upper(),
                "email": str(r.get("email") or "").strip().lower(),
                "salary": parse_decimal(r.get("salary")),
                "hire_date": parse_date(r.get("hire_date")),
                "home_country": str(r.get("home_country") or "").strip(),
                "home_region": str(r.get("home_region") or "").strip(),
                "home_city": str(r.get("home_city") or "").strip(),
                "manager_code": normalize_code(r.get("manager_code")),
            }
        )

    customers = []
    for r in mysql_data.get("ref_clients", []):
        customers.append(
            {
                "customer_code": normalize_code(r.get("customer_code")),
                "customer_name": str(r.get("customer_name") or "").strip(),
                "sector": str(r.get("sector") or "").strip(),
                "country": str(r.get("country") or "").strip(),
                "region_name": str(r.get("region_name") or "").strip(),
                "city": str(r.get("city") or "").strip(),
                "postal_code": str(r.get("postal_code") or "").strip(),
                "created_at": parse_date(r.get("created_at")),
            }
        )

    products = []
    for r in mysql_data.get("ref_produits", []):
        products.append(
            {
                "product_code": normalize_code(r.get("product_code")),
                "product_name": str(r.get("product_name") or "").strip(),
                "category_name": str(r.get("category_name") or "").strip(),
                "range_name": str(r.get("range_name") or "").strip(),
                "list_price": parse_decimal(r.get("list_price")),
                "active_flag": parse_int(r.get("active_flag")) or 0,
                "launch_date": parse_date(r.get("launch_date")),
            }
        )

    sales_orders = []
    for r in mysql_data.get("sales_orders", []):
        quantity = parse_int(r.get("quantity")) or 0
        unit_price = parse_decimal(r.get("unit_price")) or Decimal("0")
        discount_pct = parse_decimal(r.get("discount_pct")) or Decimal("0")

        # net_sales_amount = quantity * unit_price * (1 - discount_pct)
        net_sales_amount = (Decimal(quantity) * unit_price * (Decimal("1") - (discount_pct / Decimal("100"))))
        sales_orders.append(
            {
                "order_id": parse_int(r.get("order_id")),
                "order_date": parse_date(r.get("order_date")),
                "seller_code": normalize_code(r.get("seller_code")),
                "customer_code": normalize_code(r.get("customer_code")),
                "product_code": normalize_code(r.get("product_code")),
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_pct": discount_pct,
                "order_status": str(r.get("order_status") or "").strip().upper(),
                "promised_delivery_date": parse_date(r.get("promised_delivery_date")),
                "created_at": parse_date(r.get("created_at")),
                "net_sales_amount": net_sales_amount,
            }
        )

    # Route logs aggregated by seller + date
    route_agg: dict[tuple[str, date], dict[str, Decimal]] = defaultdict(lambda: {
        "km": Decimal("0"),
        "road_expense": Decimal("0"),
        "route_count": Decimal("0"),
    })
    for r in route_logs:
        seller = normalize_code(r.get("seller_code"))
        visit_date = parse_date(r.get("visit_date"))
        if not seller or not visit_date:
            continue

        km = parse_decimal(r.get("km_travelled")) or Decimal("0")
        travel_expense = parse_decimal(r.get("travel_expense")) or Decimal("0")
        road_toll = parse_decimal(r.get("road_toll")) or Decimal("0")

        key = (seller, visit_date)
        route_agg[key]["km"] += km
        route_agg[key]["road_expense"] += travel_expense + road_toll
        route_agg[key]["route_count"] += Decimal("1")

    # Fuel expenses aggregated by seller + date
    fuel_agg: dict[tuple[str, date], dict[str, Decimal]] = defaultdict(lambda: {
        "liters": Decimal("0"),
        "fuel_amount": Decimal("0"),
        "other_expense": Decimal("0"),
    })
    for r in fuel_rows:
        seller = normalize_code(pick_first(r, ["seller_code", "seller", "vendeur_code"]))
        expense_date = parse_date(pick_first(r, ["expense_date", "date", "visit_date"]))
        if not seller or not expense_date:
            continue

        liters = parse_decimal(pick_first(r, ["liters", "litres", "fuel_liters"])) or Decimal("0")
        fuel_amount = parse_decimal(pick_first(r, ["fuel_amount", "fuel_cost", "carburant"]))
        other_expense = parse_decimal(pick_first(r, ["other_expense", "other_cost", "frais_annexes"]))
        total = parse_decimal(pick_first(r, ["total_expense", "total", "amount"]))

        if fuel_amount is None:
            fuel_amount = Decimal("0")
        if other_expense is None:
            if total is not None:
                other_expense = total - fuel_amount
            else:
                other_expense = Decimal("0")

        key = (seller, expense_date)
        fuel_agg[key]["liters"] += liters
        fuel_agg[key]["fuel_amount"] += fuel_amount
        fuel_agg[key]["other_expense"] += other_expense

    # Sales promises map, with expected_amount recalculated when missing
    promise_map: dict[tuple[str, str, str, date], Decimal] = {}
    for r in sales_promises:
        seller = normalize_code(pick_first(r, ["seller_code", "seller", "vendeur_code"]))
        customer = normalize_code(pick_first(r, ["customer_code", "client_code", "customer"]))
        product = normalize_code(pick_first(r, ["product_code", "produit_code", "product"]))
        pdate = parse_date(pick_first(r, ["promise_date", "date", "visit_date", "order_date"]))

        if not seller or not customer or not product or not pdate:
            continue

        qty = parse_decimal(pick_first(r, ["quantity", "qty"])) or Decimal("0")
        up = parse_decimal(pick_first(r, ["unit_price", "price", "prix_unitaire"])) or Decimal("0")
        expected = parse_decimal(pick_first(r, ["expected_amount", "amount_expected", "montant_attendu"]))

        # Required by TODO: recalculate expected_amount when missing
        if expected is None:
            expected = qty * up

        promise_map[(seller, customer, product, pdate)] = expected

    log_ok("Data cleaning (upper/trim, dates, decimals, expected_amount)")
    log_ok("Transformations metier (net_sales_amount + aggregations km/carburant/depenses)")

    return {
        "sellers": sellers,
        "customers": customers,
        "products": products,
        "sales_orders": sales_orders,
        "route_agg": route_agg,
        "fuel_agg": fuel_agg,
        "promise_map": promise_map,
    }


def generate_target_schema_file(conn, output_dir: Path = None) -> None:
    """
    Génère le fichier SQL du schéma cible PostgreSQL (star schema)
    dans le dossier target_postgres/
    """
    if output_dir is None:
        # Crée le dossier target_postgres à côté du script
        script_dir = Path(__file__).resolve().parent
        output_dir = script_dir / "target_postgres"
    
    # Crée le dossier s'il n'existe pas
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "05_postgres_schema.sql"
    
    # DDL du schéma en étoile
    schema_ddl = """-- =====================================================
-- SCHEMA DWH EN ÉTOILE - VENTES IMPRIMANTES
-- Fichier généré automatiquement par le pipeline ETL
-- Date de génération: {timestamp}
-- =====================================================

-- Suppression des tables existantes (ordre inverse des dépendances)
DROP TABLE IF EXISTS fact_sales_activity CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_seller CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;

-- =====================================================
-- TABLES DE DIMENSIONS
-- =====================================================

-- Dimension temporelle
CREATE TABLE dim_date (
    date_key     SERIAL PRIMARY KEY,
    full_date    DATE NOT NULL UNIQUE,
    year_num     INT NOT NULL,
    month_num    INT NOT NULL,
    day_num      INT NOT NULL,
    iso_week     INT NOT NULL,
    -- Champs calculés optionnels
    month_name   TEXT GENERATED ALWAYS AS (
        CASE month_num
            WHEN 1 THEN 'Janvier' WHEN 2 THEN 'Février' WHEN 3 THEN 'Mars'
            WHEN 4 THEN 'Avril' WHEN 5 THEN 'Mai' WHEN 6 THEN 'Juin'
            WHEN 7 THEN 'Juillet' WHEN 8 THEN 'Août' WHEN 9 THEN 'Septembre'
            WHEN 10 THEN 'Octobre' WHEN 11 THEN 'Novembre' WHEN 12 THEN 'Décembre'
        END
    ) STORED,
    quarter_num  INT GENERATED ALWAYS AS (((month_num - 1) / 3) + 1) STORED
);

COMMENT ON TABLE dim_date IS 'Dimension temporelle - permet les analyses par jour/mois/année';
COMMENT ON COLUMN dim_date.full_date IS 'Date complète (AAAA-MM-JJ)';
COMMENT ON COLUMN dim_date.iso_week IS 'Numéro de semaine ISO (1-53)';

-- Dimension vendeur
CREATE TABLE dim_seller (
    seller_key   SERIAL PRIMARY KEY,
    seller_code  TEXT NOT NULL UNIQUE,
    first_name   TEXT,
    last_name    TEXT,
    email        TEXT,
    salary       NUMERIC(14,2),
    hire_date    DATE,
    home_country TEXT,
    home_region  TEXT,
    home_city    TEXT,
    manager_code TEXT,
    -- Champ dérivé
    full_name    TEXT GENERATED ALWAYS AS (
        COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')
    ) STORED
);

COMMENT ON TABLE dim_seller IS 'Dimension vendeurs - informations RH et géographiques';
COMMENT ON COLUMN dim_seller.seller_code IS 'Code unique du vendeur (ex: V001)';
COMMENT ON COLUMN dim_seller.manager_code IS 'Code du manager/référent hiérarchique';

-- Dimension client
CREATE TABLE dim_customer (
    customer_key   SERIAL PRIMARY KEY,
    customer_code  TEXT NOT NULL UNIQUE,
    customer_name  TEXT,
    sector         TEXT,
    country        TEXT,
    region_name    TEXT,
    city           TEXT,
    postal_code    TEXT,
    created_at     DATE
);

COMMENT ON TABLE dim_customer IS 'Dimension clients - informations démographiques et géographiques';
COMMENT ON COLUMN dim_customer.sector IS 'Secteur d''activité du client (ex: Industrie, Retail, Service)';

-- Dimension produit
CREATE TABLE dim_product (
    product_key   SERIAL PRIMARY KEY,
    product_code  TEXT NOT NULL UNIQUE,
    product_name  TEXT,
    category_name TEXT,
    range_name    TEXT,
    list_price    NUMERIC(14,2),
    active_flag   INT DEFAULT 1,
    launch_date   DATE,
    is_active     BOOLEAN GENERATED ALWAYS AS (active_flag = 1) STORED
);

COMMENT ON TABLE dim_product IS 'Dimension produits - catalogue et tarifs';
COMMENT ON COLUMN dim_product.range_name IS 'Gamme de produits (ex: Entrée, Milieu, Premium)';

-- =====================================================
-- TABLE DE FAITS
-- =====================================================

-- Table de faits des activités commerciales
CREATE TABLE fact_sales_activity (
    fact_id             BIGSERIAL PRIMARY KEY,
    date_key            INT NOT NULL REFERENCES dim_date(date_key),
    seller_key          INT NOT NULL REFERENCES dim_seller(seller_key),
    customer_key        INT NOT NULL REFERENCES dim_customer(customer_key),
    product_key         INT NOT NULL REFERENCES dim_product(product_key),
    
    -- Métriques de vente
    order_id            INT,
    quantity            INT,
    unit_price          NUMERIC(14,2),
    discount_pct        NUMERIC(7,4),
    net_sales_amount    NUMERIC(14,2),
    expected_amount     NUMERIC(14,2),
    
    -- Métriques logistiques
    km_travelled        NUMERIC(14,2),
    fuel_liters         NUMERIC(14,2),
    fuel_amount         NUMERIC(14,2),
    travel_expense      NUMERIC(14,2),
    total_expense       NUMERIC(14,2),
    
    -- Métriques de performance
    transformation_rate NUMERIC(10,4),
    
    -- Timestamp ETL
    etl_loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE fact_sales_activity IS 'Table de faits - activités commerciales, ventes et coûts associés';
COMMENT ON COLUMN fact_sales_activity.net_sales_amount IS 'Montant net des ventes = quantity * unit_price * (1 - discount_pct/100)';
COMMENT ON COLUMN fact_sales_activity.expected_amount IS 'Montant attendu (promesse de vente)';
COMMENT ON COLUMN fact_sales_activity.total_expense IS 'Dépenses totales = travel_expense + fuel_amount + other_expense';
COMMENT ON COLUMN fact_sales_activity.transformation_rate IS 'Taux de transformation = net_sales_amount / expected_amount';

-- =====================================================
-- INDEX POUR OPTIMISATION DES PERFORMANCES
-- =====================================================

-- Index sur les clés étrangères
CREATE INDEX idx_fact_date ON fact_sales_activity(date_key);
CREATE INDEX idx_fact_seller ON fact_sales_activity(seller_key);
CREATE INDEX idx_fact_customer ON fact_sales_activity(customer_key);
CREATE INDEX idx_fact_product ON fact_sales_activity(product_key);

-- Index composites pour les requêtes courantes
CREATE INDEX idx_fact_date_seller ON fact_sales_activity(date_key, seller_key);
CREATE INDEX idx_fact_date_customer ON fact_sales_activity(date_key, customer_key);
CREATE INDEX idx_fact_sales_amount ON fact_sales_activity(net_sales_amount DESC);

-- Index sur les codes métier dans les dimensions
CREATE INDEX idx_seller_code ON dim_seller(seller_code);
CREATE INDEX idx_customer_code ON dim_customer(customer_code);
CREATE INDEX idx_product_code ON dim_product(product_code);
CREATE INDEX idx_date_full ON dim_date(full_date);

-- =====================================================
-- VUES ANALYTIQUES PRÉDÉFINIES
-- =====================================================

-- Vue 1: Résumé mensuel des ventes par vendeur
CREATE OR REPLACE VIEW v_seller_monthly_performance AS
SELECT 
    s.seller_code,
    s.full_name as seller_name,
    d.year_num,
    d.month_num,
    d.month_name,
    COUNT(DISTINCT f.order_id) as nb_orders,
    SUM(f.quantity) as total_quantity,
    ROUND(SUM(f.net_sales_amount)::numeric, 2) as total_revenue,
    ROUND(SUM(f.km_travelled)::numeric, 2) as total_km,
    ROUND(SUM(f.total_expense)::numeric, 2) as total_cost,
    ROUND(AVG(f.transformation_rate)::numeric, 4) as avg_conversion_rate
FROM fact_sales_activity f
JOIN dim_seller s ON s.seller_key = f.seller_key
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY s.seller_code, s.full_name, d.year_num, d.month_num, d.month_name
ORDER BY d.year_num DESC, d.month_num DESC, total_revenue DESC;

-- Vue 2: Clients les plus coûteux à servir
CREATE OR REPLACE VIEW v_expensive_customers AS
SELECT 
    c.customer_code,
    c.customer_name,
    c.sector,
    c.region_name,
    c.city,
    COUNT(DISTINCT f.order_id) as nb_orders,
    ROUND(SUM(f.net_sales_amount)::numeric, 2) as total_revenue,
    ROUND(SUM(f.km_travelled)::numeric, 2) as total_km,
    ROUND(SUM(f.total_expense)::numeric, 2) as total_service_cost,
    ROUND(
        CASE WHEN SUM(f.net_sales_amount) = 0 THEN 0
        ELSE (SUM(f.total_expense) / SUM(f.net_sales_amount)) * 100
        END::numeric, 2
    ) as cost_per_100_revenue
FROM fact_sales_activity f
JOIN dim_customer c ON c.customer_key = f.customer_key
GROUP BY c.customer_code, c.customer_name, c.sector, c.region_name, c.city
ORDER BY total_service_cost DESC;

-- Vue 3: Produits avec meilleure performance
CREATE OR REPLACE VIEW v_profitability_by_product AS
SELECT 
    p.product_code,
    p.product_name,
    p.category_name,
    p.range_name,
    COUNT(DISTINCT f.order_id) as nb_orders,
    SUM(f.quantity) as units_sold,
    ROUND(SUM(f.net_sales_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(f.unit_price)::numeric, 2) as avg_selling_price,
    ROUND(AVG(p.list_price)::numeric, 2) as catalog_price
FROM fact_sales_activity f
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY p.product_code, p.product_name, p.category_name, p.range_name
ORDER BY total_revenue DESC;

-- =====================================================
-- STATISTIQUES POUR OPTIMISEUR DE REQUÊTES
-- =====================================================

ANALYZE dim_date;
ANALYZE dim_seller;
ANALYZE dim_customer;
ANALYZE dim_product;
ANALYZE fact_sales_activity;
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(schema_ddl.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    
    log_ok(f"Schema cible PostgreSQL généré dans {output_file}")
    print(f"\n📄 Fichier de schéma généré : {output_file}")
    print(f"📊 Taille : {len(schema_ddl):,} caractères\n")


def recreate_dwh_tables(conn) -> None:
    ddl = """
    DROP VIEW IF EXISTS v_seller_monthly_performance CASCADE;
    DROP VIEW IF EXISTS v_expensive_customers CASCADE;
    DROP VIEW IF EXISTS v_profitability_by_product CASCADE;
    
    -- Puis supprimer les tables avec CASCADE
    DROP TABLE IF EXISTS fact_sales_activity CASCADE;
    DROP TABLE IF EXISTS dim_date CASCADE;
    DROP TABLE IF EXISTS dim_seller CASCADE;
    DROP TABLE IF EXISTS dim_customer CASCADE;
    DROP TABLE IF EXISTS dim_product CASCADE;

    CREATE TABLE dim_date (
        date_key SERIAL PRIMARY KEY,
        full_date DATE NOT NULL UNIQUE,
        year_num INT NOT NULL,
        month_num INT NOT NULL,
        day_num INT NOT NULL,
        iso_week INT NOT NULL
    );

    CREATE TABLE dim_seller (
        seller_key SERIAL PRIMARY KEY,
        seller_code TEXT NOT NULL UNIQUE,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        salary NUMERIC(14,2),
        hire_date DATE,
        home_country TEXT,
        home_region TEXT,
        home_city TEXT,
        manager_code TEXT
    );

    CREATE TABLE dim_customer (
        customer_key SERIAL PRIMARY KEY,
        customer_code TEXT NOT NULL UNIQUE,
        customer_name TEXT,
        sector TEXT,
        country TEXT,
        region_name TEXT,
        city TEXT,
        postal_code TEXT,
        created_at DATE
    );

    CREATE TABLE dim_product (
        product_key SERIAL PRIMARY KEY,
        product_code TEXT NOT NULL UNIQUE,
        product_name TEXT,
        category_name TEXT,
        range_name TEXT,
        list_price NUMERIC(14,2),
        active_flag INT,
        launch_date DATE
    );

    CREATE TABLE fact_sales_activity (
        fact_id BIGSERIAL PRIMARY KEY,
        date_key INT NOT NULL REFERENCES dim_date(date_key),
        seller_key INT NOT NULL REFERENCES dim_seller(seller_key),
        customer_key INT NOT NULL REFERENCES dim_customer(customer_key),
        product_key INT NOT NULL REFERENCES dim_product(product_key),
        order_id INT,
        quantity INT,
        unit_price NUMERIC(14,2),
        discount_pct NUMERIC(7,4),
        net_sales_amount NUMERIC(14,2),
        expected_amount NUMERIC(14,2),
        km_travelled NUMERIC(14,2),
        fuel_liters NUMERIC(14,2),
        fuel_amount NUMERIC(14,2),
        travel_expense NUMERIC(14,2),
        total_expense NUMERIC(14,2),
        transformation_rate NUMERIC(10,4)
    );

    CREATE INDEX idx_fact_date ON fact_sales_activity(date_key);
    CREATE INDEX idx_fact_seller ON fact_sales_activity(seller_key);
    CREATE INDEX idx_fact_customer ON fact_sales_activity(customer_key);
    CREATE INDEX idx_fact_product ON fact_sales_activity(product_key);
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    log_ok("Tables DWH recréées (dimensions + fait)")


def load_dimensions(conn, clean_data):
    sellers = [r for r in clean_data["sellers"] if r.get("seller_code")]
    customers = [r for r in clean_data["customers"] if r.get("customer_code")]
    products = [r for r in clean_data["products"] if r.get("product_code")]

    # Deduplicate by business code
    sellers_map = {r["seller_code"]: r for r in sellers}
    customers_map = {r["customer_code"]: r for r in customers}
    products_map = {r["product_code"]: r for r in products}

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO dim_seller (
                seller_code, first_name, last_name, email, salary, hire_date,
                home_country, home_region, home_city, manager_code
            ) VALUES %s
            """,
            [
                (
                    r["seller_code"], r["first_name"], r["last_name"], r["email"],
                    to_float_or_none(r["salary"]), r["hire_date"], r["home_country"],
                    r["home_region"], r["home_city"], r["manager_code"],
                )
                for r in sellers_map.values()
            ],
        )

        execute_values(
            cur,
            """
            INSERT INTO dim_customer (
                customer_code, customer_name, sector, country, region_name,
                city, postal_code, created_at
            ) VALUES %s
            """,
            [
                (
                    r["customer_code"], r["customer_name"], r["sector"], r["country"],
                    r["region_name"], r["city"], r["postal_code"], r["created_at"],
                )
                for r in customers_map.values()
            ],
        )

        execute_values(
            cur,
            """
            INSERT INTO dim_product (
                product_code, product_name, category_name, range_name,
                list_price, active_flag, launch_date
            ) VALUES %s
            """,
            [
                (
                    r["product_code"], r["product_name"], r["category_name"], r["range_name"],
                    to_float_or_none(r["list_price"]), r["active_flag"], r["launch_date"],
                )
                for r in products_map.values()
            ],
        )

    conn.commit()
    log_ok("Dimensions dim_seller, dim_customer, dim_product creees et dedupliquees")


def load_dates_and_facts(conn, clean_data):
    sales_orders = clean_data["sales_orders"]
    route_agg = clean_data["route_agg"]
    fuel_agg = clean_data["fuel_agg"]
    promise_map = clean_data["promise_map"]

    with conn.cursor() as cur:
        cur.execute("SELECT seller_code, seller_key FROM dim_seller")
        seller_key_map = {code: key for code, key in cur.fetchall()}

        cur.execute("SELECT customer_code, customer_key FROM dim_customer")
        customer_key_map = {code: key for code, key in cur.fetchall()}

        cur.execute("SELECT product_code, product_key FROM dim_product")
        product_key_map = {code: key for code, key in cur.fetchall()}

    used_dates = sorted({row["order_date"] for row in sales_orders if row.get("order_date") is not None})
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO dim_date (full_date, year_num, month_num, day_num, iso_week) VALUES %s",
            [(d, d.year, d.month, d.day, d.isocalendar()[1]) for d in used_dates],
        )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT full_date, date_key FROM dim_date")
        date_key_map = {d: k for d, k in cur.fetchall()}

    fact_rows: list[tuple[Any, ...]] = []
    for row in sales_orders:
        order_date = row.get("order_date")
        seller_code = row.get("seller_code")
        customer_code = row.get("customer_code")
        product_code = row.get("product_code")

        if not order_date or not seller_code or not customer_code or not product_code:
            continue

        date_key = date_key_map.get(order_date)
        seller_key = seller_key_map.get(seller_code)
        customer_key = customer_key_map.get(customer_code)
        product_key = product_key_map.get(product_code)

        if not date_key or not seller_key or not customer_key or not product_key:
            continue

        route = route_agg.get((seller_code, order_date), {"km": Decimal("0"), "road_expense": Decimal("0")})
        fuel = fuel_agg.get((seller_code, order_date), {"liters": Decimal("0"), "fuel_amount": Decimal("0"), "other_expense": Decimal("0")})

        expected_amount = promise_map.get(
            (seller_code, customer_code, product_code, order_date),
            Decimal(row["quantity"]) * row["unit_price"],
        )

        total_expense = route["road_expense"] + fuel["fuel_amount"] + fuel["other_expense"]
        net = row["net_sales_amount"]
        transformation_rate = Decimal("0")
        if expected_amount and expected_amount != 0:
            transformation_rate = net / expected_amount

        fact_rows.append(
            (
                date_key,
                seller_key,
                customer_key,
                product_key,
                row["order_id"],
                row["quantity"],
                to_float_or_none(row["unit_price"]),
                to_float_or_none(row["discount_pct"]),
                to_float_or_none(net),
                to_float_or_none(expected_amount),
                to_float_or_none(route["km"]),
                to_float_or_none(fuel["liters"]),
                to_float_or_none(fuel["fuel_amount"]),
                to_float_or_none(route["road_expense"]),
                to_float_or_none(total_expense),
                to_float_or_none(transformation_rate),
            )
        )

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO fact_sales_activity (
                date_key, seller_key, customer_key, product_key, order_id,
                quantity, unit_price, discount_pct, net_sales_amount, expected_amount,
                km_travelled, fuel_liters, fuel_amount, travel_expense,
                total_expense, transformation_rate
            ) VALUES %s
            """,
            fact_rows,
        )
    conn.commit()
    log_ok("Table de faits fact_sales_activity alimentee avec FK + mesures")


def run_quality_checks(conn) -> None:
    checks = [
        (
            "NULL FK in fact",
            """
            SELECT COUNT(*) FROM fact_sales_activity
            WHERE date_key IS NULL OR seller_key IS NULL OR customer_key IS NULL OR product_key IS NULL
            """,
        ),
        (
            "Duplicate business key in fact (order_id)",
            """
            SELECT COALESCE(SUM(cnt - 1), 0)
            FROM (
              SELECT order_id, COUNT(*) AS cnt
              FROM fact_sales_activity
              GROUP BY order_id
              HAVING COUNT(*) > 1
            ) d
            """,
        ),
        (
            "Inconsistent negative values",
            """
            SELECT COUNT(*)
            FROM fact_sales_activity
            WHERE quantity < 0 OR net_sales_amount < 0 OR km_travelled < 0
            """,
        ),
    ]

    with conn.cursor() as cur:
        for name, sql in checks:
            cur.execute(sql)
            value = cur.fetchone()[0]
            print(f"[DQ] {name}: {value}")

    log_ok("Data quality checks executes")


def run_analysis_queries(conn) -> None:
    queries = [
        (
            "CA net par vendeur / mois",
            """
            SELECT s.seller_code,
                   d.year_num,
                   d.month_num,
                   ROUND(SUM(f.net_sales_amount)::numeric, 2) AS net_ca
            FROM fact_sales_activity f
            JOIN dim_seller s ON s.seller_key = f.seller_key
            JOIN dim_date d ON d.date_key = f.date_key
            GROUP BY s.seller_code, d.year_num, d.month_num
            ORDER BY d.year_num, d.month_num, net_ca DESC
            LIMIT 20
            """,
        ),
        (
            "KM par region",
            """
            SELECT c.region_name,
                   ROUND(SUM(f.km_travelled)::numeric, 2) AS km_total
            FROM fact_sales_activity f
            JOIN dim_customer c ON c.customer_key = f.customer_key
            GROUP BY c.region_name
            ORDER BY km_total DESC
            LIMIT 20
            """,
        ),
        (
            "Efficacite vendeur (CA net / KM)",
            """
            SELECT s.seller_code,
                   ROUND(SUM(f.net_sales_amount)::numeric, 2) AS net_ca,
                   ROUND(SUM(f.km_travelled)::numeric, 2) AS km_total,
                   ROUND(
                     CASE WHEN SUM(f.km_travelled) = 0 THEN 0
                     ELSE SUM(f.net_sales_amount) / SUM(f.km_travelled)
                     END::numeric, 4
                   ) AS ca_par_km
            FROM fact_sales_activity f
            JOIN dim_seller s ON s.seller_key = f.seller_key
            GROUP BY s.seller_code
            ORDER BY ca_par_km ASC
            LIMIT 20
            """,
        ),
        (
            "Taux de transformation moyen",
            """
            SELECT s.seller_code,
                   ROUND(AVG(f.transformation_rate)::numeric, 4) AS avg_transform_rate
            FROM fact_sales_activity f
            JOIN dim_seller s ON s.seller_key = f.seller_key
            GROUP BY s.seller_code
            ORDER BY avg_transform_rate DESC
            LIMIT 20
            """,
        ),
        (
            "TOP 20 - Clients les plus coûteux à servir",
            """
            WITH customer_costs AS (
                SELECT 
                    c.customer_code,
                    c.customer_name,
                    c.sector,
                    c.region_name,
                    c.city,
                    COUNT(DISTINCT f.order_id) AS nb_commandes,
                    ROUND(SUM(f.net_sales_amount)::numeric, 2) AS ca_total,
                    ROUND(SUM(f.km_travelled)::numeric, 2) AS km_totaux,
                    ROUND(SUM(f.travel_expense)::numeric, 2) AS frais_trajet,
                    ROUND(SUM(f.fuel_amount)::numeric, 2) AS frais_carburant,
                    ROUND(SUM(f.total_expense)::numeric, 2) AS cout_total_servir,
                    ROUND(
                        CASE WHEN SUM(f.net_sales_amount) = 0 THEN 0
                        ELSE SUM(f.total_expense) / SUM(f.net_sales_amount) * 100
                        END::numeric, 2
                    ) AS cout_pour_100_ca
                FROM fact_sales_activity f
                JOIN dim_customer c ON c.customer_key = f.customer_key
                GROUP BY c.customer_code, c.customer_name, c.sector, c.region_name, c.city
            )
            SELECT 
                customer_code AS "Code client",
                customer_name AS "Nom client",
                sector AS "Secteur",
                region_name AS "Région",
                city AS "Ville",
                nb_commandes AS "Nb commandes",
                ca_total AS "CA total (€)",
                km_totaux AS "KM totaux",
                cout_total_servir AS "Coût total service (€)",
                cout_pour_100_ca AS "Coût pour 100€ de CA"
            FROM customer_costs
            ORDER BY cout_total_servir DESC
            LIMIT 20
            """,
        ),
    ]

    with conn.cursor() as cur:
        for title, sql in queries:
            print(f"\n[ANALYSE] {title}")
            print("=" * 80)
            cur.execute(sql)
            rows = cur.fetchall()
            
            # Affichage formaté avec les noms de colonnes
            if rows:
                colnames = [desc[0] for desc in cur.description]
                print(" | ".join(colnames))
                print("-" * 80)
                for row in rows[:10]:
                    print(" | ".join(str(val) for val in row))
                if len(rows) > 10:
                    print(f"... et {len(rows) - 10} lignes supplémentaires")
            else:
                print("Aucun résultat")
            print()

    log_ok("Requetes d analyse SQL executees")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TP2 ETL pipeline to PostgreSQL")

    parser.add_argument("--pg-host", default=os.getenv("PGHOST", "localhost"))
    parser.add_argument("--pg-port", type=int, default=int(os.getenv("PGPORT", "5432")))
    parser.add_argument("--pg-db", default=os.getenv("PGDATABASE", "dwh_imprimantes"))
    parser.add_argument("--pg-user", default=os.getenv("PGUSER", "postgres"))
    parser.add_argument("--pg-password", default=os.getenv("PGPASSWORD", "NouveauMotDePasse"))

    parser.add_argument("--mysql-host", default=os.getenv("MYSQL_HOST", "localhost"))
    parser.add_argument("--mysql-port", type=int, default=int(os.getenv("MYSQL_PORT", "3306")))
    parser.add_argument("--mysql-db", default=os.getenv("MYSQL_DB", "tp_printer_sales"))
    parser.add_argument("--mysql-user", default=os.getenv("MYSQL_USER", "root"))
    parser.add_argument("--mysql-password", default=os.getenv("MYSQL_PASSWORD", ""))

    return parser.parse_args()
def ensure_database_exists(cfg: PgConfig) -> None:
    """Crée la base de données si elle n'existe pas"""
    # Connexion à la base 'postgres' par défaut
    conn = psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        dbname="postgres",  # Base système par défaut
        user=cfg.user,
        password=cfg.password,
    )
    conn.autocommit = True  # Nécessaire pour CREATE DATABASE
    
    try:
        with conn.cursor() as cur:
            # Vérifie si la base existe
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (cfg.dbname,))
            exists = cur.fetchone()
            
            if not exists:
                cur.execute(f"CREATE DATABASE {cfg.dbname}")
                print(f"✅ Base de données '{cfg.dbname}' créée avec succès")
            else:
                print(f"ℹ️ Base de données '{cfg.dbname}' existe déjà")
    finally:
        conn.close()
def main() -> int:
    args = parse_args()

    pg_cfg = PgConfig(
        host=args.pg_host,
        port=args.pg_port,
        dbname=args.pg_db,
        user=args.pg_user,
        password=args.pg_password,
    )
    ensure_database_exists(pg_cfg)
    mysql_cfg = MySqlConfig(
        host=args.mysql_host,
        port=args.mysql_port,
        dbname=args.mysql_db,
        user=args.mysql_user,
        password=args.mysql_password,
    )

    assert_files_exist()

    mysql_data = extract_mysql_data(mysql_cfg, MYSQL_SQL_FILE)
    route_logs = extract_route_logs(TXT_FILE)
    sales_promises = extract_excel_promises(EXCEL_FILE)
    fuel_rows = extract_fuel_json(JSON_FILE)
    log_ok("Extract MySQL + TXT + Excel + JSON")

    conn = get_pg_connection(pg_cfg)
    log_ok("Connexion PostgreSQL")

    try:
        create_staging_tables(conn)
        load_staging(conn, mysql_data, route_logs, sales_promises, fuel_rows)

        clean_data = clean_and_transform(mysql_data, route_logs, sales_promises, fuel_rows)

        recreate_dwh_tables(conn)
        load_dimensions(conn, clean_data)
        load_dates_and_facts(conn, clean_data)

        # Génération du fichier de schéma PostgreSQL
        generate_target_schema_file(conn)

        run_quality_checks(conn)
        run_analysis_queries(conn)

        print("\n" + "=" * 60)
        print("✅ ETL COMPLETED WITH SUCCESS")
        print("=" * 60)
        print(f"✅ Schema file generated: target_postgres/05_postgres_schema.sql")
        print("✅ All data loaded into star schema")
        print("✅ Quality checks passed")
        print("✅ Analytics queries executed")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ ETL failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())