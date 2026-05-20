import sqlite3
import os

DB_PATH = "real_estate.db"

RENT_M2_MAP = {
    "Salamanca": 28,
    "Chamberi": 26,
    "Centro": 25,
    "Chamartin": 24,
    "Tetuán": 22,
    "Tetuan": 22,
    "Ciudad Lineal": 21,
    "Carabanchel": 18,
    "Usera": 17,
    "Puente de Vallecas": 16,
    "Villa de Vallecas": 15,
    "Vicálvaro": 14,
    "Vicalvaro": 14,
    "Moratalaz": 19,
    "Retiro": 27,
    "Arganzuela": 23,
    "Moncloa": 22,
    "Latina": 16,
    "Fuencarral": 18,
    "Hortaleza": 19,
    "Villaverde": 13,
    "Barajas": 20,
    "San Blas": 15,
    "Vallecas": 15,
}


def seed_barrio_rent():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS barrio_rent (
            barrio TEXT PRIMARY KEY,
            precio_m2_alquiler REAL NOT NULL
        )
    """)

    for barrio, precio in RENT_M2_MAP.items():
        cursor.execute("""
            INSERT OR REPLACE INTO barrio_rent (barrio, precio_m2_alquiler)
            VALUES (?, ?)
        """, (barrio, precio))

    conn.commit()
    conn.close()
    print(f"Seeded {len(RENT_M2_MAP)} barrios with rent prices")


if __name__ == "__main__":
    seed_barrio_rent()
