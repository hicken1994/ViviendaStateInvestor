import streamlit as st
import pandas as pd
import unicodedata
import pydeck as pdk
import numpy as np

from utils.db import get_top_opportunities, get_connection
from utils.images import add_images
from utils.tooltips import tooltip_help
from utils.profiles import get_perfil


# ========================
# CONSTANTES
# ========================

FIX_NAMES = {
    "vicalvaro": "Vicálvaro",
    "villa de vallecas": "Villa de Vallecas",
    "puente de vallecas": "Puente de Vallecas",
}


# ========================
# FUNCIONES AUXILIARES
# ========================

def normalize(text):
    if pd.isna(text):
        return text
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    return text


def calculate_is_premium(row):
    return row.get("score_total", 0) > 80


# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)


# ========================
# HEADER
# ========================

st.markdown("# 🗺️ Mapa de concentración — Madrid")
st.caption("Mapa térmico de oportunidades. Las zonas más cálidas concentran propiedades con mejor puntuación según tu perfil.")
st.markdown(f"**{perfil['emoji']} {perfil['nombre']}** — _{perfil['descripcion']}_")


# ========================
# CARGA DE DATOS
# ========================

conn = get_connection()
df = get_top_opportunities(300)
map_df = pd.read_sql("SELECT distrito, latitud, longitud FROM mapas_distritos", conn)
mapping_df = pd.read_sql("SELECT * FROM distrito_mapping", conn)
conn.close()

df = add_images(df)

# Normalizar y cruzar con mapa
df["distrito_raw"] = df["barrio"].apply(normalize)
map_df["distrito"] = map_df["distrito"].apply(normalize)
mapping_df["distrito_raw"] = mapping_df["distrito_raw"].apply(normalize)
mapping_df["distrito_mapa"] = mapping_df["distrito_mapa"].apply(normalize)

df = df.merge(mapping_df, on="distrito_raw", how="left")
df["distrito_final"] = df["distrito_mapa"].fillna(df["distrito_raw"])

df = df.merge(map_df, left_on="distrito_final", right_on="distrito", how="left")
df["barrio"] = df["distrito_final"].map(FIX_NAMES).fillna(df["distrito_final"].str.title())

# Calcular is_premium ANTES de que se use
df["is_premium"] = df.apply(calculate_is_premium, axis=1)


# ========================
# FILTROS — SIDEBAR
# ========================

st.sidebar.header("🔧 Filtros del mapa")

min_score = st.sidebar.slider(
    "Score mínimo", 0, 100, perfil["min_score"],
    help=tooltip_help("score_total"),
)

barrios_disponibles = sorted(df["barrio"].dropna().unique().tolist())
barrios_seleccionados = st.sidebar.multiselect(
    "Barrios", barrios_disponibles, default=[],
    help="Deja vacío para ver todos los barrios",
)

precio_max = st.sidebar.slider(
    "Precio máximo (€)", 50000, 1_000_000, perfil["max_precio"],
    step=10000, help=tooltip_help("precio_total"),
)

df = df[df["score_total"] >= min_score]
df = df[df["precio_total"] <= precio_max]
if barrios_seleccionados:
    df = df[df["barrio"].isin(barrios_seleccionados)]

if df.empty:
    st.warning("No hay propiedades con estos filtros. Ajusta los criterios en el sidebar.")
    st.stop()

df = df.reset_index(drop=True)


# ========================
# KPIs
# ========================

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("🏠 Propiedades", len(df))
kpi2.metric("💰 Precio medio", f"{int(df['precio_total'].mean()):,} €", help=tooltip_help("precio_total"))
kpi3.metric("📊 Score medio", round(df["score_total"].mean(), 1), help=tooltip_help("score_total"))


# ========================
# LEYENDA
# ========================

st.markdown("""
<div style="display:flex; gap:0.75rem; padding:0.5rem 0; align-items:center;">
    <span>📊 Concentración:</span>
    <span style="background:linear-gradient(to right, #ffffcc, #feb34c, #e63c28, #8c0028); width:160px; height:14px; border-radius:4px; display:inline-block;"></span>
    <span style="color:#999;">Baja &nbsp;→&nbsp; Alta</span>
</div>
""", unsafe_allow_html=True)


# ========================
# DATOS PARA EL MAPA TÉRMICO
# ========================

map_data = df.dropna(subset=["latitud", "longitud"]).copy()
map_data = map_data.rename(columns={"latitud": "lat", "longitud": "lon"}).reset_index(drop=True)

rng = np.random.default_rng(42)
map_data["lat"] += rng.uniform(-0.002, 0.002, size=len(map_data))
map_data["lon"] += rng.uniform(-0.002, 0.002, size=len(map_data))

