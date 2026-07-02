import sys, os, sqlite3
sys.path.insert(0, os.getcwd())

conn = sqlite3.connect('real_estate.db')
cnt = conn.execute('SELECT COUNT(*) FROM oportunidades').fetchone()[0]
print(f"oportunidades: {cnt} rows")

cols = conn.execute('PRAGMA table_info(oportunidades)').fetchall()
print(f"Columnas: {[c[1] for c in cols]}")

# Try the exact query Radar uses
import pandas as pd
_DESCUENTO_SQL = """
    ROUND(
        CASE
            WHEN o.precio_m2_barrio IS NOT NULL AND o.precio_m2_barrio != 0
            THEN (o.precio_m2_barrio - o.precio_m2) * 100.0 / o.precio_m2_barrio
            ELSE NULL
        END
    , 2) AS descuento_pct
"""
try:
    df = pd.read_sql(f"""
        SELECT o.*, {_DESCUENTO_SQL}
        FROM oportunidades o
        ORDER BY opportunity_score DESC
        LIMIT 5
    """, conn)
    print(f"Radar query OK: {len(df)} rows")
    if not df.empty:
        print(df[['propiedad_id','barrio','opportunity_score','precio_total']].head())
except Exception as e:
    print(f"ERROR en query: {e}")

# Check radar_oportunidades table
rc = conn.execute('SELECT COUNT(*) FROM radar_oportunidades').fetchone()[0]
print(f"radar_oportunidades: {rc} rows")
if rc > 0:
    print(conn.execute('SELECT * FROM radar_oportunidades LIMIT 3').fetchall())

conn.close()
