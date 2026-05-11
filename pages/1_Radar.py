import streamlit as st
import pandas as pd
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
st.caption("Análisis de oportunidades inmobiliarias en Madrid ordenadas por puntuación según tu perfil.")
st.markdown(f"**{perfil['emoji']} {perfil['nombre']}** — _{perfil['descripcion']}_")


# ========================
# CARGA DE DATOS + SIMULACIÓN
# ========================

df = get_top_opportunities(300)

if df.empty:
    st.warning("No hay datos disponibles")
    st.stop()

with st.sidebar:
    st.markdown("### 📊 Simulación")
    if st.button("📊 Simular cambios de mercado", key="sim_radar", use_container_width=True):
        df_sim = simulate_market(df.copy())
        st.session_state["radar_simulated"] = df_sim.to_dict("records")
        st.rerun()

if "radar_simulated" in st.session_state:
    df = pd.DataFrame(st.session_state["radar_simulated"])
    st.sidebar.success("📊 Simulación activa")
    if st.sidebar.button("🔄 Resetear datos", key="reset_radar", use_container_width=True):
        st.session_state.pop("radar_simulated", None)
        st.rerun()

df = add_images(df)

# ========================
# SCORING CON PERFIL (ÚNICO)
# ========================

profile_metrics = df.apply(
    lambda row: compute_score_with_profile(row, perfil),
    axis=1,
    result_type="expand",
)

for col in profile_metrics.columns:
    df[col] = profile_metrics[col]

df = df.sort_values("score_total", ascending=False).reset_index(drop=True)


# ========================
# KPIs
# ========================

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_opps = len(df[df["score_total"] >= perfil["min_score"]])
avg_rent = df["rentabilidad_estimada"].mean()
avg_score = df["score_total"].mean()

kpi1.metric(
    "🏠 Analizadas", len(df),
    help="Total de propiedades cargadas en el radar.",
)
kpi2.metric(
    "📈 Rent. media", f"{avg_rent:.1f}%",
    help=tooltip_help("rentabilidad_estimada"),
)
kpi3.metric(
    "📊 Score medio", f"{avg_score:.1f}",
    help=tooltip_help("score_total"),
)
kpi4.metric(
    "🎯 Para tu perfil", f"{total_opps}",
    help=f"Propiedades con score ≥ {perfil['min_score']}, el mínimo que definiste para tu perfil {perfil['nombre']}.",
)

st.divider()


# ========================
# 🥇 MEJOR OPORTUNIDAD
# ========================

best = df.iloc[0]
decision = best.get("decision", "")
score = best["score_total"]

if score >= perfil["min_score"] + 20:
    badge_color = "🟢"
    decision_label = "COMPRAR"
elif score >= perfil["min_score"]:
    badge_color = "🟡"
    decision_label = "NEGOCIAR"
else:
    badge_color = "🔴"
    decision_label = "DESCARTAR"

st.markdown("## Mejor puntuada")

col_img, col_info = st.columns([1, 2.5])

with col_img:
    if best.get("image_url"):
        st.image(best["image_url"], use_container_width=True)

with col_info:
    st.markdown(f"### {best['barrio']}")

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("💰 Precio", f"{int(best['precio_total']):,} €", help=tooltip_help("precio_total"))
    col_m2.metric("📊 Score", f"{round(score, 1)}", help=tooltip_help("score_total"))
    col_m3.metric("📈 Rentabilidad", f"{round(best.get('rentabilidad_estimada', 0), 1)}%", help=tooltip_help("rentabilidad_estimada"))

    st.markdown(
        f"🏗️ {int(best.get('metros', 0))} m² · "
        f"⏱️ {int(best.get('dias', 0))} días en mercado"
    )

    st.markdown(f"**Decisión:** {badge_color} **{decision_label}**")

    if st.button("🔍 Ver análisis completo", type="primary", key="best_btn"):
        st.session_state.selected_property = best.to_dict()
        st.switch_page("pages/3_propiedad.py")

st.divider()


# ========================
# TOP OPORTUNIDADES
# ========================

st.markdown("## Principales oportunidades")
st.caption(f"Ordenadas por score. Mínimo para tu perfil: **{perfil['min_score']}** puntos.")