map_data["score_total"] = map_data["score_total"].round(2)
map_data["precio_total"] = map_data["precio_total"].round(0).astype(int)
map_data["rentabilidad_estimada"] = map_data["rentabilidad_estimada"].round(2)


# ========================
# ZONAS (para la tabla)
# ========================

df_zones = df.dropna(subset=["distrito_final", "latitud", "longitud"])

zone_df = (
    df_zones.groupby("distrito_final")
    .agg(score_mean=("score_total", "mean"), precio_mean=("precio_total", "mean"),
         lat=("latitud", "first"), lon=("longitud", "first"))
    .reset_index()
)
zone_df["num_properties"] = df_zones.groupby("distrito_final").size().values
zone_df["barrio"] = zone_df["distrito_final"].map(FIX_NAMES).fillna(zone_df["distrito_final"].str.title())
zone_df["score_mean"] = zone_df["score_mean"].round(2)
zone_df["precio_mean"] = zone_df["precio_mean"].round(0).astype(int)


# ========================
# HEATMAP
# ========================

heatmap_layer = pdk.Layer(
    "HeatmapLayer", data=map_data,
    get_position="[lon, lat]",
    get_weight="score_total",
    aggregation="MEAN",
    radius_pixels=35,
    intensity=1.0,
    threshold=0.05,
    color_range=[
        [255, 255, 204],    # amarillo claro — baja concentración
        [255, 237, 160],    # amarillo
        [254, 178, 76],     # naranja
        [240, 130, 50],     # naranja intenso
        [230, 60, 40],      # rojo
        [140, 0, 40],       # rojo oscuro — alta concentración
    ],
)


# ========================
# RENDER MAPA
# ========================

st.pydeck_chart(pdk.Deck(
    layers=[heatmap_layer],
    initial_view_state=pdk.ViewState(latitude=40.4168, longitude=-3.7038, zoom=11.5, pitch=0),
))

st.caption(f"📍 {len(map_data)} propiedades en el mapa · Filtradas por score ≥ {min_score} y precio ≤ {precio_max:,} €")


# ========================
# SELECCIÓN DE PROPIEDAD
# ========================

st.divider()
st.markdown("## 🔍 Inspeccionar propiedad")
st.caption("Seleccioná una propiedad para ver su análisis detallado.")

selected_idx = st.selectbox(
    "Propiedad",
    range(len(map_data)),
    format_func=lambda i: (
        f"{map_data.iloc[i]['barrio']}  ·  "
        f"{map_data.iloc[i]['precio_total']:,} €  ·  "
        f"Score {map_data.iloc[i]['score_total']}"
    ),
    label_visibility="collapsed",
)

selected_row = map_data.iloc[selected_idx]

col_prev, col_action = st.columns([3, 1])

with col_prev:
    if selected_row.get("image_url"):
        st.image(selected_row["image_url"], use_container_width=True)
    st.markdown(
        f"**{selected_row['barrio']}** · 💰 {selected_row['precio_total']:,} € · "
        f"📊 Score {selected_row['score_total']} · 📈 {selected_row['rentabilidad_estimada']}%"
    )

with col_action:
    st.markdown("")
    st.markdown("")
    if st.button("🔍 Ver análisis completo", use_container_width=True, type="primary"):
        st.session_state.selected_property = selected_row.to_dict()
        st.switch_page("pages/3_propiedad.py")


# ========================
# MEJORES ZONAS
# ========================

st.divider()
st.markdown("## 📊 Zonas con mejor puntuación media")

top_zones = zone_df.sort_values("score_mean", ascending=False).head(5)

for _, zone in top_zones.iterrows():
    score = zone["score_mean"]
    badge = "🟢" if score >= 75 else ("🟡" if score >= 60 else "🔴")

    st.markdown(
        f"{badge} **{zone['barrio']}** — Score medio: **{score}** · "
        f"{int(zone['num_properties'])} propiedades · "
        f"Precio medio: {int(zone['precio_mean']):,} €"
    )


# ========================
# PROPIEDADES CON MEJOR PUNTUACIÓN
# ========================

st.divider()
st.markdown("## 📈 Propiedades con mejor puntuación")

premium_df = df[df["is_premium"] == True]

if not premium_df.empty:
    for _, opp in premium_df.iterrows():
        st.markdown(f"### {opp['barrio']}")
        if opp.get("image_url"):
            st.image(opp["image_url"], use_container_width=True)
        st.write(f"💰 Precio: **{int(opp['precio_total']):,} €**")
        st.write(f"📊 Score: **{opp['score_total']}**")
        st.write(f"📈 Rentabilidad estimada: **{opp['rentabilidad_estimada']}%**")
        st.markdown("---")
else:
    st.write("No hay propiedades con puntuación excepcional con los filtros actuales. Probá ajustar los filtros en el sidebar.")
