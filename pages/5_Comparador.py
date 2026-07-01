"""
Side-by-side comparison of selected properties.
"""

import streamlit as st
import pandas as pd
from utils.profiles import get_perfil
from utils.charts import create_comparison_radar
from utils.auth import require_auth

st.set_page_config(
    page_title="Comparador",
    page_icon="⚖️",
    layout="wide",
)


require_auth()

# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)


# ========================
# VALIDACIÓN
# ========================

props = st.session_state.get("compare_properties", [])
names = st.session_state.get("compare_names", [])

if len(props) < 2:
    st.warning("Selecciona al menos 2 propiedades desde el Radar para comparar.")
    if st.button("← Volver al Radar"):
        st.switch_page("pages/1_Radar.py")
    st.stop()


# ========================
# HEADER
# ========================

st.markdown("# ⚖️ Comparador de propiedades")
st.caption(
    f"Comparando {len(props)} propiedades · "
    f"Perfil activo: **{perfil['emoji']} {perfil['nombre']}**"
)

if st.button("← Volver al Radar", type="secondary"):
    st.switch_page("pages/1_Radar.py")

st.divider()


# ========================
# 1. KPI ROW — cards lado a lado
# ========================

card_cols = st.columns(len(props))

for i, (prop, name) in enumerate(zip(props, names)):
    with card_cols[i]:
        if prop.get("image_url"):
            st.image(prop["image_url"], width="stretch")

        st.markdown(f"### {name}")

        # Decision badge
        decision = prop.get("decision", "")
        if "COMPRAR" in str(decision):
            badge = "🟢 COMPRAR"
        elif "NEGOCIAR" in str(decision):
            badge = "🟡 NEGOCIAR"
        else:
            badge = "🔴 DESCARTAR"
        st.markdown(f"**{badge}**")

        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Precio", f"{int(prop.get('precio_total', 0)):,} €")
        m2.metric("📊 Score", f"{round(prop.get('score_total', 0), 1)}")
        m3.metric("📈 Rent.", f"{round(prop.get('rentabilidad_estimada', 0), 1)}%")

        m4, m5, m6 = st.columns(3)
        m4.metric("🏗️ m²", f"{int(prop.get('metros', 0))}")
        m5.metric("⏱️ Días", f"{int(prop.get('dias', 0))}")
        m6.metric("💶 €/m²", f"{int(prop.get('precio_m2', 0)):,}")


st.divider()


# ========================
# 2. RADAR OVERLAY
# ========================

st.markdown("### 📡 Perfil de scores — comparativa visual")
st.caption("Cada propiedad es una traza. Mientras más grande el área, mejor equilibrada.")

fig = create_comparison_radar(
    properties=props,
    property_names=names,
    height=450,
)
st.plotly_chart(fig, width="stretch", key="cmp_radar")


st.divider()


# ========================
# 3. TABLA COMPARATIVA
# ========================

st.markdown("### 📊 Tabla comparativa")

cmp_rows = []
for prop, name in zip(props, names):
    cmp_rows.append({
        "Propiedad": name,
        "Barrio": prop.get("barrio", ""),
        "Precio (€)": int(prop.get("precio_total", 0)),
        "m²": int(prop.get("metros", 0)),
        "€/m²": int(prop.get("precio_m2", 0)),
        "Score": round(prop.get("score_total", 0), 1),
        "Rent. (%)": round(prop.get("rentabilidad_estimada", 0), 1),
        "Descuento": round(prop.get("score_descuento", 0), 1),
        "Precio vs Brr.": round(prop.get("score_precio", 0), 1),
        "Liquidez": round(prop.get("score_liquidez", 0), 1),
        "Tamaño": round(prop.get("score_tamano", 0), 1),
        "Ruido": round(prop.get("score_ruido", 0), 1),
        "Decisión": prop.get("decision", ""),
    })

cmp_df = pd.DataFrame(cmp_rows)
st.dataframe(
    cmp_df,
    width="stretch",
    column_config={
        "Precio (€)": st.column_config.NumberColumn(format="%d €"),
        "Score": st.column_config.NumberColumn(format="%.1f"),
        "Rent. (%)": st.column_config.NumberColumn(format="%.1f %%"),
    },
    hide_index=True,
)


st.divider()


# ========================
# 4. SIMULACIÓN COMPARADA
# ========================

st.markdown("### 🏦 Simulación de inversión comparada")
st.caption("Mismos parámetros para todas las propiedades. Ajusta y compara.")

