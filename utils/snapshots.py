def save_snapshot(df):
    ensure_history_table()

    conn = get_connection()
    try:
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