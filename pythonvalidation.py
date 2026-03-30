import sqlite3
import pandas as pd

conn = sqlite3.connect("real_estate.db")

df = pd.read_sql("SELECT * FROM barrios LIMIT 5", conn)

print(df)

conn.close()