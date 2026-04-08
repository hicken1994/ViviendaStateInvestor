"""
Tooltips y definiciones amigables para todos los conceptos de inversión.
Centralizado para mantener consistencia en toda la app.
"""

TOOLTIPS = {
    # Métricas principales
    "score_total": "Puntuación global (0-100) que combina descuento, precio vs barrio, liquidez y tamaño. Cuanto más alto, mejor oportunidad.",
    "score_radar": "Puntuación del radar (0-100) basada en rentabilidad, descuento, precio vs barrio y días en mercado. Identifica oportunidades rápidas.",
    "rentabilidad_estimada": "Porcentaje de ganancia anual estimada sobre tu inversión inicial, calculada con el valor de mercado del barrio.",
    "cashflow": "Dinero neto que recibes cada mes después de pagar hipoteca, gastos y comunidad. Positivo = ganas dinero.",
    "break_even": "Alquiler mínimo mensual que necesitas para cubrir todos tus gastos (hipoteca + gestión + fijos). Por debajo de esto, pierdes dinero.",
    "margen": "Diferencia entre lo que cobras de alquiler y lo que necesitas para cubrir gastos. Mayor margen = más seguridad.",
    "margen_pct": "Porcentaje de tu alquiler que queda como beneficio neto después de cubrir todos los gastos.",
    "precio_total": "Precio de venta publicado de la propiedad, sin incluir gastos de compra ni reforma.",
    "precio_m2": "Precio por metro cuadrado de esta propiedad. Compáralo con el del barrio para ver si está cara o barata.",
    "precio_m2_barrio": "Precio medio por m² en este barrio. Si la propiedad está por debajo, puede ser una oportunidad.",
    "descuento": "Porcentaje de descuento respecto al precio medio del barrio. Más descuento = mejor precio de entrada.",
    "metros": "Superficie útil de la vivienda en metros cuadrados.",
    "dias": "Días que lleva la propiedad publicada en el mercado. Más días puede indicar margen de negociación.",

    # Simulación
    "entrada": "Porcentaje del precio que pagas de tu bolsillo (el resto lo financia el banco).",
    "interes": "Tipo de interés anual de la hipoteca. Determina cuánto pagarás al banco cada mes.",
    "años_hipoteca": "Plazo de la hipoteca en años. Más años = cuota más baja pero más intereses totales.",
    "reforma": "Coste estimado de reformar la vivienda antes de alquilarla. Incluye pintura, cocina, baño, etc.",
    "gastos_compra": "Gastos asociados a la compra: impuestos (ITP/IVA), notaría, registro y gestoría. Suelen ser 8-12% del precio.",

    # Conceptos de inversión
    "opportunity_score": "Índice de oportunidad calculado por IA que combina múltiples factores del mercado.",
    "rentabilidad_real": "Rentabilidad anual calculada con tus números reales (alquiler / inversión total × 100).",
    "liquidez": "Facilidad para alquilar o vender la propiedad. Pisos de 50-90m² en buenas zonas son los más líquidos.",
    "score_descuento": "Puntuación parcial basada en el descuento sobre precio de mercado.",
    "score_precio": "Puntuación parcial que compara el precio/m² con la media del barrio.",
    "score_liquidez": "Puntuación parcial basada en el tamaño y facilidad de alquiler del inmueble.",
    "score_tamano": "Puntuación parcial según los metros cuadrados (más de 60m² puntúa mejor).",
    "score_ruido": "Puntuación parcial por nivel de ruido de la zona. Menos ruido = mejor puntuación.",

    # Decisiones
    "decision_comprar": "El análisis indica que esta propiedad tiene buenas métricas para invertir.",
    "decision_negociar": "La propiedad es interesante pero conviene negociar el precio un 5-10% a la baja.",
    "decision_descartar": "Los números no cuadran. Mejor buscar otra oportunidad.",

    # Perfiles
    "perfil_basico": "Inversor principiante: busca operaciones seguras con cashflow positivo y bajo riesgo.",
    "perfil_intermedio": "Inversor con experiencia: equilibra rentabilidad y riesgo, puede negociar y reformar.",
    "perfil_avanzado": "Inversor experto: busca máxima rentabilidad, tolera más riesgo y operaciones complejas.",

    # Oportunidades
    "oportunidad_dia": "La propiedad con mejor puntuación global del momento. Cambia cada vez que se actualiza el mercado.",
    "oportunidades_detectadas": "Propiedades que cumplen criterios estrictos: score ≥ 65 y rentabilidad ≥ 6%. Son las más interesantes.",
    "precio_objetivo": "Precio sugerido para hacer tu oferta. Calculado según el descuento actual y margen de negociación.",
}


def tooltip_label(label: str, key: str) -> str:
    """
    Genera un label con tooltip (icono ℹ️) usando markdown.
    Ejemplo: '💰 Precio ℹ️'
    """
    tip = TOOLTIPS.get(key, "")
    if tip:
        return f"{label} <span title='{tip}'>ℹ️</span>"
    return label


def tooltip_md(label: str, key: str) -> str:
    """
    Genera un markdown con el label y una línea de ayuda debajo.
    Para usar con st.markdown().
    """
    tip = TOOLTIPS.get(key, "")
    if tip:
        return f"{label}\n\n> 💡 *{tip}*"
    return label


def tooltip_help(key: str) -> str:
    """
    Devuelve solo el texto de ayuda para usar con el parámetro help= de Streamlit.
    Ejemplo: st.metric("Score", value, help=tooltip_help("score_total"))
    """
    return TOOLTIPS.get(key, "")
