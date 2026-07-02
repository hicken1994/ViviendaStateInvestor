-- v1: Core data tables for Vivienda AI
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.oportunidades (
    propiedad_id INTEGER,
    barrio TEXT,
    metros REAL,
    precio_m2 REAL,
    precio_m2_barrio REAL,
    diferencia_pct REAL,
    opportunity_score REAL,
    precio_total REAL,
    score_descuento REAL,
    score_precio REAL,
    score_liquidez REAL,
    score_tamano REAL,
    rentabilidad_estimada REAL,
    decision TEXT,
    is_premium INTEGER DEFAULT 0,
    -- extra metadata from source
    source TEXT,
    source_id TEXT,
    rooms INTEGER,
    bathrooms INTEGER,
    has_lift INTEGER,
    has_terrace INTEGER,
    construction_year INTEGER,
    latitude REAL,
    longitude REAL
);

CREATE INDEX IF NOT EXISTS idx_oportunidades_barrio ON public.oportunidades(barrio);
CREATE INDEX IF NOT EXISTS idx_oportunidades_precio ON public.oportunidades(precio_total);

-- Tablas auxiliares
CREATE TABLE IF NOT EXISTS public.barrio_rent (
    barrio TEXT PRIMARY KEY,
    precio_m2_alquiler REAL
);

CREATE TABLE IF NOT EXISTS public.mapas_distritos (
    distrito TEXT PRIMARY KEY,
    latitud REAL,
    longitud REAL
);

CREATE TABLE IF NOT EXISTS public.distrito_mapping (
    distrito_raw TEXT,
    distrito_mapa TEXT
);

CREATE TABLE IF NOT EXISTS public.radar_oportunidades (
    barrio TEXT PRIMARY KEY,
    oportunidades INTEGER,
    descuento_medio REAL,
    precio_m2_medio REAL,
    opportunity_index REAL
);

CREATE TABLE IF NOT EXISTS public.property_history (
    property_id TEXT,
    precio_total REAL,
    rentabilidad REAL,
    fecha TIMESTAMP DEFAULT NOW()
);
