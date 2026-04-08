import sqlite3
import random

import pandas as pd
from datetime import datetime
from utils.scoring import compute_investment_metrics

DB_PATH = "real_estate.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_top_opportunities(limit=50):
    conn = get_connection()
    try:
        query = """
        SELECT *
        FROM vista_oportunidades_ai
        ORDER BY opportunity_score DESC
        LIMIT ?
        """

        df = pd.read_sql(query, conn, params=(limit,))
    finally:
        conn.close()

    # ========================
    # APPLY DECISION ENGINE
    # ========================
    metrics = df.apply(
        compute_investment_metrics,
        axis=1,
        result_type="expand"
    )

    # Eliminar columnas si ya existen
    cols_to_remove = [
        "score_total",
        "score_descuento",
        "score_precio",
        "score_liquidez",
        "score_tamano",
        "score_ruido",
        "rentabilidad_estimada",
        "decision"
    ]

    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns], errors="ignore")

    # Añadir nuevas columnas de métricas
    df = pd.concat([df, metrics], axis=1)

    return df


def get_barrios():
    conn = get_connection()
    try:
        query = """
        SELECT *
        FROM radar_oportunidades
        ORDER BY opportunity_index DESC
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def get_property(prop_id):
    conn = get_connection()
    try:
        query = """
        SELECT *
        FROM vista_oportunidades_ai
        WHERE propiedad_id = ?
        """

        df = pd.read_sql(query, conn, params=(prop_id,))
    finally:
        conn.close()

    metrics = df.apply(
        compute_investment_metrics,
        axis=1,
        result_type="expand"
    )

    df = pd.concat([df, metrics], axis=1)

    return df


def get_map_data():
    conn = get_connection()
    try:
        query = """
        SELECT distrito, latitud, longitud
        FROM mapas_distritos
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


# ========================
# 📸 SNAPSHOT HISTÓRICO
# ========================

def ensure_history_table():
    conn = get_connection()
    try:
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
    finally:
        conn.close()


def detect_price_drop():
    conn = get_connection()
    try:
        query = """
        SELECT property_id,
               MAX(precio_total) as old_price,
               MIN(precio_total) as new_price
        FROM property_history
        GROUP BY property_id
        HAVING old_price > new_price
        """

        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    df["drop_pct"] = round(
        (df["old_price"] - df["new_price"]) / df["old_price"] * 100, 2
    )

    return df[df["drop_pct"] > 5]


def save_snapshot(df):
    ensure_history_table()

    conn = get_connection()
    try:
        cursor = conn.cursor()

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO property_history (property_id, precio_total, rentabilidad, fecha)
                VALUES (?, ?, ?, ?)
            """, (
                str(row.get("id") or row.get("url") or row.get("precio_total")),
                round(row.get("precio_total", 0), 2),
                round(row.get("rentabilidad_estimada", 0), 2),
                datetime.now()
            ))

        conn.commit()
    finally:
        conn.close()


# ========================
# 🎲 SIMULACIÓN DE MERCADO
# ========================

def simulate_market(df):

    df = df.copy()

    for i in df.index:

        # Simular bajada de precio (20% probabilidad)
        if random.random() < 0.2:
            drop = random.uniform(0.95, 0.99)
            df.at[i, "precio_total"] = round(df.at[i, "precio_total"] * drop, 2)

        # Aumentar días
        dias_actual = int(df.at[i, "dias"]) if "dias" in df.columns and pd.notna(df.at[i, "dias"]) else 0
        df.at[i, "dias"] = dias_actual + random.randint(1, 3)

        # Ajustar rentabilidad ligeramente
        if "rentabilidad_estimada" in df.columns and pd.notna(df.at[i, "rentabilidad_estimada"]):
            df.at[i, "rentabilidad_estimada"] = round(
                df.at[i, "rentabilidad_estimada"] * random.uniform(0.98, 1.02), 2
            )

    return df
