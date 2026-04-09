import streamlit as st
from utils.db import get_top_opportunities, simulate_market, get_recent_events
from utils.images import add_images
from utils.tooltips import tooltip_help
from utils.profiles import get_perfil, compute_score_with_profile

st.title("📡 Radar de oportunidades")
st.caption("💡 El radar analiza el mercado en tiempo real y detecta las mejores oportunidades de inversión.")

# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)

st.info(f"🎯 Perfil activo: **{perfil['nombre']}** — {perfil['descripcion']}")

# ========================
# DATA
# ========================

df = get_top_opportunities(300)

if df.empty:
    st.warning("No hay datos disponibles")
    st.stop()

df = simulate_market(df)  # 🔥 ACTIVAR
df = add_images(df)

# ========================
# SCORING CON PERFIL
# ========================

profile_metrics = df.apply(
    lambda row: compute_score_with_profile(row, perfil),
    axis=1,
    result_type="expand"
)

# Reemplazar métricas con las del perfil
for col in profile_metrics.columns:
    df[col] = profile_metrics[col]

# ========================
# SCORING RADAR
# ========================

def compute_radar_score(row):
    score = 0

    rent = row.get("rentabilidad_estimada", 0)
    if rent > 8:
        score += 25
    elif rent > 6:
        score += 15
    elif rent > 5:
        score += 5

    desc = row.get("descuento", 0)
    if desc > 15:
        score += 25
    elif desc > 10:
        score += 15
    elif desc > 5:
        score += 5

    metros = row.get("metros", 0)
    precio = row.get("precio_total", 0)
    precio_m2_barrio = row.get("precio_m2_barrio", 0)

    if metros and precio_m2_barrio:
        precio_m2 = precio / metros
        if precio_m2 < precio_m2_barrio * 0.9:
            score += 20
        elif precio_m2 < precio_m2_barrio:
            score += 10

    if row.get("dias", 0) > 60:
        score += 10

    return min(score, 100)

df["score_radar"] = df.apply(compute_radar_score, axis=1)
df = df.sort_values("score_total", ascending=False).reset_index(drop=True)

# ========================
# LABEL
# ========================

def get_label(score):
    if score >= 65:
        return "🔥 Alta prioridad"
    elif score >= 45:
        return "👍 Interesante"
    else:
        return "⚠️ Débil"

# ========================
# 🏆 OPORTUNIDAD DEL DÍA (ARRIBA DE TODO)
# ========================

best = df.iloc[0]

st.markdown("## 🏆 Oportunidad del Día")
st.caption(tooltip_help("oportunidad_dia"))

if best.get("image_url"):
    st.image(best["image_url"], use_container_width=True)

st.success(f"""
🔥 MEJOR OPORTUNIDAD HOY

{best['barrio']}
💰 {int(best['precio_total']):,} €
📊 Score: {round(best['score_total'], 1)}
📈 Rentabilidad: {round(best.get('rentabilidad_estimada', 0), 1)}%

👉 Si encaja contigo, revisa ahora
👉 Este tipo de oportunidades no duran mucho
""")

if st.button("🔍 Ver oportunidad del día"):
    st.session_state.selected_property = best.to_dict()
    st.switch_page("pages/3_propiedad.py")

st.divider()

# ========================
# HERO — TOP 3
# ========================

st.markdown("## 🔥 Mejores oportunidades ahora")
st.caption(tooltip_help("score_total"))

top3 = df.head(3)

for i, row in top3.iterrows():
    label = get_label(row["score_total"])

    if row.get("image_url"):
        st.image(row["image_url"], use_container_width=True)

    st.markdown(f"""
### 🏆 {row['barrio']} — {label}

💰 {int(row['precio_total']):,} €  
📊 Score: {round(row['score_total'], 1)}  
📈 Rentabilidad: {round(row.get('rentabilidad_estimada', 0), 1)}%  

👉 **Acción: Analizar en detalle**
""")

    if st.button(f"Ver propiedad {i}"):
        st.session_state.selected_property = row.to_dict()
        st.switch_page("pages/3_propiedad.py")

st.caption("⚠️ Radar usa estimaciones. La decisión final se valida en análisis de propiedad (cashflow real).")

