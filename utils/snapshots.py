import sqlite3
from datetime import datetime

DB_PATH = "real_estate.db"


def save_snapshot(df):
    conn = sqlite3.connect(DB_PATH)
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