col_e, col_i, col_a = st.columns(3)
entrada_pct = col_e.slider(
    "Entrada (%)", 10, 40, perfil["entrada_pct"],
    key="cmp_entrada",
) / 100
interes = col_i.slider(
    "Interés (%)", 1.0, 6.0, float(perfil["interes"]),
    key="cmp_interes",
) / 100
años = col_a.slider(
    "Años", 10, 40, perfil["años"],
    key="cmp_años",
)

reforma = st.number_input(
    "Coste reforma (€)", value=perfil["reforma"],
    key="cmp_reforma",
)
gastos_pct = st.slider(
    "Gastos compra (%)", 5, 15, perfil["gastos_pct"],
    key="cmp_gastos",
) / 100

# Mapa de alquiler por barrio
RENT_M2_MAP = {
    "Salamanca": 28, "Chamberí": 26, "Centro": 25,
    "Chamartín": 24, "Tetuán": 22, "Ciudad Lineal": 21,
    "Carabanchel": 18, "Usera": 17,
}

sim_cols = st.columns(len(props))
for i, (prop, name) in enumerate(zip(props, names)):
    with sim_cols[i]:
        precio = prop.get("precio_total", 0)
        metros = prop.get("metros", 0)
        barrio = prop.get("barrio", "")

        entrada = precio * entrada_pct
        gastos = precio * gastos_pct
        total_inv = entrada + gastos + reforma
        prestamo = precio - entrada

        r = interes / 12
        n = años * 12
        cuota = round(prestamo * (r * (1 + r)**n) / ((1 + r)**n - 1), 2)

        precio_m2_alquiler = RENT_M2_MAP.get(barrio, 20)
        base_alquiler = round(precio_m2_alquiler * metros, 2)
        alquiler = round(base_alquiler * 1.15, 2)

        gastos_mensuales = round(alquiler * 0.15, 2)
        gastos_fijos = 100
        cashflow = round(alquiler - cuota - gastos_mensuales - gastos_fijos, 2)
        rent_real = round((alquiler * 12) / total_inv * 100, 2) if total_inv else 0
        break_even = round((cuota + gastos_fijos) / (1 - 0.15), 2)

        st.markdown(f"**{name}**")
        st.metric("Inversión total", f"{int(total_inv):,} €")
        st.metric("Cuota mensual", f"{cuota:,.2f} €/mes")
        st.metric("Alquiler estimado", f"{alquiler:,.2f} €/mes")
        st.metric(
            "Cashflow",
            f"{cashflow:,.2f} €/mes",
            delta=f"{cashflow:+,.2f} €/mes",
            delta_color="normal",
        )
        st.metric("Rentabilidad real", f"{rent_real:.2f} %")

        if cashflow > 0:
            st.success("✅ Cashflow positivo")
        else:
            st.error("❌ Cashflow negativo")


st.divider()


# ========================
# 5. RECOMENDACIÓN
# ========================

st.markdown("### 🎯 Veredicto para tu perfil")

# Encontrar la mejor propiedad según score y cashflow
best_prop_idx = None
best_combined = -999

for i, (prop, name) in enumerate(zip(props, names)):
    precio = prop.get("precio_total", 0)
    metros = prop.get("metros", 0)
    barrio = prop.get("barrio", "")

    entrada = precio * entrada_pct
    gastos = precio * gastos_pct
    total_inv = entrada + gastos + reforma
    prestamo = precio - entrada
    r = interes / 12
    n = años * 12
    cuota = round(prestamo * (r * (1 + r)**n) / ((1 + r)**n - 1), 2)

    precio_m2_alquiler = RENT_M2_MAP.get(barrio, 20)
    alquiler = round(precio_m2_alquiler * metros * 1.15, 2)
    cashflow = round(alquiler - cuota - round(alquiler * 0.15, 2) - 100, 2)

    score = prop.get("score_total", 0)
    rent = prop.get("rentabilidad_estimada", 0)

    combined = score * 0.5 + cashflow * 0.3 + rent * 0.2
    if combined > best_combined:
        best_combined = combined
        best_prop_idx = i

if best_prop_idx is not None:
    best_name = names[best_prop_idx]
    st.success(
        f"🏆 Considerando score, cashflow y rentabilidad, "
        f"la mejor opción para tu perfil **{perfil['nombre']}** es "
        f"**{best_name}**."
    )

col_reset_1, col_reset_2, col_reset_3 = st.columns([1, 1, 1])
with col_reset_2:
    if st.button("🔄 Nueva comparación", type="secondary", width="stretch"):
        st.session_state.selected_for_compare = []
        st.switch_page("pages/1_Radar.py")
