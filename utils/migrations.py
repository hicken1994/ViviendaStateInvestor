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


@_migration(1, "Agregar columna extra a events, indice en property_id")
def migration_001(conn: sqlite3.Connection):
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
