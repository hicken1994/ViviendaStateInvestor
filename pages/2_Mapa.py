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
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)

# ========================
# HEADER
# ========================

st.markdown("# 🗺️ Mapa de inversión — Madrid")
st.caption("Explora oportunidades en el mapa. Cada punto es una propiedad. Los colores indican calidad de la oportunidad.")

st.markdown(f"**{perfil['emoji']} {perfil['nombre']}** — _{perfil['descripcion']}_")

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

conn = get_connection()

df = get_top_opportunities(300)

map_df = pd.read_sql(
    "SELECT distrito, latitud, longitud FROM mapas_distritos",
    conn
)

mapping_df = pd.read_sql(
    "SELECT * FROM distrito_mapping",
    conn
)

conn.close()

df = add_images(df)

# ========================
# NORMALIZAR Y MAPEAR
# ========================

df["distrito_raw"] = df["barrio"].apply(normalize)
map_df["distrito"] = map_df["distrito"].apply(normalize)
mapping_df["distrito_raw"] = mapping_df["distrito_raw"].apply(normalize)
mapping_df["distrito_mapa"] = mapping_df["distrito_mapa"].apply(normalize)

df = df.merge(mapping_df, on="distrito_raw", how="left")
df["distrito_final"] = df["distrito_mapa"].fillna(df["distrito_raw"])

df = df.merge(
    map_df,
    left_on="distrito_final",
    right_on="distrito",
    how="left"
)

fix_names = {
    "vicalvaro": "Vicálvaro",
    "villa de vallecas": "Villa de Vallecas",
    "puente de vallecas": "Puente de Vallecas"
}

df["barrio"] = df["distrito_final"].map(fix_names).fillna(df["distrito_final"].str.title())

# ========================
# FILTROS — SIDEBAR
# ========================

st.sidebar.header("🔧 Filtros del mapa")

min_score = st.sidebar.slider(
    "Score mínimo",
    0, 100, perfil["min_score"],
    help=tooltip_help("score_total")
)

barrios_disponibles = sorted(df["barrio"].dropna().unique().tolist())
barrios_seleccionados = st.sidebar.multiselect(
    "Barrios",
    barrios_disponibles,
    default=[],
    help="Deja vacío para ver todos los barrios"
)

precio_max = st.sidebar.slider(
    "Precio máximo (€)",
    50000, 1000000, perfil["max_precio"],
    step=10000,
    help=tooltip_help("precio_total")
)

# Aplicar filtros
df = df[df["score_total"] >= min_score]
df = df[df["precio_total"] <= precio_max]

if barrios_seleccionados:
    df = df[df["barrio"].isin(barrios_seleccionados)]

if df.empty:
    st.warning("No hay propiedades con estos filtros. Ajusta los criterios en el sidebar.")
    st.stop()

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
<div style="display:flex; gap:1.5rem; padding:0.5rem 0;">
    <span>🟢 <b>Score ≥ 75</b> — Excelente</span>
    <span>🟡 <b>Score ≥ 60</b> — Buena</span>
    <span>🔴 <b>Score < 60</b> — Débil</span>
    <span>⭕ <b>Círculos grandes</b> = Zonas con más propiedades</span>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ========================
# PREPARAR MAPA
# ========================

map_plot = df.dropna(subset=["latitud", "longitud"]).copy()
map_plot = map_plot.rename(columns={"latitud": "lat", "longitud": "lon"})

rng = np.random.default_rng(42)
map_plot["lat"] += rng.uniform(-0.002, 0.002, size=len(map_plot))
map_plot["lon"] += rng.uniform(-0.002, 0.002, size=len(map_plot))

map_plot["score_total"] = map_plot["score_total"].round(2)
map_plot["rentabilidad_estimada"] = map_plot["rentabilidad_estimada"].round(2)
map_plot["precio_total"] = map_plot["precio_total"].round(0).astype(int)
map_plot["num_properties"] = 1
map_plot["score_mean"] = map_plot["score_total"]
map_plot["precio_mean"] = map_plot["precio_total"]

# ========================
# COLORES Y RADIOS
# ========================

def get_color(score):
    if score >= 75: return [34, 197, 94]
    elif score >= 60: return [234, 179, 8]
    else: return [239, 68, 68]

def get_radius(score):
    return 6 + (score * 0.12)

map_plot["color"] = map_plot["score_total"].apply(get_color)
map_plot["radius"] = map_plot["score_total"].apply(get_radius)

# ========================
# CAPA PROPIEDADES
# ========================

points_layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_plot,
    get_position="[lon, lat]",
    get_fill_color="color",
    get_radius="radius",
    radius_units="pixels",
    pickable=True,
    opacity=0.9,
    stroked=True,
    get_line_color=[255, 255, 255],
    line_width_min_pixels=1,
)

# ========================
# CAPA ZONAS
# ========================

df_zones = df.dropna(subset=["distrito_final", "latitud", "longitud"])

zone_df = df_zones.groupby("distrito_final").agg({
    "latitud": "first",
    "longitud": "first",
    "score_total": "mean",
    "precio_total": "mean"
}).reset_index()

zone_df["num_properties"] = df_zones.groupby("distrito_final").size().values
zone_df = zone_df.rename(columns={"latitud": "lat", "longitud": "lon", "score_total": "score_mean", "precio_total": "precio_mean"})