top5 = df.head(7).iloc[1:]  # skip #1, ya mostrada arriba

for idx in range(0, len(top5), 3):
    cols = st.columns(3)
    chunk = top5.iloc[idx : idx + 3]

    for col, (_, row) in zip(cols, chunk.iterrows()):
        with col:
            with st.container():
                if row.get("image_url"):
                    st.image(row["image_url"], use_container_width=True)

                score_val = row["score_total"]
                rent_val = row.get("rentabilidad_estimada", 0)
                decision_val = row.get("decision", "")

                if "COMPRAR" in decision_val:
                    badge = "🟢"
                    decision_text = "COMPRAR"
                elif "NEGOCIAR" in decision_val:
                    badge = "🟡"
                    decision_text = "NEGOCIAR"
                else:
                    badge = "🔴"
                    decision_text = "DESCARTAR"

                st.markdown(f"**{badge} {row['barrio']}**")
                st.markdown(
                    f"💰 {int(row['precio_total']):,} € · "
                    f"📊 **{round(score_val, 1)}** · "
                    f"📈 {round(rent_val, 1)}%",
                )
                st.caption(
                    f"🏗️ {int(row.get('metros', 0))} m² · "
                    f"⏱️ {int(row.get('dias', 0))} días"
                )

                if st.button(
                    "Analizar →",
                    key=f"top_{idx}_{row.name}",
                    use_container_width=True,
                ):
                    st.session_state.selected_property = row.to_dict()
                    st.switch_page("pages/3_propiedad.py")

st.divider()


# ========================
# 📊 RANKING COMPLETO
# ========================

with st.expander("📊 Ranking completo — Top 20", expanded=False):
    display_df = df[
        ["barrio", "precio_total", "score_total", "rentabilidad_estimada", "decision"]
    ].head(20).copy()

    display_df.columns = [
        "Barrio", "Precio (€)", "Score Total", "Rentabilidad (%)", "Decisión",
    ]

    for c in ["Score Total", "Rentabilidad (%)"]:
        display_df[c] = display_df[c].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Precio (€)": st.column_config.NumberColumn(format="%d €"),
            "Score Total": st.column_config.ProgressColumn(
                min_value=0, max_value=100, format="%.1f"
            ),
            "Rentabilidad (%)": st.column_config.NumberColumn(format="%.2f %%"),
            "Decisión": st.column_config.TextColumn(),
        },
    )


# ========================
# 📡 ACTIVIDAD DEL MERCADO
# ========================

with st.expander("📡 Actividad del mercado", expanded=False):
    events = get_recent_events(10)

    if events.empty:
        st.info("No se han detectado movimientos recientes en el mercado.")
    else:
        for _, e in events.iterrows():
            etype = e.get("event_type", "")
            prop_id = e.get("property_id", "—")
            old_val = e.get("old_value")
            new_val = e.get("new_value")

            if etype == "price_drop":
                delta = f"de {int(old_val):,}€ a {int(new_val):,}€" if old_val and new_val else ""
                st.markdown(f"💸 **Bajada de precio** — {prop_id} {delta}")
            elif etype == "yield_up":
                delta = f"de {round(old_val, 2)}% a {round(new_val, 2)}%" if old_val and new_val else ""
                st.markdown(f"📈 **Mejora de rentabilidad** — {prop_id} {delta}")
            elif etype == "new_listing":
                st.markdown(f"🆕 **Nueva propiedad** — {prop_id}")
            else:
                st.markdown(f"📌 {etype} — {prop_id}")


# ========================
# 🧪 DETALLE DEL SCORING (AVANZADO)
# ========================

if perfil.get("mostrar_detalle_scoring"):
    with st.expander("🧪 Desglose del scoring", expanded=False):
        scoring_cols = [
            "barrio", "score_total", "score_descuento",
            "score_precio", "score_liquidez", "score_tamano",
        ]
        if "score_ruido" in df.columns:
            scoring_cols.append("score_ruido")

        available_cols = [c for c in scoring_cols if c in df.columns]
        scoring_df = df[available_cols].head(10).copy()

        for col in scoring_df.select_dtypes(include="number").columns:
            scoring_df[col] = scoring_df[col].round(2)

        st.dataframe(scoring_df, use_container_width=True)
