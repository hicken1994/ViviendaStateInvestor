import streamlit as st
from utils.db import get_top_opportunities, simulate_market, get_recent_events
from utils.images import add_images
from utils.tooltips import tooltip_help
from utils.profiles import get_perfil, compute_score_with_profile


# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)

# ========================
# HEADER
# ========================

st.markdown("# 📡 Radar de inversión")
st.caption("Análisis en tiempo real de +3.000 propiedades en Madrid · Actualizado con cada visita")

st.markdown(f"**{perfil['emoji']} {perfil['nombre']}** — _{perfil['descripcion']}_")

# ========================
# DATA
# ========================

df = get_top_opportunities(300)

if df.empty:
    st.warning("No hay datos disponibles")
    st.stop()

df = simulate_market(df)
df = add_images(df)

# ========================
# SCORING CON PERFIL
# ========================

profile_metrics = df.apply(
    lambda row: compute_score_with_profile(row, perfil),
    axis=1,
    result_type="expand"
)

for col in profile_metrics.columns:
    df[col] = profile_metrics[col]


def compute_radar_score(row):
    score = 0
    rent = row.get("rentabilidad_estimada", 0)
    if rent > 8: score += 25
    elif rent > 6: score += 15
    elif rent > 5: score += 5

    desc = row.get("descuento", 0)
    if desc > 15: score += 25
    elif desc > 10: score += 15
    elif desc > 5: score += 5

    metros = row.get("metros", 0)
    precio = row.get("precio_total", 0)
    precio_m2_barrio = row.get("precio_m2_barrio", 0)
    if metros and precio_m2_barrio:
        precio_m2 = precio / metros
        if precio_m2 < precio_m2_barrio * 0.9: score += 20
        elif precio_m2 < precio_m2_barrio: score += 10

    if row.get("dias", 0) > 60: score += 10
    return min(score, 100)


df["score_radar"] = df.apply(compute_radar_score, axis=1)
df = df.sort_values("score_total", ascending=False).reset_index(drop=True)

# ========================
# KPIs GLOBALES
# ========================

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_opps = len(df[df["score_total"] >= perfil["min_score"]])
avg_rent = df["rentabilidad_estimada"].mean()
avg_score = df["score_total"].mean()
price_drops = len(get_recent_events(100).query("event_type == 'price_drop'")) if not get_recent_events(100).empty else 0

kpi1.metric("🏠 Oportunidades", f"{total_opps}", help="Propiedades que superan tu score mínimo")
kpi2.metric("📈 Rent. media", f"{avg_rent:.1f}%", help=tooltip_help("rentabilidad_estimada"))
kpi3.metric("📊 Score medio", f"{avg_score:.1f}", help=tooltip_help("score_total"))
kpi4.metric("💸 Bajadas hoy", f"{price_drops}", help="Propiedades con bajada de precio detectada")

st.divider()

# ========================
# 🏆 OPORTUNIDAD DEL DÍA
# ========================

best = df.iloc[0]

st.markdown("## 🏆 Oportunidad del Día")

col_img, col_info = st.columns([1, 2])

with col_img:
    if best.get("image_url"):
        st.image(best["image_url"], use_container_width=True)

with col_info:
    st.markdown(f"### {best['barrio']}")

    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Precio", f"{int(best['precio_total']):,} €")
    m2.metric("📊 Score", f"{round(best['score_total'], 1)}")
    m3.metric("📈 Rentabilidad", f"{round(best.get('rentabilidad_estimada', 0), 1)}%")

    st.markdown(f"""
    🏗️ {int(best.get('metros', 0))} m² · ⏱️ {int(best.get('dias', 0))} días en mercado
    """)

    if st.button("🔍 Analizar esta oportunidad", type="primary", key="best_btn"):
        st.session_state.selected_property = best.to_dict()
        st.switch_page("pages/3_propiedad.py")

st.divider()

# ========================
# 🔥 TOP OPORTUNIDADES — CARDS
# ========================

st.markdown("## 🔥 Top oportunidades")
st.caption("Las mejores propiedades ordenadas por score. Haz clic para analizar en detalle.")

top5 = df.head(6).iloc[1:]  # skip best, ya mostrado arriba

