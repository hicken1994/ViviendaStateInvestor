import sqlite3
import random

import pandas as pd
from datetime import datetime
from utils.scoring import compute_investment_metrics

DB_PATH = "real_estate.db"


# ========================
# 🔌 CONEXIÓN
# ========================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ========================
# 🖼️ HELPERS
# ========================

BARRIO_IMAGES = {
    "Salamanca": "https://images.unsplash.com/photo-1505691938895-1758d7feb511",
    "Chamberí": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2",
    "Centro": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
    "Tetuán": "https://images.unsplash.com/photo-1493809842364-78817add7ffb",
    "Carabanchel": "https://images.unsplash.com/photo-1484154218962-a197022b5858",
    "Usera": "https://images.unsplash.com/photo-1507089947368-19c1da9775ae",
    "Retiro": "https://images.unsplash.com/photo-1508609349937-5ec4ae374ebf",
    "Arganzuela": "https://images.unsplash.com/photo-1523217582562-09d0def993a6",
    "Latina": "https://images.unsplash.com/photo-1560185008-5f44982808b6",
    "Moncloa": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688",
    "Fuencarral": "https://images.unsplash.com/photo-1554995207-c18c203602cb",
    "Hortaleza": "https://images.unsplash.com/photo-1505691723518-36a5ac3b2d52",
    "Chamartín": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750",
    "Villaverde": "https://images.unsplash.com/photo-1570129477492-45c003edd2be",
    "Moratalaz": "https://images.unsplash.com/photo-1487014679447-9f8336841d58",
    "Vicálvaro": "https://images.unsplash.com/photo-1501870190083-5a25e7a1e072",
    "San Blas": "https://images.unsplash.com/photo-1449844908441-8829872d2607",
    "Barajas": "https://images.unsplash.com/photo-1501183638710-841dd1904471",
    "Puente de Vallecas": "https://images.unsplash.com/photo-1519710164239-da123dc03ef4",
    "Villa de Vallecas": "https://images.unsplash.com/photo-1507086182423-c8b20045fd2a",
    "Ciudad Lineal": "https://images.unsplash.com/photo-1560448075-bb485b067938",
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1560448075-bb485b067938"


def add_images(df):
    df["image_url"] = df.apply(
        lambda row: BARRIO_IMAGES.get(row.get("barrio", ""), DEFAULT_IMAGE),
        axis=1
    )
    return df


# ========================
# 📊 CONSULTAS PRINCIPALES
# ========================

def get_top_opportunities(limit=50):
    conn = get_connection()
    try:
        df = pd.read_sql("""
            SELECT *
            FROM vista_oportunidades_ai
            ORDER BY opportunity_score DESC
            LIMIT ?
        """, conn, params=(limit,))
    finally:
        conn.close()

    metrics = df.apply(
        compute_investment_metrics,
        axis=1,
        result_type="expand"
    )

    cols_to_remove = [
        "score_total", "score_descuento", "score_precio",
        "score_liquidez", "score_tamano", "score_ruido",
        "rentabilidad_estimada", "decision"
    ]
    df = df.drop(columns=[c for c in cols_to_remove if c in df.columns], errors="ignore")
    df = pd.concat([df, metrics], axis=1)

    return df


def get_property(prop_id):
    conn = get_connection()
    try:
        df = pd.read_sql("""
            SELECT *
            FROM vista_oportunidades_ai
            WHERE propiedad_id = ?
        """, conn, params=(prop_id,))
    finally:
        conn.close()

    metrics = df.apply(
        compute_investment_metrics,
        axis=1,
        result_type="expand"
    )
    df = pd.concat([df, metrics], axis=1)
    df = add_images(df)
    return df


def get_barrios():
    conn = get_connection()
    try:
        return pd.read_sql("""
            SELECT *
            FROM radar_oportunidades
            ORDER BY opportunity_index DESC
        """, conn)
    finally:
        conn.close()


def get_map_data():
    conn = get_connection()
    try:
        return pd.read_sql("""
            SELECT distrito, latitud, longitud
            FROM mapas_distritos
        """, conn)
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
# 🎲 SIMULACIÓN DE MERCADO
# ========================

def simulate_market(df):
    """Simula movimientos de mercado y genera eventos detectables."""

    df = df.copy()
    generated_events = []

    for i in df.index:
        prop_id = str(df.at[i, "id"] if "id" in df.columns else df.at[i, "precio_total"])

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
