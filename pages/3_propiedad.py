import streamlit as st
from utils.tooltips import tooltip_help
from utils.db import get_recent_events
from utils.profiles import get_perfil, get_recomendacion_perfil


st.title("🏠 Análisis de propiedad")
st.caption("💡 Aquí se analiza en detalle si una propiedad es buena inversión para ti.")

# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)

st.info(f"🎯 Perfil activo: **{perfil['nombre']}** — {perfil['descripcion']}")

# ========================
# VALIDACIÓN
# ========================

if "selected_property" not in st.session_state:
    st.warning("No hay propiedad seleccionada")
    st.stop()

prop = st.session_state.selected_property

if prop.get("image_url"):
    st.image(prop["image_url"], use_container_width=True)

precio = prop.get("precio_total", 0)
metros = prop.get("metros", 0)
precio_m2_barrio = prop.get("precio_m2_barrio", 0)

# ========================
# 📡 ACTIVIDAD RECIENTE DE ESTA PROPIEDAD
# ========================

prop_id = str(prop.get("id", prop.get("precio_total", "")))
events = get_recent_events(50)

if not events.empty:
    prop_events = events[events["property_id"] == prop_id]

    if not prop_events.empty:
        with st.expander("🚨 Actividad reciente en esta propiedad", expanded=True):
            for _, e in prop_events.iterrows():
                etype = e.get("event_type", "")
                old_val = e.get("old_value")
                new_val = e.get("new_value")

                if etype == "price_drop":
                    delta = f"de {int(old_val):,}€ a {int(new_val):,}€" if old_val and new_val else ""
                    st.error(f"💸 **Bajada de precio** {delta}")
                elif etype == "yield_up":
                    delta = f"de {round(old_val, 2)}% a {round(new_val, 2)}%" if old_val and new_val else ""
                    st.info(f"📈 **Mejora de rentabilidad** {delta}")
                elif etype == "new_listing":
                    st.success("🆕 **Nueva propiedad** detectada")
                else:
                    st.write(f"📌 {etype}")

# ========================
# HEADER
# ========================

st.divider()
st.subheader(f"📍 {prop.get('barrio', 'Sin barrio')}")

col1, col2, col3 = st.columns(3)

col1.metric("💰 Precio", f"{int(precio):,} €", help=tooltip_help("precio_total"))
col2.metric("📊 Score", round(prop.get("score_total", 0), 2), help=tooltip_help("score_total"))
col3.metric("📈 Rentabilidad estimada", f"{round(prop.get('rentabilidad_estimada', 0), 2)}%", help=tooltip_help("rentabilidad_estimada"))

# ========================
# SIMULACIÓN
# ========================

st.divider()
st.subheader("🏦 Simulación de inversión")
st.caption(tooltip_help("entrada"))

col1, col2, col3 = st.columns(3)

entrada_pct = col1.slider("Entrada (%)", 10, 40, perfil["entrada_pct"], help=tooltip_help("entrada")) / 100
interes = col2.slider("Interés (%)", 1.0, 6.0, float(perfil["interes"]), help=tooltip_help("interes")) / 100
años = col3.slider("Años", 10, 40, perfil["años"], help=tooltip_help("años_hipoteca"))

reforma = st.number_input("Coste reforma (€)", value=perfil["reforma"], help=tooltip_help("reforma"))
gastos_pct = st.slider("Gastos compra (%)", 5, 15, perfil["gastos_pct"], help=tooltip_help("gastos_compra")) / 100

entrada = precio * entrada_pct
gastos = precio * gastos_pct
total_inversion = entrada + gastos + reforma

prestamo = precio - entrada

r = interes / 12
n = años * 12

cuota = round(prestamo * (r * (1 + r)**n) / ((1 + r)**n - 1), 2)

# ========================
# ALQUILER
# ========================

rent_m2_map = {
    "Salamanca": 28,
    "Chamberí": 26,
    "Centro": 25,
    "Chamartín": 24,
    "Tetuán": 22,
    "Ciudad Lineal": 21,
    "Carabanchel": 18,
    "Usera": 17
}

barrio = prop.get("barrio", "")
precio_m2_alquiler = rent_m2_map.get(barrio, 20)

base_alquiler = round(precio_m2_alquiler * metros, 2)
alquiler = round(base_alquiler * 1.15, 2)

# ========================
# COSTES
# ========================

gastos_mensuales = round(alquiler * 0.15, 2)
gastos_fijos = 100

cashflow = round(alquiler - cuota - gastos_mensuales - gastos_fijos, 2)
break_even = round((cuota + gastos_fijos) / (1 - 0.15), 2)

rentabilidad_real = round((alquiler * 12) / total_inversion * 100, 2) if total_inversion else 0

