
import pandas as pd
import sqlite3
from pathlib import Path

# Ajusta esto a tu DB real (por ejemplo: ProyectoVivienda/real_estate.db)
BASE_DIR = Path(__file__).resolve().parents[1]     # pages/ -> ProyectoVivienda/
db_path  = "real_estate.db"            # o el nombre real de tu DB
csv_path = "MadLatLon.csv" # recomendado: carpeta data/

# Leer CSV
df = pd.read_csv(csv_path, sep=";")  # cambia sep=";" si tu CSV está separado por ;
df.columns = [c.strip() for c in df.columns]      # limpia espacios

# Asegurar que están las columnas esperadas
expected = ["codigo_distrito","distrito","codigo_barrio","barrio","latitud","longitud"]
missing = [c for c in expected if c not in df.columns]
if missing:
    raise ValueError(f"Faltan columnas en el CSV: {missing}. Columnas encontradas: {list(df.columns)}")

# Normalizar tipos
df["codigo_distrito"] = pd.to_numeric(df["codigo_distrito"], errors="coerce").astype("Int64")
df["codigo_barrio"]   = pd.to_numeric(df["codigo_barrio"], errors="coerce").astype("Int64")
df["latitud"]         = pd.to_numeric(df["latitud"], errors="coerce")
df["longitud"]        = pd.to_numeric(df["longitud"], errors="coerce")

df["distrito"] = df["distrito"].astype(str).str.strip()
df["barrio"]   = df["barrio"].astype(str).str.strip()

# Quitar filas sin claves o sin coords (opcional pero recomendable)
df = df.dropna(subset=["codigo_distrito","codigo_barrio","latitud","longitud"])

with sqlite3.connect(db_path) as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS mapas (
      codigo_distrito INTEGER,
      distrito        TEXT,
      codigo_barrio   INTEGER,
      barrio          TEXT,
      latitud         REAL,
      longitud        REAL,
      PRIMARY KEY (codigo_distrito, codigo_barrio)
    );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mapas_distrito ON mapas (codigo_distrito);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mapas_barrio   ON mapas (codigo_barrio);")

    # Cargar datos: reemplaza la tabla completa
    df.to_sql("mapas", conn, if_exists="replace", index=False)

print("✅ Tabla 'mapas' creada y CSV cargado correctamente:", len(df), "filas")
print("DB:", db_path)
print("CSV:", csv_path)
