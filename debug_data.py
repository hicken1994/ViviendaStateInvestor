"""
Debug: verificá si los datos reales están cargados en SQLite local.
Ejecuta con: python debug_data.py
"""
import sqlite3

conn = sqlite3.connect("real_estate.db")

op = conn.execute("SELECT COUNT(*) FROM oportunidades").fetchone()[0]
rc = conn.execute("SELECT COUNT(*) FROM radar_oportunidades").fetchone()[0]
br = conn.execute("SELECT COUNT(*) FROM barrio_rent").fetchone()[0]
md = conn.execute("SELECT COUNT(*) FROM mapas_distritos").fetchone()[0]

print(f"oportunidades:      {op:>8,} filas")
print(f"radar_oportunidades: {rc:>8,} filas")
print(f"barrio_rent:        {br:>8,} filas")
print(f"mapas_distritos:    {md:>8,} filas")

if op > 0:
    src = conn.execute("SELECT DISTINCT source FROM oportunidades").fetchall()
    print(f"\nFuentes: {[r[0] for r in src]}")
    barrios = conn.execute("SELECT COUNT(DISTINCT barrio) FROM oportunidades").fetchone()[0]
    print(f"Barrios: {barrios}")
    score_range = conn.execute("SELECT MIN(opportunity_score), MAX(opportunity_score), AVG(opportunity_score) FROM oportunidades").fetchone()
    print(f"Score range: {score_range[0]:.1f} - {score_range[1]:.1f} (avg: {score_range[2]:.1f})")
    diff_range = conn.execute("SELECT MIN(diferencia_pct), MAX(diferencia_pct), AVG(diferencia_pct) FROM oportunidades").fetchone()
    print(f"Diferencia % range: {diff_range[0]:.1f} - {diff_range[1]:.1f} (avg: {diff_range[2]:.1f})")
else:
    print("\n⚠️  No hay datos en SQLite. Necesitás sincronizar desde Supabase.")

conn.close()
