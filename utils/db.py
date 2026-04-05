import sqlite3
import pandas as pd
from datetime import datetime

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


# ========================
# 📸 SNAPSHOT HISTÓRICO
# ========================

def ensure_history_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS property_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT,
            precio_total REAL,
            rentabilidad REAL,
            fecha TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def detect_price_drop(conn):

    query = """
    SELECT property_id,
           MAX(precio_total) as old_price,
           MIN(precio_total) as new_price
    FROM property_history
    GROUP BY property_id
    HAVING old_price > new_price
    """

    df = pd.read_sql(query, conn)

    df["drop_pct"] = (df["old_price"] - df["new_price"]) / df["old_price"] * 100

    return df[df["drop_pct"] > 5]


def save_snapshot(df):
    ensure_history_table()

    conn = get_connection()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO property_history (property_id, precio_total, rentabilidad, fecha)
            VALUES (?, ?, ?, ?)
        """, (
            str(row.get("id") or row.get("url") or row.get("precio_total")),
            row.get("precio_total"),
            row.get("rentabilidad_estimada"),
            datetime.now()
        ))

    conn.commit()
    conn.close()


# ========================
# 🎲 SIMULACIÓN DE MERCADO
# ========================

import random

def simulate_market(df):

    df = df.copy()

    for i in df.index:

        # Simular bajada de precio (20% probabilidad)
        if random.random() < 0.2:
            drop = random.uniform(0.95, 0.99)
            df.at[i, "precio_total"] *= drop

        # Aumentar días
        dias_actual = df.at[i, "dias"] if "dias" in df.columns else 0
        df.at[i, "dias"] = dias_actual + random.randint(1, 3)

        # Ajustar rentabilidad ligeramente
        if "rentabilidad_estimada" in df.columns:
            df.at[i, "rentabilidad_estimada"] *= random.uniform(0.98, 1.02)

    return df

