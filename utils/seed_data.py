"""
Generador de datos sintéticos para todas las tablas core.
Corri como script: python -m utils.seed_data
"""

import sqlite3
import random
import math
from datetime import datetime, timedelta

DB_PATH = "real_estate.db"

MADRID_DISTRITOS = [
    ("Centro", 40.4189, -3.7038, 28),
    ("Arganzuela", 40.3989, -3.6994, 22),
    ("Retiro", 40.4132, -3.6831, 26),
    ("Salamanca", 40.4298, -3.6800, 28),
    ("Chamartín", 40.4556, -3.6800, 24),
    ("Tetuán", 40.4607, -3.6975, 20),
    ("Chamberí", 40.4358, -3.7045, 26),
    ("Fuencarral-El Pardo", 40.4867, -3.7267, 18),
    ("Moncloa-Aravaca", 40.4353, -3.7264, 22),
    ("Latina", 40.4036, -3.7467, 16),
    ("Carabanchel", 40.3900, -3.7400, 15),
    ("Usera", 40.3886, -3.7028, 14),
    ("Puente de Vallecas", 40.3956, -3.6683, 14),
    ("Moratalaz", 40.4114, -3.6492, 16),
    ("Ciudad Lineal", 40.4456, -3.6511, 18),
    ("Hortaleza", 40.4733, -3.6436, 18),
    ("Villaverde", 40.3489, -3.7089, 12),
    ("Villa de Vallecas", 40.3806, -3.6208, 14),
    ("Vicálvaro", 40.4033, -3.6081, 14),
    ("San Blas-Canillejas", 40.4392, -3.6158, 16),
    ("Barajas", 40.4735, -3.5777, 18),
]

DISTRITO_MAPPING = [
    ("centro", "centro"),
    ("arganzuela", "arganzuela"),
    ("retiro", "retiro"),
    ("salamanca", "salamanca"),
    ("chamartin", "chamartín"),
    ("tetuan", "tetuán"),
    ("fuencarral", "fuencarral-el pardo"),
    ("moncloa", "moncloa-aravaca"),
    ("latina", "latina"),
    ("carabanchel", "carabanchel"),
    ("usera", "usera"),
    ("puente de vallecas", "puente de vallecas"),
    ("moratalaz", "moratalaz"),
    ("ciudad lineal", "ciudad lineal"),
    ("hortaleza", "hortaleza"),
    ("villaverde", "villaverde"),
    ("villa de vallecas", "villa de vallecas"),
    ("vicalvaro", "vicálvaro"),
    ("san blas", "san blas-canillejas"),
    ("barajas", "barajas"),
    ("chamberi", "chamberí"),
    ("vicalvaro", "vicálvaro"),
]

NOMBRES_BARRIO = [d[0] for d in MADRID_DISTRITOS]


def _rand_norm(mean, sigma, lo=None, hi=None):
    v = random.gauss(mean, sigma)
    if lo is not None:
        v = max(v, lo)
    if hi is not None:
        v = min(v, hi)
    return v


def _pick_barrio_price(barrio_idx):
    b = MADRID_DISTRITOS[barrio_idx]
    base_price = b[3] * 100 + 1500
    return _rand_norm(base_price, base_price * 0.15, lo=800, hi=7000)


def generate_oportunidades(conn: sqlite3.Connection, count: int = 1500):
    conn.execute("DELETE FROM oportunidades")
    rows = []
    for pid in range(1, count + 1):
        bi = random.randrange(len(MADRID_DISTRITOS))
        barrio = NOMBRES_BARRIO[bi]
        metros = _rand_norm(80, 25, lo=35, hi=250)
        precio_m2_barrio = _pick_barrio_price(bi)
        discount = _rand_norm(12, 8, lo=-5, hi=35)
        precio_m2 = precio_m2_barrio * (1 - discount / 100)
        precio_total = round(precio_m2 * metros)
        diferencia_pct = round((precio_m2_barrio - precio_m2) / precio_m2_barrio * 100, 2)
        opportunity_score = _rand_norm(65, 18, lo=10, hi=99)
        score_descuento = None
        score_precio = None
        score_liquidez = None
        score_tamano = None
        rentabilidad_estimada = round(discount + _rand_norm(0, 3), 2)
        decision = None
        is_premium = 1 if opportunity_score > 80 else 0
        rows.append((
            pid, barrio, round(metros, 1), round(precio_m2, 1),
            round(precio_m2_barrio, 1), round(diferencia_pct, 2),
            round(opportunity_score, 1), round(precio_total, 1),
            score_descuento, score_precio, score_liquidez, score_tamano,
            round(rentabilidad_estimada, 2), decision, is_premium,
        ))
    conn.executemany("""
        INSERT INTO oportunidades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()


def generate_barrio_rent(conn: sqlite3.Connection):
    conn.execute("DELETE FROM barrio_rent")
    for name, _, _, base_rent in MADRID_DISTRITOS:
        rent = _rand_norm(base_rent, 3, lo=8, hi=35)
        conn.execute(
            "INSERT OR REPLACE INTO barrio_rent (barrio, precio_m2_alquiler) VALUES (?, ?)",
            (name, round(rent, 1)),
        )
    conn.commit()


def generate_radar_oportunidades(conn: sqlite3.Connection):
    conn.execute("DELETE FROM radar_oportunidades")
    for name, _, _, _ in MADRID_DISTRITOS:
        cnt = random.randint(30, 80)
        desc_medio = _rand_norm(-12, 4, lo=-25, hi=-2)
        precio_m2 = _rand_norm(3500, 1000, lo=1200, hi=6500)
        idx = _rand_norm(75, 10, lo=50, hi=95)
        conn.execute("""
            INSERT INTO radar_oportunidades VALUES (?, ?, ?, ?, ?)
        """, (name, cnt, round(desc_medio, 2), round(precio_m2, 2), round(idx, 2)))
    conn.commit()


def generate_mapas_distritos(conn: sqlite3.Connection):
    conn.execute("DELETE FROM mapas_distritos")
    for name, lat, lon, _ in MADRID_DISTRITOS:
        conn.execute(
            "INSERT INTO mapas_distritos VALUES (?, ?, ?)",
            (name.lower(), lat, lon),
        )
    conn.commit()


def generate_distrito_mapping(conn: sqlite3.Connection):
    conn.execute("DELETE FROM distrito_mapping")
    seen = set()
    for raw, mapa in DISTRITO_MAPPING:
        if raw not in seen:
            conn.execute(
                "INSERT INTO distrito_mapping VALUES (?, ?)",
                (raw, mapa),
            )
            seen.add(raw)
    conn.commit()


def generate_property_history(conn: sqlite3.Connection):
    conn.execute("DELETE FROM property_history")
    conn.commit()


def seed_all(conn: sqlite3.Connection):
    print("Generando barrio_rent...")
    generate_barrio_rent(conn)
    print("Generando mapas_distritos...")
    generate_mapas_distritos(conn)
    print("Generando distrito_mapping...")
    generate_distrito_mapping(conn)
    print("Generando radar_oportunidades...")
    generate_radar_oportunidades(conn)
    print("Generando oportunidades (1500 propiedades)...")
    generate_oportunidades(conn)
    print("Generando property_history...")
    generate_property_history(conn)
    print("Seed completado.")


def get_counts(conn: sqlite3.Connection) -> dict:
    tables = [
        "oportunidades", "barrio_rent", "radar_oportunidades",
        "mapas_distritos", "distrito_mapping", "property_history",
    ]
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=OFF")
    seed_all(conn)
    for t, c in get_counts(conn).items():
        print(f"  {t}: {c} rows")
    conn.close()
