-- =====================================================
-- SCHEMA DWH EN ÉTOILE - VENTES IMPRIMANTES
-- Fichier généré automatiquement par le pipeline ETL
-- Date de génération: 2026-04-23 18:43:41
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
