import streamlit as st
import pandas as pd
import unicodedata
import pydeck as pdk
import numpy as np

from utils.db import get_top_opportunities, get_connection
from utils.tooltips import tooltip_help
from utils.profiles import get_perfil

st.set_page_config(layout="wide")

st.title("🗺️ Radar de oportunidades inmobiliarias")
st.caption("💡 Visualiza las mejores oportunidades de inversión en el mapa de Madrid.")

# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)

st.info(f"🎯 Perfil activo: **{perfil['nombre']}** — {perfil['descripcion']}")

# ========================
# DB
# ========================

conn = get_connection()

# ========================
# FUNCIONES
# ========================

def normalize(text):
    if pd.isna(text):
        return text
    text = text.strip().lower()
    text = unicodedata.normalize('NFKD', text)\
        .encode('ascii', 'ignore')\
        .decode('utf-8')
    return text

# ========================
# DATA
# ========================

df = get_top_opportunities(300)

map_df = pd.read_sql(
    "SELECT distrito, latitud, longitud FROM mapas_distritos",
    conn
)

mapping_df = pd.read_sql(
    "SELECT * FROM distrito_mapping",
    conn
)

# ========================
# NORMALIZAR (CLAVE)
# ========================

df["distrito_raw"] = df["barrio"].apply(normalize)

map_df["distrito"] = map_df["distrito"].apply(normalize)

mapping_df["distrito_raw"] = mapping_df["distrito_raw"].apply(normalize)
mapping_df["distrito_mapa"] = mapping_df["distrito_mapa"].apply(normalize)

# ========================
# MAPEO
# ========================

df = df.merge(mapping_df, on="distrito_raw", how="left")

df["distrito_final"] = df["distrito_mapa"].fillna(df["distrito_raw"])

df = df.merge(
    map_df,
    left_on="distrito_final",
    right_on="distrito",
    how="left"
)

# ========================
# LABEL VISUAL (FIX PRO)
# ========================

fix_names = {
    "vicalvaro": "Vicálvaro",
    "villa de vallecas": "Villa de Vallecas",
    "puente de vallecas": "Puente de Vallecas"
}

df["barrio"] = df["distrito_final"].map(fix_names).fillna(df["distrito_final"].str.title())

# ========================
# FILTROS
# ========================

st.sidebar.header("Filtros")

min_score = st.sidebar.slider(
    "Opportunity Score mínimo",
    0, 100, 60,
    help=tooltip_help("score_total")
)

df = df[df["score_total"] >= min_score]

# ========================
# MÉTRICAS
# ========================

col1, col2, col3 = st.columns(3)

col1.metric("📊 Oportunidades", len(df))
col2.metric("💰 Precio medio", f"{int(df['precio_total'].mean()):,} €" if len(df) else "0 €", help=tooltip_help("precio_total"))
col3.metric("🔥 Score medio", round(df["score_total"].mean(), 1) if len(df) else 0, help=tooltip_help("score_total"))

# ========================
# MAPA BASE
# ========================

st.subheader("📍 Oportunidades activas")

map_plot = df.dropna(subset=["latitud", "longitud"]).copy()

map_plot = map_plot.rename(columns={
    "latitud": "lat",
    "longitud": "lon"
})

# ========================
# JITTER
# ========================

rng = np.random.default_rng(42)

map_plot["lat"] += rng.uniform(-0.002, 0.002, size=len(map_plot))
map_plot["lon"] += rng.uniform(-0.002, 0.002, size=len(map_plot))

# ========================
# FORMATO DATOS (PRO)
# ========================

map_plot["score_total"] = map_plot["score_total"].round(2)
map_plot["rentabilidad_estimada"] = map_plot["rentabilidad_estimada"].round(2)
map_plot["precio_total"] = map_plot["precio_total"].round(0).astype(int)

map_plot["num_properties"] = 1
map_plot["score_mean"] = map_plot["score_total"]
map_plot["precio_mean"] = map_plot["precio_total"]

# ========================
# VISUAL PROPIEDADES
# ========================

def get_color(score):
    if score >= 75:
        return [0, 180, 0]
    elif score >= 60:
        return [255, 200, 0]
    else:
        return [220, 50, 50]

def get_radius(score):
    return 5 + (score * 0.15)

