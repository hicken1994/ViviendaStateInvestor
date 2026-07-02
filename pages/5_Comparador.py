"""
Comparador lateral: compara propiedades seleccionadas desde el Radar.
"""

import streamlit as st
import pandas as pd
from utils.profiles import get_perfil
from utils.charts import create_comparison_radar
from utils.auth import require_auth
from utils.plan_gate import render_feature_gate
from utils.services import get_barrio_rent

st.set_page_config(page_title="Comparador", page_icon="⚖️", layout="wide")

require_auth()
render_feature_gate("comparador", "Comparador de propiedades")

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)

props = st.session_state.get("compare_properties", [])
names = st.session_state.get("compare_names", [])

if len(props) < 2:
    st.warning("Selecciona al menos 2 propiedades desde el Radar para comparar.")
    if st.button("Volver al Radar"):
        st.switch_page("pages/1_Radar.py")
    st.stop()

st.markdown("# Comparador de propiedades")
st.caption(f"Comparando {len(props)} propiedades · Perfil activo: **{perfil['emoji']} {perfil['nombre']}**")
if st.button("Volver al Radar", type="secondary"):
    st.switch_page("pages/1_Radar.py")
st.divider()

# ── 1. KPIS ──────────────────────────────────

card_cols = st.columns(len(props))
for i, (prop, name) in enumerate(zip(props, names)):
    with card_cols[i]:
        if prop.get("image_url"):
            st.image(prop["image_url"], width="stretch")
        st.markdown(f"### {name}")
        decision = prop.get("decision", "")
        if "COMPRAR" in str(decision):
            badge = "COMPRAR"
        elif "NEGOCIAR" in str(decision):
            badge = "NEGOCIAR"
        else:
            badge = "DESCARTAR"
        st.markdown(f"**{badge}**")

        m1, m2, m3 = st.columns(3)
        m1.metric("Precio", f"{int(prop.get('precio_total', 0)):,} EUR")
        m2.metric("Score", f"{round(prop.get('score_total', 0), 1)}")
        m3.metric("Rent.", f"{round(prop.get('rentabilidad_estimada', 0), 1)}%")

        m4, m5, m6 = st.columns(3)
        m4.metric("m2", f"{int(prop.get('metros', 0))}")
        m5.metric("Habitaciones", f"{int(prop.get('rooms', 0))}")
        m6.metric("Banos", f"{int(prop.get('bathrooms', 0))}")

        m7, m8, m9 = st.columns(3)
        lift = "Si" if prop.get("has_lift") else "No"
        terrace = "Si" if prop.get("has_terrace") else "No"
        year = int(prop.get("construction_year", 0)) if prop.get("construction_year") else "—"
        m7.metric("Ascensor", lift)
        m8.metric("Terraza", terrace)
        m9.metric("Ano const.", str(year))

st.divider()

# ── 2. RADAR ──────────────────────────────────

st.markdown("### Perfil de scores — comparativa visual")
st.caption("Cada propiedad es una traza. Mientras mas grande el area, mejor equilibrada.")
fig = create_comparison_radar(properties=props, property_names=names, height=450)
st.plotly_chart(fig, width="stretch", key="cmp_radar")
st.divider()

# ── 3. TABLA COMPARATIVA ──────────────────────

st.markdown("### Tabla comparativa")
cmp_rows = []
for prop, name in zip(props, names):
    lift = "Si" if prop.get("has_lift") else "No"
    terrace = "Si" if prop.get("has_terrace") else "No"
    year = int(prop.get("construction_year", 0)) if prop.get("construction_year") else "—"
    cmp_rows.append({
        "Propiedad": name,
        "Barrio": prop.get("barrio", ""),
        "Precio": int(prop.get("precio_total", 0)),
        "m2": int(prop.get("metros", 0)),
        "EUR/m2": int(prop.get("precio_m2", 0)),
        "Habitaciones": int(prop.get("rooms", 0)),
        "Banos": int(prop.get("bathrooms", 0)),
        "Ascensor": lift,
        "Terraza": terrace,
        "Ano constr.": year,
        "Score": round(prop.get("score_total", 0), 1),
        "Rent. (%)": round(prop.get("rentabilidad_estimada", 0), 1),
        "Decision": prop.get("decision", ""),
    })

