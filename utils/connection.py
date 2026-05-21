"""
Context manager para conexiones SQLite con WAL mode y manejo centralizado de errores.
"""

import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

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
    try:
        yield conn
    finally:
        conn.close()


def db_error(msg: str = "Error de base de datos") -> Exception:
    """Crea una excepcion con contexto."""
    logger.error(msg)
    return RuntimeError(msg)
