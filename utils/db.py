import json
import sqlite3
import random

import pandas as pd
from datetime import datetime, timedelta

from utils.services import get_top_opportunities, get_barrios, get_map_data

DB_PATH = "real_estate.db"


# ========================
# 🔌 CONEXIÓN
# ========================

def get_connection():
    return sqlite3.connect(DB_PATH)


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


def detect_price_drop():
    conn = get_connection()
    try:
        df = pd.read_sql("""
            SELECT property_id,
                   MAX(precio_total) as old_price,
                   MIN(precio_total) as new_price
            FROM property_history
            GROUP BY property_id
            HAVING old_price > new_price
        """, conn)
    finally:
        conn.close()

    df["drop_pct"] = round(
        (df["old_price"] - df["new_price"]) / df["old_price"] * 100, 2
    )
    return df[df["drop_pct"] > 5]


# ========================
# 📡 EVENTOS DE MERCADO
# ========================

def ensure_events_table():
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id TEXT,
                event_type TEXT,
                old_value REAL,
                new_value REAL,
                timestamp TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def insert_event(event):
    ensure_events_table()
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO events (property_id, event_type, old_value, new_value, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event["property_id"],
            event["type"],
            event.get("old"),
            event.get("new"),
            datetime.now()
        ))
        conn.commit()
    finally:
        conn.close()


def get_recent_events(limit=20):
    ensure_events_table()
    conn = get_connection()
    try:
        return pd.read_sql("""
            SELECT * FROM events
            ORDER BY timestamp DESC
            LIMIT ?
        """, conn, params=(limit,))
    finally:
        conn.close()


# ========================
# 📊 PROMEDIO POR BARRIO (para gráficos radar)
# ========================


def get_barrio_avg_scores(barrio: str, perfil: dict) -> dict:
    """Promedio de scores con perfil para propiedades de un barrio.

    Args:
        barrio: Nombre del barrio a consultar.
        perfil: Dict de perfil (get_perfil).

    Returns:
        Dict con score_total, score_descuento, score_precio,
        score_liquidez, score_tamano, score_ruido promediados.
    """
    from utils.profiles import compute_score_with_profile

    conn = get_connection()
    try:
        df = pd.read_sql("""
            SELECT *
            FROM vista_oportunidades_ai
            WHERE barrio = ?
        """, conn, params=(barrio,))
    finally:
        conn.close()

    if df.empty:
        return {}

    profile_metrics = df.apply(
        lambda row: compute_score_with_profile(row, perfil),
        axis=1,
        result_type="expand",
    )

    score_cols = [
        "score_total", "score_descuento", "score_precio",
        "score_liquidez", "score_tamano", "score_ruido",
    ]
    available = [c for c in score_cols if c in profile_metrics.columns]

    averages = profile_metrics[available].mean().to_dict()
    return {k: round(v, 2) for k, v in averages.items()}


# ========================
# 🎲 SIMULACIÓN DE MERCADO
# ========================

def simulate_market(df):
    """Simula movimientos de mercado y genera eventos detectables."""

    df = df.copy()
    generated_events = []

    for i in df.index:
        prop_id = str(
            df.at[i, "propiedad_id"] if "propiedad_id" in df.columns
            else df.at[i, "id"] if "id" in df.columns
            else df.at[i, "precio_total"]
        )

        # Simular bajada de precio (20% probabilidad)
        if random.random() < 0.2:
            old_price = df.at[i, "precio_total"]
            drop = random.uniform(0.95, 0.99)
            new_price = round(old_price * drop, 2)
            df.at[i, "precio_total"] = new_price

            generated_events.append({
                "property_id": prop_id,
                "type": "price_drop",
                "old": round(old_price, 2),
                "new": new_price,
            })

        # Flash drop: baja temporal mas agresiva (8-15%) con expiracion
        if random.random() < 0.08:
            old_price = df.at[i, "precio_total"]
            drop = random.uniform(0.85, 0.92)
            flash_price = round(old_price * drop, 2)
            expires_at = (datetime.now() + timedelta(hours=random.randint(24, 72))).isoformat()

            df.at[i, "precio_total"] = flash_price
            df.at[i, "flash_price_original"] = old_price
            df.at[i, "flash_expires"] = expires_at

            generated_events.append({
                "property_id": prop_id,
                "type": "flash_drop",
                "old": round(old_price, 2),
                "new": flash_price,
                "extra": json.dumps({"expires": expires_at, "drop_pct": round((1 - drop) * 100, 1)}),
            })

        # Aumentar días
        dias_actual = int(df.at[i, "dias"]) if "dias" in df.columns and pd.notna(df.at[i, "dias"]) else 0
        df.at[i, "dias"] = dias_actual + random.randint(1, 3)

        # Ajustar rentabilidad ligeramente
        if "rentabilidad_estimada" in df.columns and pd.notna(df.at[i, "rentabilidad_estimada"]):
            old_rent = df.at[i, "rentabilidad_estimada"]
            factor = random.uniform(0.98, 1.02)
            new_rent = round(old_rent * factor, 2)
            df.at[i, "rentabilidad_estimada"] = new_rent

            if new_rent > old_rent * 1.01:
                generated_events.append({
                    "property_id": prop_id,
                    "type": "yield_up",
                    "old": round(old_rent, 2),
                    "new": new_rent,
                })

    # Persistir eventos generados
    for event in generated_events:
        try:
            insert_event(event)
        except Exception:
            pass

    return df


# ========================
# 🛠️ ACTUALIZACIÓN DE ESQUEMA
# ========================


def add_is_premium_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(oportunidades)")
    columns = [row[1] for row in cursor.fetchall()]

    if "is_premium" not in columns:
        cursor.execute("""
            ALTER TABLE oportunidades
            ADD COLUMN is_premium INTEGER DEFAULT 0
        """)
        conn.commit()

    conn.close()

# Call the function to ensure the column is added and updated