cmp_df = pd.DataFrame(cmp_rows)
st.dataframe(cmp_df, width="stretch", hide_index=True)
st.divider()

# ── 4. SIMULACION COMPARADA ──────────────────

st.markdown("### Simulacion de inversion comparada")
st.caption("Mismos parametros para todas las propiedades. Ajusta y compara.")

col_e, col_i, col_a = st.columns(3)
entrada_pct = col_e.slider("Entrada (%)", 10, 40, perfil["entrada_pct"], key="cmp_entrada") / 100
interes = col_i.slider("Interes (%)", 1.0, 6.0, float(perfil["interes"]), key="cmp_interes") / 100
anos = col_a.slider("Anos", 10, 40, perfil["años"], key="cmp_anos")

reforma = st.number_input("Coste reforma (EUR)", value=perfil["reforma"], key="cmp_reforma")
gastos_pct = st.slider("Gastos compra (%)", 5, 15, perfil["gastos_pct"], key="cmp_gastos") / 100

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
        n = anos * 12
        cuota = round(prestamo * (r * (1 + r)**n) / ((1 + r)**n - 1), 2)

        precio_m2_alquiler = get_barrio_rent(barrio, default=20)
        base_alquiler = round(precio_m2_alquiler * metros, 2)
        alquiler = round(base_alquiler * 1.15, 2)

        gastos_mensuales = round(alquiler * 0.15, 2)
        gastos_fijos = 100
        cashflow = round(alquiler - cuota - gastos_mensuales - gastos_fijos, 2)
        rent_real = round((alquiler * 12) / total_inv * 100, 2) if total_inv else 0

        st.markdown(f"**{name}**")
        st.metric("Inversion total", f"{int(total_inv):,} EUR")
        st.metric("Cuota mensual", f"{cuota:,.2f} EUR/mes")
        st.metric("Alquiler estimado", f"{alquiler:,.2f} EUR/mes")
        st.metric("Cashflow", f"{cashflow:,.2f} EUR/mes", delta=f"{cashflow:+,.2f} EUR/mes", delta_color="normal")
        st.metric("Rentabilidad real", f"{rent_real:.2f} %")
        if cashflow > 0:
            st.success("Cashflow positivo")
        else:
            st.error("Cashflow negativo")

st.divider()

# ── 5. VEREDICTO ──────────────────────────────

st.markdown("### Veredicto para tu perfil")
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
    n = anos * 12
    cuota = round(prestamo * (r * (1 + r)**n) / ((1 + r)**n - 1), 2)

    precio_m2_alquiler = get_barrio_rent(barrio, default=20)
    alquiler = round(precio_m2_alquiler * metros * 1.15, 2)
    cashflow = round(alquiler - cuota - round(alquiler * 0.15, 2) - 100, 2)
    score = prop.get("score_total", 0)
    rent = prop.get("rentabilidad_estimada", 0)

    combined = score * 0.5 + cashflow * 0.3 + rent * 0.2
    if combined > best_combined:
        best_combined = combined
        best_prop_idx = i

if best_prop_idx is not None:
    st.success(
        f"Considerando score, cashflow y rentabilidad, "
        f"la mejor opcion para tu perfil **{perfil['nombre']}** es "
        f"**{names[best_prop_idx]}**."
    )

col_r1, col_r2, col_r3 = st.columns([1, 1, 1])
with col_r2:
    if st.button("Nueva comparacion", type="secondary", width="stretch"):
        st.session_state.compare_properties = []
        st.session_state.compare_names = []
        st.switch_page("pages/1_Radar.py")