map_plot["color"] = map_plot["score_total"].apply(get_color)
map_plot["radius"] = map_plot["score_total"].apply(get_radius)

points_layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_plot,
    get_position="[lon, lat]",
    get_fill_color="color",
    get_radius="radius",
    radius_units="pixels",
    pickable=True,
    opacity=0.85,
    stroked=True,
    get_line_color=[255, 255, 255],
    line_width_min_pixels=1,
)

# ========================
# ZONAS (FIX REAL)
# ========================

df = df.dropna(subset=["distrito_final", "latitud", "longitud"])

zone_df = df.groupby("distrito_final").agg({
    "latitud": "first",
    "longitud": "first",
    "score_total": "mean",
    "precio_total": "mean"
}).reset_index()

zone_df["num_properties"] = df.groupby("distrito_final").size().values

zone_df = zone_df.rename(columns={
    "latitud": "lat",
    "longitud": "lon",
    "score_total": "score_mean",
    "precio_total": "precio_mean"
})

# LABEL BONITO
zone_df["barrio"] = zone_df["distrito_final"].map(fix_names).fillna(zone_df["distrito_final"].str.title())

# FORMATO
zone_df["score_mean"] = zone_df["score_mean"].round(2)
zone_df["precio_mean"] = zone_df["precio_mean"].round(0).astype(int)

zone_df["score_total"] = zone_df["score_mean"]
zone_df["precio_total"] = zone_df["precio_mean"]
zone_df["rentabilidad_estimada"] = 0

# ========================
# VISUAL ZONAS
# ========================

def get_zone_color(score):
    if score >= 75:
        return [0, 120, 255, 80]
    elif score >= 60:
        return [255, 180, 0, 60]
    else:
        return [180, 180, 180, 40]

zone_df["color"] = zone_df["score_mean"].apply(get_zone_color)

zone_df["radius"] = 10 + (zone_df["score_mean"] * 0.5)

zones_layer = pdk.Layer(
    "ScatterplotLayer",
    data=zone_df,
    get_position="[lon, lat]",
    get_fill_color="color",
    get_radius="radius",
    radius_units="pixels",
    pickable=True,
    opacity=0.15,
)

# ========================
# TOOLTIP PERFECTO
# ========================

tooltip = {
    "html": """
    <b>{barrio}</b><br/>
    💰 {precio_total} €<br/>
    📊 Score: {score_total}<br/>
    📈 Rentabilidad: {rentabilidad_estimada}%<br/>
    <hr/>
    🏠 {num_properties} oportunidades<br/>
    📊 Score zona: {score_mean}<br/>
    💰 Precio medio: {precio_mean} €
    """,
    "style": {
        "backgroundColor": "#111",
        "color": "white"
    }
}

# ========================
# VIEW
# ========================

view_state = pdk.ViewState(
    latitude=40.4168,
    longitude=-3.7038,
    zoom=11,
)

# ========================
# RENDER
# ========================

st.pydeck_chart(pdk.Deck(
    layers=[zones_layer, points_layer],
    initial_view_state=view_state,
    tooltip=tooltip
))

# ========================
# CONTADOR
# ========================

st.caption(f"Mostrando {len(map_plot)} oportunidades en el mapa")

# ========================
# SELECCIÓN
# ========================

st.divider()
st.subheader("📋 Seleccionar propiedad")

selection_df = map_plot[["barrio", "precio_total", "score_total"]]

selected_index = st.selectbox(
    "Elige una propiedad",
    selection_df.index,
    format_func=lambda i: f"{selection_df.loc[i, 'barrio']} | {selection_df.loc[i, 'precio_total']:,} € | Score {selection_df.loc[i, 'score_total']}"
)

if st.button("🔍 Ver propiedad"):
    st.session_state.selected_property = map_plot.loc[selected_index].to_dict()
    st.switch_page("pages/3_propiedad.py")

# ========================
# TOP
# ========================

st.divider()
st.subheader("🔥 Mejores oportunidades")

top = df.sort_values("score_total", ascending=False).head(5)

for _, row in top.iterrows():
    st.markdown(f"""
    **{row['barrio']}**  
    💰 {int(row['precio_total']):,} €  
    📊 Score: {row['score_total']}  
    """)