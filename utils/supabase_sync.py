"""
supabase_sync.py: Pull data from Supabase into local SQLite cache.
Called on app boot to refresh the local DB with real market data.
"""

import logging
import pandas as pd

from utils.connection import get_conn, get_conn_ro

log = logging.getLogger(__name__)

# Tables to sync from Supabase → local SQLite (events is local-only)
SYNC_TABLES = [
    "oportunidades",
    "barrio_rent",
    "radar_oportunidades",
    "distrito_mapping",
    "mapas_distritos",
    "property_history",
]


def _get_supabase():
    import re
    try:
        from supabase import create_client
        with open(".streamlit/secrets.toml") as f:
            content = f.read()
        url = re.search(r'SUPABASE_URL\s*=\s*"([^"]+)"', content).group(1)
        key = re.search(r'SUPABASE_SERVICE_ROLE_KEY\s*=\s*"([^"]+)"', content).group(1)
        return create_client(url, key)
    except Exception as e:
        log.warning("No se pudo conectar a Supabase: %s", e)
        return None


PAGE_SIZE = 1000


def _fetch_table(sb, table: str) -> pd.DataFrame:
    """Fetch all rows from a Supabase table via pagination."""
    try:
        all_data = []
        start = 0
        while True:
            resp = sb.table(table).select("*").range(start, start + PAGE_SIZE - 1).execute()
            if not resp.data:
                break
            all_data.extend(resp.data)
            start += PAGE_SIZE
            if len(resp.data) < PAGE_SIZE:
                break
        if not all_data:
            log.info("  %s: vacia", table)
            return pd.DataFrame()
        df = pd.DataFrame(all_data)
        log.info("  %s: %d filas (%d requests)", table, len(df), (start // PAGE_SIZE))
        return df
    except Exception as e:
        log.warning("  error fetching %s: %s", table, e)
        return pd.DataFrame()


def _clean_for_sqlite(df: pd.DataFrame) -> pd.DataFrame:
    """Convert NaN/NaT/Inf to None for SQLite compatibility."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype in ("float64", "float32"):
            mask = df[col].notna()
            df.loc[~mask, col] = None
        elif df[col].dtype.name in ("Int64", "Int32", "Int8"):
            df[col] = df[col].astype(object).where(df[col].notna(), None)
    return df


def sync_from_supabase():
    """Pull all core tables from Supabase into the local SQLite cache."""
    sb = _get_supabase()
    if sb is None:
        log.info("Supabase no disponible — usando datos locales existentes")
        return

    log.info("=== Sincronizando desde Supabase ===")

    for table in SYNC_TABLES:
        df = _fetch_table(sb, table)
        if df.empty:
            continue
        df = _clean_for_sqlite(df)
        with get_conn() as conn:
            df.to_sql(table, conn, if_exists="replace", index=False)
        log.info("  %s: %d filas sincronizadas", table, len(df))

    with get_conn_ro() as conn:
        cnt = conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()[0]
        log.info("=== Sincronizacion completada: %d propiedades en cache local ===", cnt)


def needs_sync() -> bool:
    """Check if the local DB is empty and needs a sync."""
    try:
        with get_conn_ro() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()[0]
            return cnt == 0
    except Exception:
        return True
