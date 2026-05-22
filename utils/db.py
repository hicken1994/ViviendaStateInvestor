import json
import logging
import random

from datetime import datetime, timedelta

from utils.connection import get_conn, DB_PATH
from utils.services import get_top_opportunities, get_barrio_avg_scores

logger = logging.getLogger(__name__)


# ========================
# 🛠️ ESQUEMA (legacy)
# ========================

def add_is_premium_column():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute("PRAGMA table_info(oportunidades)")
        columns = [row[1] for row in cursor.fetchall()]
        if "is_premium" not in columns:
            conn.execute("ALTER TABLE oportunidades ADD COLUMN is_premium INTEGER DEFAULT 0")
            conn.commit()
    finally:
        conn.close()


# ========================
# 📡 EVENTOS DE MERCADO
# ========================

def insert_event(event):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO events (property_id, event_type, old_value, new_value, extra, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event["property_id"],
            event["type"],
            event.get("old"),
            event.get("new"),
            event.get("extra"),
            datetime.now(),
        ))


def get_recent_events(limit=20):
    import pandas as pd
    with get_conn() as conn:
        return pd.read_sql("""
            SELECT *
            FROM events
            ORDER BY timestamp DESC
            LIMIT ?
        """, conn, params=(limit,))


# ========================
# 🎲 SIMULACIÓN DE MERCADO
# ========================

def simulate_market(df):
    import pandas as pd

    df = df.copy()
    generated_events = []

    for i in df.index:
        prop_id = str(
            df.at[i, "propiedad_id"] if "propiedad_id" in df.columns
            else df.at[i, "id"] if "id" in df.columns
            else df.at[i, "precio_total"]
        )

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

        key_dias = "dias" if "dias" in df.columns else None
        if key_dias:
            dias_actual = int(df.at[i, key_dias]) if pd.notna(df.at[i, key_dias]) else 0
            df.at[i, key_dias] = dias_actual + random.randint(1, 3)

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

    errors = 0
    for event in generated_events:
        try:
            insert_event(event)
        except Exception as e:
            errors += 1
            logger.warning("Error al insertar evento %s: %s", event.get("type"), e)

    logger.info(
        "Simulacion: %d eventos (%d errores)",
        len(generated_events), errors,
    )
    return df
