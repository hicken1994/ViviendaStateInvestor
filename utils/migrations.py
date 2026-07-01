"""
Sistema de migraciones secuenciales para SQLite.

Cada migracion es una funcion numerada que se ejecuta en orden.
El schema version se persiste en la tabla `_schema_version`.
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = "real_estate.db"

MIGRATIONS = []


def _migration(version: int, description: str):
    """Decorador que registra una migracion."""
    def wrapper(func):
        MIGRATIONS.append((version, description, func))
        return func
    return wrapper


def _ensure_version_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def get_current_version() -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_version_table(conn)
        row = conn.execute("SELECT MAX(version) FROM _schema_version").fetchone()
        return row[0] if row and row[0] else 0
    finally:
        conn.close()


def run_migrations():
    """Ejecuta todas las migraciones pendientes en orden."""
    current = get_current_version()
    pending = sorted([m for m in MIGRATIONS if m[0] > current], key=lambda x: x[0])

    if not pending:
        logger.info("Schema en version %d, sin migraciones pendientes", current)
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_version_table(conn)
        for version, desc, func in pending:
            logger.info("Migrando a v%d: %s", version, desc)
            func(conn)
            conn.execute(
                "INSERT INTO _schema_version (version) VALUES (?)",
                (version,),
            )
            conn.commit()
            logger.info("Migracion v%d aplicada", version)
    finally:
        conn.close()


# ========================
# MIGRACIONES
# ========================


@_migration(1, "Crear tabla events si no existe, agregar columna extra")
def migration_001(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT,
            event_type TEXT,
            old_value REAL,
            new_value REAL,
            extra TEXT,
            timestamp TIMESTAMP
        )
    """)
    cursor = conn.execute("PRAGMA table_info(events)")
    cols = [row[1] for row in cursor.fetchall()]
    if "extra" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN extra TEXT")


@_migration(2, "Indices para consultas frecuentes")
def migration_002(conn: sqlite3.Connection):
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_type
        ON events(event_type)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_timestamp
        ON events(timestamp DESC)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_property
        ON events(property_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_oportunidades_barrio
        ON oportunidades(barrio)
    """)


@_migration(3, "Habilitar WAL mode y configuracion")
def migration_003(conn: sqlite3.Connection):
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-8000")
    conn.execute("PRAGMA temp_store=MEMORY")


@_migration(4, "Crear tabla events si no existe (schema completo)")
def migration_004(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT,
            event_type TEXT,
            old_value REAL,
            new_value REAL,
            extra TEXT,
            timestamp TIMESTAMP
        )
    """)


@_migration(5, "Crear tablas principales si el seed no las proveyó")
def migration_005(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS oportunidades (
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
            is_premium INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mapas_distritos (
            distrito TEXT PRIMARY KEY,
            latitud REAL,
            longitud REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS distrito_mapping (
            distrito_raw TEXT,
            distrito_mapa TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS radar_oportunidades (
            barrio TEXT PRIMARY KEY,
            oportunidades INTEGER,
            descuento_medio REAL,
            precio_m2_medio REAL,
            opportunity_index REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS property_history (
            property_id TEXT,
            precio_total REAL,
            rentabilidad REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


@_migration(6, "Crear vista_oportunidades_ai si la tabla oportunidades existe")
def migration_006(conn: sqlite3.Connection):
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='oportunidades'"
    )
    if cursor.fetchone() is None:
        return
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view' AND name='vista_oportunidades_ai'"
    )
    if cursor.fetchone() is None:
        conn.execute("""
            CREATE VIEW vista_oportunidades_ai AS
            SELECT
                o.*,
                ROUND(
                    CASE
                        WHEN o.precio_m2_barrio IS NOT NULL
                             AND o.precio_m2_barrio != 0
                        THEN (o.precio_m2_barrio - o.precio_m2) * 100.0 / o.precio_m2_barrio
                        ELSE NULL
                    END
                , 2) AS descuento_pct
            FROM oportunidades o
        """)
