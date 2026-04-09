import sqlite3

DB_PATH = "real_estate.db"


def detect_events(df):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    events = []

    for _, row in df.iterrows():

        pid = str(row["id"])
        price = row["precio_total"]
        rent = row.get("rentabilidad_estimada", 0)

        cursor.execute("""
        SELECT precio_total, rentabilidad
        FROM property_history
        WHERE property_id = ?
        ORDER BY fecha DESC
        LIMIT 1 OFFSET 1
        """, (pid,))

        prev = cursor.fetchone()

        if prev:
            old_price, old_rent = prev

            # 🔻 PRICE DROP
            if price < old_price * 0.97:
                events.append({
                    "property_id": pid,
                    "type": "price_drop",
                    "old": old_price,
                    "new": price
                })

            # 📈 RENT SPIKE
            if rent > old_rent + 1:
                events.append({
                    "property_id": pid,
                    "type": "yield_up",
                    "old": old_rent,
                    "new": rent
                })

        else:
            events.append({
                "property_id": pid,
                "type": "new_listing",
                "old": None,
                "new": price
            })

    conn.close()
    return events