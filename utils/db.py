import sqlite3
import pandas as pd

def get_connection():
    return sqlite3.connect("real_estate.db")

from utils.scoring import compute_investment_metrics

def get_top_opportunities(limit=50):
    conn = get_connection()

    query = f"""
    SELECT *
    FROM vista_oportunidades_ai
    ORDER BY opportunity_score DESC
    LIMIT {limit}
    """

    df = pd.read_sql(query, conn)

    # ========================
    # APPLY DECISION ENGINE
    # ========================
    metrics = df.apply(
        compute_investment_metrics,
        axis=1,
        result_type="expand"
    )

   # eliminar columnas si ya existen
    cols_to_remove = [
     "score_total",
     "score_descuento",
     "score_precio",
     "score_liquidez",
     "score_tamano",
     "rentabilidad_estimada",
     "decision"
    ]

    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns], errors="ignore")

# ahora añadir nuevas
    df = pd.concat([df, metrics], axis=1)

    return df

def get_barrios():
    conn = get_connection()
    query = """
    SELECT *
    FROM radar_oportunidades
    ORDER BY opportunity_index DESC
    """
    return pd.read_sql(query, conn)

def get_property(prop_id):
    conn = get_connection()
    
    query = f"""
    SELECT *
    FROM vista_oportunidades_ai
    WHERE propiedad_id = {prop_id}
    """
    
    df = pd.read_sql(query, conn)

    # 🔥 ESTO ES LO IMPORTANTE
    metrics = df.apply(
        compute_investment_metrics,
        axis=1,
        result_type="expand"
    )

    df = pd.concat([df, metrics], axis=1)

    return df


def get_map_data():
    conn = get_connection()
    query = """
    SELECT distrito, latitud, longitud
    FROM mapas_distritos
    """
    return pd.read_sql(query, conn)