st.divider()

# ========================
# TABLA
# ========================

st.markdown("## 📊 Ranking de oportunidades")
st.caption("💡 Ordenado por score total. Haz clic en una columna para reordenar.")

display_df = df[[
    "barrio",
    "precio_total",
    "score_total",
    "score_radar",
    "rentabilidad_estimada"
]].copy()

display_df.columns = [
    "Barrio",
    "Precio (€)",
    "Score Total",
    "Score Radar",
    "Rentabilidad (%)"
]

display_df["Score Total"] = display_df["Score Total"].round(2)
display_df["Score Radar"] = display_df["Score Radar"].round(2)
display_df["Rentabilidad (%)"] = display_df["Rentabilidad (%)"].round(2)

st.dataframe(display_df.head(20), use_container_width=True)

st.divider()

# ========================
# 📡 EVENTOS DEL MERCADO
# ========================

st.markdown("## 🚨 Eventos del mercado")
st.caption("💡 Movimientos recientes detectados por la simulación: bajadas de precio, nuevas propiedades, mejoras de rentabilidad.")

events = get_recent_events(10)

if events.empty:
    st.info("No se han detectado eventos recientes. Se generan al simular el mercado.")
else:
    for _, e in events.iterrows():
        etype = e.get("event_type", "")
        prop_id = e.get("property_id", "—")
        old_val = e.get("old_value")
        new_val = e.get("new_value")

        if etype == "price_drop":
            delta = f"de {int(old_val):,}€ a {int(new_val):,}€" if old_val and new_val else ""
            st.error(f"💸 **Bajada de precio** — Propiedad {prop_id} {delta}")

        elif etype == "new_listing":
            st.success(f"🆕 **Nueva propiedad** detectada — {prop_id}")

        elif etype == "yield_up":
            delta = f"de {round(old_val, 2)}% a {round(new_val, 2)}%" if old_val and new_val else ""
            st.info(f"📈 **Mejora de rentabilidad** — Propiedad {prop_id} {delta}")

        else:
            st.write(f"📌 Evento: {etype} — {prop_id}")

st.divider()

# ========================
# 🔥 OPORTUNIDADES DETECTADAS (FOMO)
# ========================

st.markdown("## 🎯 Oportunidades detectadas")
st.caption(tooltip_help("oportunidades_detectadas"))

def is_opportunity(row):
    return (
        row.get("score_radar", 0) >= 65 and
        row.get("rentabilidad_estimada", 0) >= perfil["min_rentabilidad"]
    )

opps = df[df.apply(is_opportunity, axis=1)].copy()

if not opps.empty:
    opps = opps.sort_values("score_radar", ascending=False).head(5)

    for _, row in opps.iterrows():
        st.error(f"""
🔥 NUEVA OPORTUNIDAD

📍 {row['barrio']}
💰 {int(row['precio_total']):,} €
📊 Score: {round(row['score_radar'], 1)}
📈 {round(row.get('rentabilidad_estimada', 0), 1)}%
⏱️ Lleva {int(row.get('dias', 0))} días en mercado

👉 **Revisar ahora**
""")
        if st.button(f"Ver oportunidad {row['barrio']} {int(row['precio_total'])}"):
            st.session_state.selected_property = row.to_dict()
            st.switch_page("pages/3_propiedad.py")
else:
    st.info("No hay oportunidades claras ahora con tu perfil actual. Prueba a cambiar de perfil en el sidebar.")

# ========================
# 📊 DETALLE SCORING (SOLO AVANZADO)
# ========================

if perfil.get("mostrar_detalle_scoring"):
    st.divider()
    st.markdown("## 🧪 Detalle del scoring")
    st.caption("Solo visible para perfil avanzado.")

    scoring_cols = ["barrio", "score_total", "score_descuento", "score_precio", "score_liquidez", "score_tamano"]
    if "score_ruido" in df.columns:
        scoring_cols.append("score_ruido")

    available_cols = [c for c in scoring_cols if c in df.columns]
    scoring_df = df[available_cols].head(10).copy()

    for col in scoring_df.select_dtypes(include="number").columns:
        scoring_df[col] = scoring_df[col].round(2)

    st.dataframe(scoring_df, use_container_width=True)
