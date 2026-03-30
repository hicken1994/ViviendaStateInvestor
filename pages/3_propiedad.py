import streamlit as st

st.title("🏠 Análisis de propiedad")

# ========================
# VALIDACIÓN
# ========================

if "selected_property" not in st.session_state:
    st.warning("No hay propiedad seleccionada")
    st.stop()

# ✅ AHORA SÍ DEFINIMOS PROP BIEN
prop = st.session_state.selected_property

precio = prop.get("precio_total", 0)
metros = prop.get("metros", 0)
precio_m2_barrio = prop.get("precio_m2_barrio", 0)

# ========================
# HEADER
# ========================

st.divider()
st.subheader(prop.get("barrio"))

col1, col2, col3 = st.columns(3)

col1.metric("💰 Precio", f"{int(precio):,} €")
col2.metric("📊 Score", prop.get("score_total"))
col3.metric("📈 Rentabilidad estimada", f"{prop.get('rentabilidad_estimada', 0)}%")

# ========================
# SIMULACIÓN
# ========================

st.divider()
st.subheader("🏦 Simulación de inversión")

col1, col2, col3 = st.columns(3)

entrada_pct = col1.slider("Entrada (%)", 10, 40, 20) / 100
interes = col2.slider("Interés (%)", 1.0, 6.0, 3.5) / 100
años = col3.slider("Años", 10, 40, 30)

reforma = st.number_input("Coste reforma (€)", value=15000)
gastos_pct = st.slider("Gastos compra (%)", 5, 15, 10) / 100

entrada = precio * entrada_pct
gastos = precio * gastos_pct
total_inversion = entrada + gastos + reforma

prestamo = precio - entrada

r = interes / 12
n = años * 12

cuota = prestamo * (r * (1 + r)**n) / ((1 + r)**n - 1)

# ========================
# DETECCIÓN MODO
# ========================

default_values = {"entrada": 0.20, "interes": 0.035, "años": 30}

is_advanced = (
    abs(entrada_pct - default_values["entrada"]) > 0.01 or
    abs(interes - default_values["interes"]) > 0.001 or
    años != default_values["años"]
)

modo = "avanzado" if is_advanced else "simple"

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

base_alquiler = precio_m2_alquiler * metros
alquiler = base_alquiler * 1.15

# ========================
# COSTES
# ========================

gastos_mensuales = alquiler * 0.15
gastos_fijos = 100

cashflow = alquiler - cuota - gastos_mensuales - gastos_fijos
break_even = (cuota + gastos_fijos) / (1 - 0.15)

rentabilidad_real = (alquiler * 12) / total_inversion * 100 if total_inversion else 0

# ========================
# MARGEN
# ========================

margen_euros = alquiler - break_even
margen_pct = (margen_euros / alquiler) * 100

# ========================
# 🧠 RECOMENDACIÓN (DECISIÓN FINAL)
# ========================

if cashflow > 0 and margen_pct > 25:
    recomendacion = "🟢 BUENA COMPRA"
elif cashflow > 0:
    recomendacion = "🟡 OPERACIÓN JUSTA"
else:
    recomendacion = "🔴 NO COMPRAR"

# ========================
# 🚀 HERO
# ========================

st.markdown("## 🎯 Decisión")
st.markdown(f"### 👉 {recomendacion}")

# ========================
# MÉTRICAS CLAVE
# ========================

col1, col2, col3 = st.columns(3)

col1.metric("💰 Cashflow", f"{int(cashflow):,} €/mes")
col2.metric("🎯 Break-even", f"{int(break_even):,} €/mes")
col3.metric("🛡️ Margen", f"{int(margen_euros)} €")

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
# UX → SIGUIENTE PASO
# ========================

st.info("👉 Puedes validar esta decisión con un análisis más profundo usando IA")

if st.button("🔍 Validar con IA"):
    # ✅ AQUÍ PASAMOS TODO AL COPILOT
    st.session_state.copilot_property = {
        **prop,
        "cashflow": cashflow,
        "break_even": break_even,
        "margen": margen_euros,
        "margen_pct": margen_pct,
        "recomendacion_modelo": recomendacion
    }

    st.switch_page("pages/4_Analisis_Detallado.py")

# ========================
# MODO SIMPLE
# ========================

if modo == "simple":

    st.markdown(f"""
    💡 **Resumen claro:**

    - Ingreso estimado: **{int(alquiler)}€/mes**
    - Necesitas: **{int(break_even)}€/mes**
    - Diferencia: **{int(margen_euros)}€/mes**
    """)

    if margen_euros < 200:
        st.warning("Cualquier imprevisto puede eliminar la rentabilidad")

# ========================
# DETALLE
# ========================

with st.expander("Ver análisis detallado"):

    st.markdown("### 🧠 Estimación de alquiler")
    st.write(f"{int(base_alquiler)} € base → {int(alquiler)} € ajustado")

    st.markdown("### 💸 Costes")
    st.write(f"Hipoteca: {int(cuota)} €")
    st.write(f"Gastos: {int(gastos_mensuales)} €")
    st.write(f"Fijos: {int(gastos_fijos)} €")

    st.markdown("### 📊 Rentabilidad")
    st.metric("Rentabilidad real", f"{rentabilidad_real:.1f}%")

    st.markdown("### 📈 Escenarios")

    for nombre, val in [
        ("Conservador", base_alquiler),
        ("Esperado", alquiler),
        ("Optimista", base_alquiler * 1.25)
    ]:
        cf = val - cuota - (val * 0.15) - gastos_fijos
        st.write(f"{nombre}: {int(val)}€ → {int(cf)}€/mes")
