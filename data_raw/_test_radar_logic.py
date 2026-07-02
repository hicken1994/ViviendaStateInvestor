import sys, os, sqlite3, pandas as pd
sys.path.insert(0, os.getcwd())
from utils.profiles import get_perfil, compute_score_with_profile

conn = sqlite3.connect('real_estate.db')
_DESCUENTO_SQL = """
    ROUND(
        CASE
            WHEN o.precio_m2_barrio IS NOT NULL AND o.precio_m2_barrio != 0
            THEN (o.precio_m2_barrio - o.precio_m2) * 100.0 / o.precio_m2_barrio
            ELSE NULL
        END
    , 2) AS descuento_pct
"""
df = pd.read_sql(f"""
    SELECT o.*, {_DESCUENTO_SQL}
    FROM oportunidades o
    ORDER BY opportunity_score DESC
    LIMIT 5
""", conn)
conn.close()

print("Top 5 properties by opportunity_score:")
print(df[['propiedad_id','barrio','precio_m2','precio_m2_barrio','diferencia_pct','descuento_pct','opportunity_score']].to_string())

perfil = get_perfil("intermedio")
for i, (_, row) in enumerate(df.iterrows()):
    scores = compute_score_with_profile(row, perfil)
    print(f"\nProperty {i}: {row['barrio']}")
    print(f"  descuento_pct={row['descuento_pct']}, precio_m2={row['precio_m2']}, precio_m2_barrio={row['precio_m2_barrio']}, metros={row['metros']}")
    print(f"  Computed scores: {scores}")

# Also check: how many properties have score_total >= min_score?
df_full = pd.read_sql(f"""
    SELECT o.*, {_DESCUENTO_SQL}
    FROM oportunidades o
    ORDER BY opportunity_score DESC
    LIMIT 300
""", conn)
conn.close()

results = df_full.apply(lambda row: compute_score_with_profile(row, perfil), axis=1, result_type="expand")
for col in results.columns:
    df_full[col] = results[col]

df_full = df_full.sort_values("score_total", ascending=False).reset_index(drop=True)
print(f"\n=== Resumen Radar ===")
print(f"Total propiedades: {len(df_full)}")
print(f"Score total range: {df_full['score_total'].min():.1f} - {df_full['score_total'].max():.1f}")
print(f"Top 3 scores: {df_full['score_total'].head(3).tolist()}")
print(f"Null scores: {df_full['score_total'].isna().sum()}")
min_score = perfil['min_score']
total_opps = len(df_full[df_full["score_total"] >= min_score])
print(f"Properties with score >= {min_score}: {total_opps}")
print(f"Top 5 rows:")
print(df_full[['barrio','precio_total','score_total','descuento_pct','decision']].head(10).to_string())
