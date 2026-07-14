import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.explorer_service import count_properties, get_barrios, get_page, predict_page

st.set_page_config(page_title="Explorador", page_icon="🔍", layout="wide")
require_auth()

st.markdown("# 🔍 Explorador de propiedades")
st.caption("Navegá por las 86.183 propiedades. Filtrá, ordená y compará con predicciones del ML.")

# ── Session state for page ──
if "explorer_offset" not in st.session_state:
    st.session_state.explorer_offset = 0
if "explorer_filters" not in st.session_state:
    st.session_state.explorer_filters = {}

PAGE_SIZE = 100

# ── Filters ──
barrios = ["Todos"] + get_barrios()

col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
with col_f1:
    selected_barrio = st.selectbox("Barrio", barrios, key="expl_barrio")
with col_f2:
    precio_min = st.number_input("Precio min (€)", 0, 2_000_000, 0, step=10000, key="expl_precio_min")
with col_f3:
    precio_max = st.number_input("Precio max (€)", 0, 2_000_000, 2_000_000, step=10000, key="expl_precio_max")
with col_f4:
    score_min = st.slider("Score min", 0, 100, 0, key="expl_score_min")
with col_f5:
    metros_min = st.number_input("Metros min", 0, 500, 0, step=10, key="expl_metros_min")

filters = {}
if selected_barrio and selected_barrio != "Todos":
    filters["barrio"] = selected_barrio
if precio_min > 0:
    filters["precio_min"] = precio_min
if precio_max < 2_000_000:
    filters["precio_max"] = precio_max
if score_min > 0:
    filters["score_min"] = score_min
if metros_min > 0:
    filters["metros_min"] = metros_min

total = count_properties(filters)
offset = st.session_state.explorer_offset

st.markdown(f"**{total:,}** propiedades encontradas")

# ── Pagination controls ──
col_p1, col_p2, col_p3, col_p4 = st.columns([1, 3, 3, 1])
with col_p1:
    if st.button("⬅ Anterior", disabled=offset == 0):
        st.session_state.explorer_offset = max(0, offset - PAGE_SIZE)
        st.rerun()
with col_p4:
    if st.button("Siguiente ➡", disabled=offset + PAGE_SIZE >= total):
        st.session_state.explorer_offset = offset + PAGE_SIZE
        st.rerun()
with col_p2:
    page_num = (offset // PAGE_SIZE) + 1
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    st.markdown(f"Página **{page_num}** de **{total_pages}**")
with col_p3:
    page_input = st.number_input("Ir a página", 1, total_pages, page_num, key="expl_goto")
    if page_input != page_num:
        st.session_state.explorer_offset = (page_input - 1) * PAGE_SIZE
        st.rerun()

st.divider()

# ── Load data + ML predictions ──
df = get_page(filters, offset, PAGE_SIZE)

if df.empty:
    st.info("No hay propiedades con esos filtros.")
    st.stop()

ml_decisions = predict_page(df)

# Compute rule-based decision from opportunity_score
df["decision_rule"] = df["opportunity_score"].apply(
    lambda s: "COMPRAR" if s >= 70 else ("NEGOCIAR" if s >= 50 else "DESCARTAR")
)

# Add ML label
if ml_decisions:
    df["decision_ml"] = ml_decisions
    df["coincide"] = df["decision_rule"] == df["decision_ml"]
else:
    df["decision_ml"] = "—"
    df["coincide"] = True

# ── Display table ──
display_cols = [
    "propiedad_id", "barrio", "metros", "precio_total",
    "precio_m2", "opportunity_score",
    "rentabilidad_estimada", "decision_rule", "decision_ml", "coincide",
]

available = [c for c in display_cols if c in df.columns]
st.dataframe(
    df[available].style.format({
        "precio_total": "{:,.0f}",
        "precio_m2": "{:,.0f}",
        "opportunity_score": "{:.1f}",
        "rentabilidad_estimada": "{:.1f}%",
        "metros": "{:.0f}",
    }, na_rep="-"),
    width="stretch",
    height=600,
    use_container_width=True,
    column_config={
        "propiedad_id": "ID",
        "barrio": "Barrio",
        "metros": "m²",
        "precio_total": st.column_config.NumberColumn("Precio", format="%d €"),
        "precio_m2": st.column_config.NumberColumn("€/m²", format="%d €"),
        "opportunity_score": st.column_config.NumberColumn("Score", format="%.1f"),
        "rentabilidad_estimada": st.column_config.NumberColumn("Rent.", format="%.1f%%"),
        "decision_rule": "Decisión (regla)",
        "decision_ml": "Decisión (ML)" if ml_decisions else "Decisión (ML)",
        "coincide": st.column_config.CheckboxColumn("Coincide"),
    },
)

# ── KPIs del lote actual ──
st.divider()
k1, k2, k3, k4 = st.columns(4)
k1.metric("🏠 Mostrando", f"{len(df)} propiedades")
k2.metric("📊 Score medio", f"{df['opportunity_score'].mean():.1f}")
k3.metric("💰 Precio medio", f"{int(df['precio_total'].mean()):,} €")
k4.metric("📐 m² medio", f"{int(df['metros'].mean())} m²")

if ml_decisions:
    coincidencias = df["coincide"].sum()
    k_extra = st.columns(1)[0]
    k_extra.metric(
        "🤖 Regla vs ML: coinciden",
        f"{coincidencias}/{len(df)} ({coincidencias/len(df)*100:.0f}%)",
    )

# ── Export CSV ──
st.divider()
csv = df[available].to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Exportar página como CSV",
    data=csv,
    file_name=f"propiedades_pagina_{page_num}.csv",
    mime="text/csv",
    width="stretch",
    key="expl_csv",
)

st.caption("Modelo ML: RandomForestClassifier entrenado sobre 86K propiedades. Datos históricos Idealista18 (2018).")
