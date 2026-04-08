def compute_investment_metrics(row):

    try:
        # ========================
        # SAFE GETS
        # ========================
        descuento = float(row.get("descuento_pct", 0) or 0)
        precio_m2 = float(row.get("precio_m2", 0) or 0)
        precio_barrio = float(row.get("precio_m2_barrio", 0) or 0)
        metros = float(row.get("metros", 0) or 0)
        precio_total = float(row.get("precio_total", 0) or 0)

        # ========================
        # DESCUENTO
        # ========================
        score_descuento = min(descuento * 2, 40)

        # ========================
        # PRECIO VS BARRIO
        # ========================
        if precio_barrio > 0:
            ratio = precio_m2 / precio_barrio
        else:
            ratio = 1

        if ratio < 0.85:
            score_precio = 25
        elif ratio < 0.95:
            score_precio = 15
        else:
            score_precio = 5
        # ========================
        # NOISE_SCORING
        # ========================
        
        noise = float(row.get("noise_score", 50) or 50)

        # cuanto menor ruido → mejor score
        if noise < 40:
           score_ruido = 10
        elif noise < 70:
           score_ruido = 5
        else:
           score_ruido = 0
        
        
        # ========================
        # LIQUIDEZ
        # ========================
        if 50 <= metros <= 90:
            score_liquidez = 15
        elif 90 < metros <= 140:
            score_liquidez = 10
        else:
            score_liquidez = 5

        # ========================
        # TAMAÑO
        # ========================
        score_tamano = 10 if metros > 60 else 5

        # ========================
        # SCORE TOTAL
        # ========================
        score_total = (
            score_descuento +
            score_precio +
            score_liquidez +
            score_tamano +
            score_ruido
        )

        # ========================
        # RENTABILIDAD
        # ========================
        if precio_barrio > 0 and precio_total > 0:
            valor_mercado = precio_barrio * metros
            rentabilidad = (valor_mercado - precio_total) / precio_total
        else:
            rentabilidad = 0

        # ========================
        # DECISION
        # ========================
        if score_total >= 70:
            decision = "COMPRAR"
        elif score_total >= 50:
            decision = "NEGOCIAR"
        else:
            decision = "DESCARTAR"

        return {
            "score_total": round(score_total, 2),
            "score_descuento": round(score_descuento, 2),
            "score_precio": score_precio,
            "score_liquidez": score_liquidez,
            "score_tamano": score_tamano,
            "score_ruido": score_ruido,
            "rentabilidad_estimada": round(rentabilidad * 100, 2),
            "decision": decision
        }

    except Exception as e:
        print("Error en fila:", e)
        return {
            "score_total": None,
            "score_descuento": None,
            "score_precio": None,
            "score_liquidez": None,
            "score_tamano": None,
            "score_ruido": None,
            "rentabilidad_estimada": None,
            "decision": None
        }