# ========================
# MARGEN
# ========================

margen_euros = round(alquiler - break_even, 2)
margen_pct = round((margen_euros / alquiler) * 100, 2) if alquiler else 0

# ========================
# 🧠 RECOMENDACIÓN ADAPTADA AL PERFIL
# ========================

score_total = prop.get("score_total", 0)
recomendacion = get_recomendacion_perfil(perfil, cashflow, margen_pct, score_total)

# ========================
# 🚀 HERO
# ========================

st.markdown("## 🎯 Decisión")
st.markdown(f"### 👉 {recomendacion}")

# ========================
# MÉTRICAS CLAVE
# ========================

col1, col2, col3 = st.columns(3)

col1.metric("💰 Cashflow", f"{cashflow:,.2f} €/mes", help=tooltip_help("cashflow"))
col2.metric("🎯 Break-even", f"{break_even:,.2f} €/mes", help=tooltip_help("break_even"))
col3.metric("🛡️ Margen", f"{margen_euros:,.2f} €", help=tooltip_help("margen"))

# ========================
# INTERPRETACIÓN
# ========================

if cashflow <= 0:
    st.error("Esta operación pierde dinero mensualmente")
elif margen_pct < 10:
    st.error("Margen muy bajo — alta probabilidad de problemas")
elif margen_pct < 25:
    st.warning("Margen limitado — depende del mercado")
else:
    st.success("Margen sólido — operación defensiva")

# ========================
# 📊 DETALLE SCORING POR PERFIL
# ========================

if perfil.get("mostrar_detalle_scoring"):
    st.divider()
    st.markdown("### 🧪 Desglose del scoring")
    st.caption("Visible solo para perfil avanzado.")

    score_cols = {
        "score_descuento": "Descuento",
        "score_precio": "Precio vs Barrio",
        "score_liquidez": "Liquidez",
        "score_tamano": "Tamaño",
        "score_ruido": "Ruido",
    }

    cols = st.columns(len(score_cols))
    for idx, (key, label) in enumerate(score_cols.items()):
        val = prop.get(key, 0)
        cols[idx].metric(label, round(val, 2) if val else 0, help=tooltip_help(key))

# ========================
# UX → SIGUIENTE PASO
# ========================

st.divider()
st.info("👉 Puedes validar esta decisión con un análisis más profundo usando IA")

if st.button("🔍 Validar con IA"):
    st.session_state.copilot_property = {
        **prop,
        "score_total": round(prop.get("score_total", 0), 2),
        "cashflow": round(cashflow, 2),
        "break_even": round(break_even, 2),
        "margen": round(margen_euros, 2),
        "margen_pct": round(margen_pct, 2),
        "recomendacion_modelo": recomendacion,
        "perfil_inversion": perfil_nombre,
    }
    st.switch_page("pages/4_Analisis_Detallado.py")

# ========================
# MODO SIMPLE (PARA PERFIL BÁSICO)
# ========================

if perfil_nombre == "basico":

    st.divider()
    st.markdown(f"""
    💡 **Resumen claro:**

    - Ingreso estimado: **{alquiler:.2f}€/mes**
    - Necesitas: **{break_even:.2f}€/mes**
    - Diferencia: **{margen_euros:.2f}€/mes**
    """)

    if margen_euros < 200:
        st.warning("Cualquier imprevisto puede eliminar la rentabilidad")

# ========================
# ESCENARIOS (INTERMEDIO Y AVANZADO)
# ========================

if perfil.get("mostrar_escenarios"):

    with st.expander("📊 Ver análisis detallado"):

        st.markdown("### 🧠 Estimación de alquiler")
        st.caption(tooltip_help("rentabilidad_real"))
        st.write(f"{base_alquiler:.2f} € base → {alquiler:.2f} € ajustado")

        st.markdown("### 💸 Costes")
        st.write(f"Hipoteca: {cuota:.2f} €")
        st.write(f"Gastos: {gastos_mensuales:.2f} €")
        st.write(f"Fijos: {gastos_fijos:.2f} €")

        st.markdown("### 📊 Rentabilidad")
        st.metric("Rentabilidad real", f"{rentabilidad_real:.2f}%", help=tooltip_help("rentabilidad_real"))

        st.markdown("### 📈 Escenarios")

        for nombre, val in [
            ("🟢 Conservador", base_alquiler),
            ("🟡 Esperado", alquiler),
            ("🔵 Optimista", base_alquiler * 1.25)
        ]:
            cf = round(val - cuota - (val * 0.15) - gastos_fijos, 2)
            color = "success" if cf > 0 else "error"
            getattr(st, color)(f"{nombre}: {val:.2f}€/mes → **{cf:.2f}€/mes** cashflow")
