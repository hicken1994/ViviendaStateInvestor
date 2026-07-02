"""
Context manager para conexiones SQLite con WAL mode y manejo centralizado de errores.
"""

import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = "real_estate.db"


@contextmanager
def get_conn():
    """Context manager que garantiza commit/rollback y cierre.

    Uso:
        with get_conn() as conn:
            conn.execute(...)
            conn.commit()
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-8000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Error en operacion de base de datos")
        raise
    finally:
        conn.close()


@contextmanager
def get_conn_ro():
    """Context manager para conexiones de solo lectura (sin commit)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-8000")
    conn.execute("PRAGMA temp_store=MEMORY")
    _ensure_core_tables(conn)
    try:
        yield conn
    finally:
        conn.close()


_CORE_TABLES = """
    CREATE TABLE IF NOT EXISTS oportunidades (
        propiedad_id INTEGER, barrio TEXT, metros REAL,
        precio_m2 REAL, precio_m2_barrio REAL, diferencia_pct REAL,
        opportunity_score REAL, precio_total REAL,
        score_descuento REAL, score_precio REAL,
        score_liquidez REAL, score_tamano REAL,
        rentabilidad_estimada REAL, decision TEXT,
        is_premium INTEGER DEFAULT 0,
        source TEXT
    );
    CREATE TABLE IF NOT EXISTS mapas_distritos (
        distrito TEXT PRIMARY KEY, latitud REAL, longitud REAL
    );
    CREATE TABLE IF NOT EXISTS distrito_mapping (
        distrito_raw TEXT, distrito_mapa TEXT
    );
    CREATE TABLE IF NOT EXISTS radar_oportunidades (
        barrio TEXT PRIMARY KEY, oportunidades INTEGER,
        descuento_medio REAL, precio_m2_medio REAL, opportunity_index REAL
    );
    CREATE TABLE IF NOT EXISTS property_history (
        property_id TEXT, precio_total REAL, rentabilidad REAL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id TEXT,
        event_type TEXT,
        old_value REAL,
        new_value REAL,
        extra TEXT,
        timestamp TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS barrio_rent (
        barrio TEXT,
        precio_m2_alquiler REAL
    );
"""


def _ensure_core_tables(conn: sqlite3.Connection):
    conn.executescript(_CORE_TABLES)


def db_error(msg: str = "Error de base de datos") -> Exception:
    """Crea una excepcion con contexto."""
    logger.error(msg)
    return RuntimeError(msg)
