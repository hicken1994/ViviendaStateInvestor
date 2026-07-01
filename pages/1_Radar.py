import streamlit as st
import pandas as pd
from utils.db import get_top_opportunities, simulate_market, get_recent_events, get_barrio_avg_scores
from utils.images import add_images
from utils.tooltips import tooltip_help
from utils.profiles import get_perfil, compute_score_with_profile
from utils.charts import create_radar_chart, create_comparison_radar, create_price_history_chart
from utils.history import generate_price_history, compute_price_trend
from components.footer import render_footer
from components.score_help import render_score_breakdown
from utils.auth import require_auth


require_auth()

# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)

if "selected_for_compare" not in st.session_state:
    st.session_state.selected_for_compare = []


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

    if best.get("flash_expires"):
        st.markdown(
            f"🔥 **Oferta flash** — Precio reducido temporalmente. "
            f"Vence: {str(best['flash_expires'])[:16]}"
        )

    st.markdown(
        f"🏗️ {int(best.get('metros', 0))} m² · "
        f"⏱️ {int(best.get('dias', 0))} días en mercado"
    )

    st.markdown(f"**Decisión:** {badge_color} **{decision_label}**")

    best_id_val = str(best.get("propiedad_id", best.get("precio_total", 0)))
    hist = generate_price_history(best_id_val, float(best.get("precio_total", 0)), days=45)
    trend = compute_price_trend(hist)
    trend_icon = "📈" if trend["trend"] == "subiendo" else ("📉" if trend["trend"] == "bajando" else "➡️")
    st.caption(f"Historico 45d: {trend_icon} {trend['change_pct']:+.1f}%  ·  Min: {int(trend['min']):,}€  ·  Max: {int(trend['max']):,}€")
    fig_spark = create_price_history_chart(hist, height=80)
    st.plotly_chart(fig_spark, use_container_width=True, key="spark_best")

    if st.button("🔍 Ver análisis completo", type="primary", key="best_btn"):
        st.session_state.selected_property = best.to_dict()
        st.switch_page("pages/3_propiedad.py")

    # Acciones: comparar + vigilar
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        cmp_key_best = f"cmp_best"
        checked_best = st.checkbox(
            "➕ Comparar", key=cmp_key_best,
            value="best" in st.session_state.get("selected_for_compare", []),
        )
        if checked_best and "best" not in st.session_state.selected_for_compare:
            st.session_state.selected_for_compare.append("best")
            st.rerun()
        elif not checked_best and "best" in st.session_state.selected_for_compare:
            st.session_state.selected_for_compare.remove("best")
            st.rerun()

    with act_col2:
        best_id = str(best.get("propiedad_id", ""))
        wl = st.session_state.get("watchlist", {"propiedades": [], "barrios": []})
        is_watched = best_id in [str(p) for p in wl.get("propiedades", [])]
        if st.button(
            "✅ Vigilada" if is_watched else "👁️ Vigilar",
            key="watch_best",
            use_container_width=True,
        ):
            if is_watched:
                wl["propiedades"] = [p for p in wl["propiedades"] if str(p) != best_id]
            else:
                wl["propiedades"].append(best_id)
            st.session_state.watchlist = wl
            st.rerun()

# --- Radar chart: perfil de la mejor puntuada vs barrio ---
barrio_nombre = best.get("barrio", "")
if barrio_nombre:
    barrio_avg = get_barrio_avg_scores(barrio_nombre, perfil)
    if barrio_avg:
        with st.expander("📡 Perfil de scores vs. barrio", expanded=False):
            fig = create_radar_chart(
                property_scores=best.to_dict(),
                barrio_avg=barrio_avg,
                property_name=f"📍 {best['barrio']}",
                barrio_name=f"🏙️ Promedio {barrio_nombre}",
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True, key="radar_best")
            st.caption(
                "Comparación del perfil de puntuación de esta propiedad "
                "vs. el promedio del barrio. Cada eje es una dimensión de inversión."
            )

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

                if row.get("flash_expires"):
                    st.markdown(f"🔥 **Flash** — vence {str(row['flash_expires'])[:16]}")

                if st.button(
                    "Analizar →",
                    key=f"top_{idx}_{row.name}",
                    use_container_width=True,
                ):
                    st.session_state.selected_property = row.to_dict()
                    st.switch_page("pages/3_propiedad.py")

                # Acciones: comparar + vigilar
                r_name = str(row.name)
                act_c1, act_c2 = st.columns(2)
                with act_c1:
                    cmp_key = f"cmp_{r_name}"
                    checked = st.checkbox(
                        "➕", key=cmp_key,
                        value=r_name in st.session_state.get("selected_for_compare", []),
                        help="Agregar a comparación",
                    )
                    if checked and r_name not in st.session_state.selected_for_compare:
                        st.session_state.selected_for_compare.append(r_name)
                        st.rerun()
                    elif not checked and r_name in st.session_state.selected_for_compare:
                        st.session_state.selected_for_compare.remove(r_name)
                        st.rerun()

                with act_c2:
                    row_id = str(row.get("propiedad_id", ""))
                    wl = st.session_state.get("watchlist", {"propiedades": [], "barrios": []})
                    is_watched = row_id in [str(p) for p in wl.get("propiedades", [])]
                    if st.button(
                        "✅" if is_watched else "👁️",
                        key=f"watch_{r_name}",
                        use_container_width=True,
                        help="Quitar de vigiladas" if is_watched else "Vigilar propiedad",
                    ):
                        if is_watched:
                            wl["propiedades"] = [p for p in wl["propiedades"] if str(p) != row_id]
                        else:
                            wl["propiedades"].append(row_id)
                        st.session_state.watchlist = wl
                        st.rerun()

st.divider()

# --- Botón de comparación ---
if len(st.session_state.get("selected_for_compare", [])) >= 2:
    cols_btn = st.columns([1, 1, 1])
    with cols_btn[1]:
        if st.button(
            f"🔄 Comparar {len(st.session_state.selected_for_compare)} seleccionadas",
            type="primary", use_container_width=True, key="cmp_grid_btn",
        ):
            selected_props = []
            prop_names = []
            for item in st.session_state.selected_for_compare:
                if item == "best":
                    selected_props.append(best.to_dict())
                    prop_names.append(f"📍 {best['barrio']}")
                else:
                    try:
                        idx = int(item)
                        row = df.loc[idx]
                        selected_props.append(row.to_dict())
                        prop_names.append(f"📍 {row['barrio']}")
                    except (ValueError, KeyError):
                        continue

            st.session_state["compare_properties"] = selected_props
            st.session_state["compare_names"] = prop_names
            st.switch_page("pages/5_Comparador.py")


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

        st.markdown("##### 📡 Perfil visual — Top 3")
        top3 = df.head(3)
        rad_cols = st.columns(3)
        for i, (_, row) in enumerate(top3.iterrows()):
            barrio_name = row.get("barrio", "")
            b_avg = get_barrio_avg_scores(barrio_name, perfil) if barrio_name else {}
            if b_avg:
                with rad_cols[i]:
                    fig = create_radar_chart(
                        property_scores=row.to_dict(),
                        barrio_avg=b_avg,
                        property_name=barrio_name,
                        barrio_name=f"Promedio {barrio_name}",
                        height=280,
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"radar_top3_{i}")

st.divider()

if not df.empty and perfil.get("mostrar_detalle_scoring"):
    best_row = df.iloc[0].to_dict() if len(df) > 0 else None
    if best_row:
        render_score_breakdown(best_row, perfil, expanded=False)

render_footer(show_sources=False, show_disclaimer=True)