zone_df["barrio"] = zone_df["distrito_final"].map(fix_names).fillna(zone_df["distrito_final"].str.title())
zone_df["score_mean"] = zone_df["score_mean"].round(2)
zone_df["precio_mean"] = zone_df["precio_mean"].round(0).astype(int)
zone_df["score_total"] = zone_df["score_mean"]
zone_df["precio_total"] = zone_df["precio_mean"]
zone_df["rentabilidad_estimada"] = 0

def get_zone_color(score):
    if score >= 75: return [34, 197, 94, 60]
    elif score >= 60: return [234, 179, 8, 50]
    else: return [150, 150, 150, 30]

zone_df["color"] = zone_df["score_mean"].apply(get_zone_color)
zone_df["radius"] = 12 + (zone_df["score_mean"] * 0.4)

zones_layer = pdk.Layer(
    "ScatterplotLayer",
    data=zone_df,
    get_position="[lon, lat]",
    get_fill_color="color",
    get_radius="radius",
    radius_units="pixels",
    pickable=True,
    opacity=0.2,
)

# ========================
# TOOLTIP
# ========================

tooltip = {
    "html": """
    <div style="font-family:system-ui; padding:4px;">
        <b style="font-size:14px;">{barrio}</b><br/>
        <hr style="margin:4px 0; border-color:rgba(255,255,255,0.2)"/>
        💰 <b>{precio_total}</b> €<br/>
        📊 Score: <b>{score_total}</b><br/>
        📈 Rentabilidad: <b>{rentabilidad_estimada}%</b><br/>
        <hr style="margin:4px 0; border-color:rgba(255,255,255,0.2)"/>
        🏠 {num_properties} oportunidades en zona<br/>
        📊 Score zona: {score_mean}<br/>
        💰 Precio medio zona: {precio_mean} €
    </div>
    """,
    "style": {"backgroundColor": "#111", "color": "white", "borderRadius": "8px", "padding": "8px"}
}

# ========================
# RENDER MAPA
# ========================

st.pydeck_chart(pdk.Deck(
    layers=[zones_layer, points_layer],
    initial_view_state=pdk.ViewState(
        latitude=40.4168,
        longitude=-3.7038,
        zoom=11.5,
        pitch=0,
    ),
    tooltip=tooltip
))

st.caption(f"📍 {len(map_plot)} propiedades en el mapa · Filtradas por score ≥ {min_score} y precio ≤ {precio_max:,}€")

# ========================
# SELECCIÓN DE PROPIEDAD
# ========================

st.divider()
st.markdown("## 🔍 Seleccionar propiedad")
st.caption("Elige una propiedad del mapa para analizarla en detalle.")

selection_df = map_plot[["barrio", "precio_total", "score_total"]].copy()

selected_index = st.selectbox(
    "Propiedad",
    selection_df.index,
    format_func=lambda i: f"{selection_df.loc[i, 'barrio']}  ·  {selection_df.loc[i, 'precio_total']:,} €  ·  Score {selection_df.loc[i, 'score_total']}",
    label_visibility="collapsed"
)

selected_row = map_plot.loc[selected_index]

# Preview
col_prev, col_action = st.columns([3, 1])

with col_prev:
    if selected_row.get("image_url"):
        st.image(selected_row["image_url"], use_container_width=True)

    st.markdown(f"**{selected_row['barrio']}** · 💰 {int(selected_row['precio_total']):,} € · 📊 Score {selected_row['score_total']} · 📈 {selected_row['rentabilidad_estimada']}%")

with col_action:
    st.markdown("")
    st.markdown("")
    if st.button("🔍 Analizar propiedad", use_container_width=True, type="primary"):
        st.session_state.selected_property = selected_row.to_dict()
        st.switch_page("pages/3_propiedad.py")

# ========================
# TOP ZONAS
# ========================

st.divider()
st.markdown("## 🏆 Mejores zonas para invertir")

top_zones = zone_df.sort_values("score_mean", ascending=False).head(5)

for _, zone in top_zones.iterrows():
    score = zone["score_mean"]
    if score >= 75: badge = "🟢"
    elif score >= 60: badge = "🟡"
    else: badge = "🔴"

    st.markdown(f"""
{badge} **{zone['barrio']}** — Score medio: **{score}** · {int(zone['num_properties'])} propiedades · Precio medio: {int(zone['precio_mean']):,}€
""")

# ========================
# PREMIUM CARDS
# ========================

st.divider()
st.markdown("## 🌟 Propiedades Premium")

# ========================
# VALIDAR COLUMNA 'is_premium'
# ========================

if "is_premium" not in df.columns:
    st.error("La columna 'is_premium' no existe en el DataFrame. Verifica el cálculo previo.")
    st.stop()

premium_df = df[df["is_premium"] == True]

if not premium_df.empty:
    for _, opp in premium_df.iterrows():
        st.markdown(f"### 🌟 **{opp['barrio']}** 🌟")
        if opp['image_url']:
            st.image(opp['image_url'], use_column_width=True)
        st.write(f"💰 Precio: **{int(opp['precio_total']):,} €**")
        st.write(f"📊 Score: **{opp['score_total']}**")
        st.write(f"📈 Rentabilidad estimada: **{opp['rentabilidad_estimada']}%**")
        st.write("🔔 **¡Propiedad exclusiva!** Actúa rápido antes de que sea tarde.")
        st.markdown("---")
else:
    st.write("No hay propiedades premium disponibles con los filtros actuales.")

# ========================
# CALCULAR PROPIEDADES PREMIUM
# ========================

def calculate_is_premium(row):
    return row.get("score_total", 0) > 80  # Umbral para propiedades premium

df["is_premium"] = df.apply(calculate_is_premium, axis=1)
