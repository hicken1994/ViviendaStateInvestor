"""
Perfiles de inversión: básico, intermedio, avanzado.
Define umbrales, pesos de scoring y análisis adaptado a cada nivel.
"""

PERFILES = {
    "basico": {
        "nombre": "🟢 Básico",
        "descripcion": "Busca seguridad y cashflow positivo. Ideal para tu primera inversión.",
        "emoji": "🟢",
        # Umbrales más conservadores
        "min_cashflow": 200,
        "min_margen_pct": 25,
        "max_precio": 250000,
        "min_rentabilidad": 5,
        "min_score": 60,
        # Pesos de scoring adaptados
        "peso_descuento": 1.0,
        "peso_precio": 1.0,
        "peso_liquidez": 1.5,   # Prioriza liquidez (fácil de alquilar)
        "peso_tamano": 1.0,
        "peso_ruido": 1.2,       # Le importa más el ruido
        # Parámetros de simulación por defecto
        "entrada_pct": 25,
        "interes": 3.5,
        "años": 30,
        "reforma": 10000,
        "gastos_pct": 10,
        # Mensajes
        "consejo_compra": "✅ Operación segura con buen margen. Ideal para empezar.",
        "consejo_negociar": "⚠️ Podría funcionar si negocias un 5-10%. Pide ayuda a un experto.",
        "consejo_descartar": "❌ No es para ti. Busca algo con más margen de seguridad.",
        # Métricas que se muestran
        "metricas_visibles": ["cashflow", "rentabilidad_real", "margen", "break_even"],
        "mostrar_escenarios": False,
        "mostrar_detalle_scoring": False,
    },
    "intermedio": {
        "nombre": "🟡 Intermedio",
        "descripcion": "Equilibra rentabilidad y riesgo. Ya has invertido antes.",
        "emoji": "🟡",
        "min_cashflow": 100,
        "min_margen_pct": 15,
        "max_precio": 400000,
        "min_rentabilidad": 4,
        "min_score": 45,
        "peso_descuento": 1.2,
        "peso_precio": 1.2,
        "peso_liquidez": 1.0,
        "peso_tamano": 1.0,
        "peso_ruido": 0.8,
        "entrada_pct": 20,
        "interes": 3.5,
        "años": 25,
        "reforma": 15000,
        "gastos_pct": 10,
        "consejo_compra": "✅ Buenos números. Valida con un análisis detallado antes de ofertar.",
        "consejo_negociar": "🟡 Interesante pero con margen ajustado. Negocia agresivamente.",
        "consejo_descartar": "❌ Los números no cuadran. Hay mejores opciones en el radar.",
        "metricas_visibles": ["cashflow", "rentabilidad_real", "margen", "break_even", "score_descuento", "score_precio"],
        "mostrar_escenarios": True,
        "mostrar_detalle_scoring": False,
    },
    "avanzado": {
        "nombre": "🔴 Avanzado",
        "descripcion": "Máxima rentabilidad. Tolera riesgo y operaciones complejas.",
        "emoji": "🔴",
        "min_cashflow": 0,
        "min_margen_pct": 5,
        "max_precio": 1000000,
        "min_rentabilidad": 3,
        "min_score": 30,
        "peso_descuento": 1.5,
        "peso_precio": 1.5,
        "peso_liquidez": 0.8,
        "peso_tamano": 0.8,
        "peso_ruido": 0.5,
        "entrada_pct": 15,
        "interes": 3.5,
        "años": 20,
        "reforma": 25000,
        "gastos_pct": 10,
        "consejo_compra": "✅ Oportunidad clara. Lanza oferta rápido.",
        "consejo_negociar": "🟡 Puede ser rentable con la negociación correcta. Analiza el detalle.",
        "consejo_descartar": "❌ No compensa el riesgo para la rentabilidad esperada.",
        "metricas_visibles": ["cashflow", "rentabilidad_real", "margen", "break_even", "score_descuento", "score_precio", "score_liquidez", "score_tamano", "score_ruido"],
        "mostrar_escenarios": True,
        "mostrar_detalle_scoring": True,
    },
}


def get_perfil(nombre: str) -> dict:
    """Devuelve el perfil por nombre. Default: intermedio."""
    return PERFILES.get(nombre, PERFILES["intermedio"])


def get_perfil_names() -> list:
    """Lista de nombres de perfiles disponibles."""
    return list(PERFILES.keys())


def compute_score_with_profile(row, perfil: dict) -> dict:
    """
    Calcula el score total ponderado según el perfil del inversor.
    Usa los pesos del perfil para ajustar cada componente.
    """
    try:
        descuento = float(row.get("descuento_pct", 0) or 0)
        precio_m2 = float(row.get("precio_m2", 0) or 0)
        precio_barrio = float(row.get("precio_m2_barrio", 0) or 0)
        metros = float(row.get("metros", 0) or 0)
        precio_total = float(row.get("precio_total", 0) or 0)
        noise = float(row.get("noise_score", 50) or 50)

        # Base scores (sin ponderar)
        score_descuento = min(descuento * 2, 40)

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

        if noise < 40:
            score_ruido = 10
        elif noise < 70:
            score_ruido = 5
        else:
            score_ruido = 0

        if 50 <= metros <= 90:
            score_liquidez = 15
        elif 90 < metros <= 140:
            score_liquidez = 10
        else:
            score_liquidez = 5

        score_tamano = 10 if metros > 60 else 5

        # Aplicar pesos del perfil
        score_total = (
            score_descuento * perfil["peso_descuento"] +
            score_precio * perfil["peso_precio"] +
            score_liquidez * perfil["peso_liquidez"] +
            score_tamano * perfil["peso_tamano"] +
            score_ruido * perfil["peso_ruido"]
        )

        # Normalizar a 100
        max_possible = (
            40 * perfil["peso_descuento"] +
            25 * perfil["peso_precio"] +
            15 * perfil["peso_liquidez"] +
            10 * perfil["peso_tamano"] +
            10 * perfil["peso_ruido"]
        )

        score_total = round((score_total / max_possible) * 100, 2) if max_possible > 0 else 0

        # Rentabilidad
        if precio_barrio > 0 and precio_total > 0:
            valor_mercado = precio_barrio * metros
            rentabilidad = ((valor_mercado - precio_total) / precio_total) * 100
        else:
            rentabilidad = 0

        # Decisión adaptada al perfil
        if score_total >= perfil["min_score"] + 20 and rentabilidad >= perfil["min_rentabilidad"]:
            decision = "COMPRAR"
        elif score_total >= perfil["min_score"]:
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
            "rentabilidad_estimada": round(rentabilidad, 2),
            "decision": decision,
        }

    except Exception as e:
        print(f"Error scoring con perfil: {e}")
        return {
            "score_total": None,
            "score_descuento": None,
            "score_precio": None,
            "score_liquidez": None,
            "score_tamano": None,
            "score_ruido": None,
            "rentabilidad_estimada": None,
            "decision": None,
        }


def get_recomendacion_perfil(perfil: dict, cashflow: float, margen_pct: float, score: float) -> str:
    """
    Devuelve la recomendación adaptada al perfil del inversor.
    """
    if cashflow >= perfil["min_cashflow"] and margen_pct >= perfil["min_margen_pct"]:
        return f"🟢 BUENA COMPRA — {perfil['consejo_compra']}"
    elif cashflow > 0 and margen_pct >= perfil["min_margen_pct"] * 0.5:
        return f"🟡 OPERACIÓN JUSTA — {perfil['consejo_negociar']}"
    else:
        return f"🔴 NO COMPRAR — {perfil['consejo_descartar']}"
