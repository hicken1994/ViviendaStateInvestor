import pandas as pd
import sqlite3

# 1) Cargar el DataFrame (AJUSTA tu ruta y separador)
csv_path = r"C:\Users\USER\OneDrive\Escritorio\ProyectoVivienda\dataset_viviendas_madrid_3000.csv"
df = pd.read_csv(csv_path, encoding="latin1", sep=";")

# 2) Conectar a SQLite
db_path = r"C:\Users\USER\OneDrive\Escritorio\ProyectoVivienda\real_estate.db"
con = sqlite3.connect(db_path)

# 3) Diagnóstico de columnas
print("DF cols:", list(df.columns))

cur = con.cursor()
cur.execute("PRAGMA table_info(propiedades_raw);")
print("DB cols:", [row[1] for row in cur.fetchall()])

# 4) Insertar (elige replace o append)
df.to_sql("propiedades_raw", con, if_exists="append", index=False)

con.close()
print("✅ Carga terminada")