for idx in range(0, len(top5), 3):
    cols = st.columns(3)
    chunk = top5.iloc[idx:idx+3]

    for col, (_, row) in zip(cols, chunk.iterrows()):
        with col:
            if row.get("image_url"):
                st.image(row["image_url"], use_container_width=True)

            score = row["score_total"]
            if score >= 65:
                badge = "🟢"
            elif score >= 45:
                badge = "🟡"
            else:
                badge = "🔴"

            st.markdown(f"**{badge} {row['barrio']}**")
            st.caption(f"💰 {int(row['precio_total']):,} € · 📊 {round(score, 1)} · 📈 {round(row.get('rentabilidad_estimada', 0), 1)}%")
            st.caption(f"🏗️ {int(row.get('metros', 0))} m² · ⏱️ {int(row.get('dias', 0))} días")

            if st.button("Analizar →", key=f"top_{idx}_{row.name}", use_container_width=True):
                st.session_state.selected_property = row.to_dict()
                st.switch_page("pages/3_propiedad.py")

st.divider()

# ========================
# 📊 RANKING COMPLETO
# ========================

with st.expander("📊 Ranking completo — Top 20", expanded=False):
    display_df = df[[
        "barrio", "precio_total", "score_total", "score_radar", "rentabilidad_estimada"
    ]].head(20).copy()

    display_df.columns = ["Barrio", "Precio (€)", "Score Total", "Score Radar", "Rentabilidad (%)"]

    for c in ["Score Total", "Score Radar", "Rentabilidad (%)"]:
        display_df[c] = display_df[c].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Precio (€)": st.column_config.NumberColumn(format="%d €"),
            "Score Total": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
            "Score Radar": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
            "Rentabilidad (%)": st.column_config.NumberColumn(format="%.2f %%"),
        }
    )

# ========================
# 🚨 EVENTOS DEL MERCADO
# ========================

with st.expander("🚨 Actividad del mercado", expanded=False):
    events = get_recent_events(10)

    if events.empty:
        st.info("No se han detectado eventos recientes.")
    else:
        for _, e in events.iterrows():
            etype = e.get("event_type", "")
            prop_id = e.get("property_id", "—")
            old_val = e.get("old_value")
            new_val = e.get("new_value")

            if etype == "price_drop":
                delta = f"de {int(old_val):,}€ a {int(new_val):,}€" if old_val and new_val else ""
                st.error(f"💸 **Bajada de precio** — {prop_id} {delta}")
            elif etype == "yield_up":
                delta = f"de {round(old_val, 2)}% a {round(new_val, 2)}%" if old_val and new_val else ""
                st.info(f"📈 **Mejora de rentabilidad** — {prop_id} {delta}")
            elif etype == "new_listing":
                st.success(f"🆕 **Nueva propiedad** — {prop_id}")
            else:
                st.write(f"📌 {etype} — {prop_id}")

# ========================
# 🎯 OPORTUNIDADES DETECTADAS (FOMO)
# ========================

st.divider()
st.markdown("## 🎯 Oportunidades que encajan contigo")
st.caption(f"Filtrado para perfil **{perfil['nombre']}** — score ≥ 65 y rentabilidad ≥ {perfil['min_rentabilidad']}%")

def is_opportunity(row):
    return (
        row.get("score_radar", 0) >= 65 and
        row.get("rentabilidad_estimada", 0) >= perfil["min_rentabilidad"]
    )

opps = df[df.apply(is_opportunity, axis=1)].copy()

if not opps.empty:
    opps = opps.sort_values("score_radar", ascending=False).head(5)

    for opp_idx, (_, row) in enumerate(opps.iterrows()):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown(f"""
**📍 {row['barrio']}** · 💰 {int(row['precio_total']):,} € · 📊 Score {round(row['score_radar'], 1)} · 📈 {round(row.get('rentabilidad_estimada', 0), 1)}% · ⏱️ {int(row.get('dias', 0))} días
""")
        with col_b:
            if st.button("Revisar →", key=f"opp_{opp_idx}", use_container_width=True):
                st.session_state.selected_property = row.to_dict()
                st.switch_page("pages/3_propiedad.py")
else:
    st.info("No hay oportunidades que encajen con tu perfil ahora. Prueba a cambiar de perfil en el sidebar.")

# ========================
# 📊 DETALLE SCORING (SOLO AVANZADO)
# ========================

if perfil.get("mostrar_detalle_scoring"):
    with st.expander("🧪 Detalle del scoring (avanzado)", expanded=False):
        scoring_cols = ["barrio", "score_total", "score_descuento", "score_precio", "score_liquidez", "score_tamano"]
        if "score_ruido" in df.columns:
            scoring_cols.append("score_ruido")

        available_cols = [c for c in scoring_cols if c in df.columns]
        scoring_df = df[available_cols].head(10).copy()

        for col in scoring_df.select_dtypes(include="number").columns:
            scoring_df[col] = scoring_df[col].round(2)

        st.dataframe(scoring_df, use_container_width=True)
