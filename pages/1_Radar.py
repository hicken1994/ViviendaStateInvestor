import streamlit as st
import pandas as pd
from utils.db import get_top_opportunities, simulate_market, get_recent_events, get_barrio_avg_scores
from utils.images import add_images
from utils.tooltips import tooltip_help
from utils.profiles import get_perfil, compute_score_with_profile
from utils.charts import create_radar_chart
from components.footer import render_footer
from utils.auth import require_auth
from components.score_help import render_score_breakdown


require_auth()

if "compare_properties" not in st.session_state:
    st.session_state.compare_properties = []
if "compare_names" not in st.session_state:
    st.session_state.compare_names = []

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

from utils.user_store import load_preferences as _lp_radar
_user_plan_radar = _lp_radar().get("plan", "Starter")
_is_real_data = _user_plan_radar in ("Pro", "Enterprise")

with st.sidebar:
    if not _is_real_data:
        st.markdown("### 📊 Simulación")
        if st.button("📊 Simular cambios de mercado", key="sim_radar", width="stretch"):
            df_sim = simulate_market(df.copy())
            st.session_state["radar_simulated"] = df_sim.to_dict("records")
            st.rerun()
    else:
        st.success("📡 Datos en vivo de Idealista")

if "radar_simulated" in st.session_state:
    df = pd.DataFrame(st.session_state["radar_simulated"])
    st.sidebar.success("📊 Simulación activa")
    if st.sidebar.button("🔄 Resetear datos", key="reset_radar", width="stretch"):
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
# 🥇 TOP 3 OPORTUNIDADES
# ========================

st.markdown("## 🎯 Top oportunidades para tu perfil")
st.caption(f"Las 3 mejores propiedades según tu scoring personalizado. Mínimo: **{perfil['min_score']}** pts.")

top3 = df.head(3).reset_index(drop=True)

for i, (_, row) in enumerate(top3.iterrows()):
    score_val = row["score_total"]
    decision_val = row.get("decision", "")

    if "COMPRAR" in decision_val:
        badge, dec = "🟢", "COMPRAR"
    elif "NEGOCIAR" in decision_val:
        badge, dec = "🟡", "NEGOCIAR"
    else:
        badge, dec = "🔴", "DESCARTAR"

    col_img, col_info = st.columns([1, 2.5])

    with col_img:
        if row.get("image_url"):
            st.image(row["image_url"], width="stretch")

    _is_selected = any(p.get("propiedad_id") == row.get("propiedad_id") for p in st.session_state.compare_properties)

    with col_info:
        st.markdown(f"### {badge} {row['barrio']} — {dec}")

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Precio", f"{int(row['precio_total']):,} EUR", help=tooltip_help("precio_total"))
        col_m2.metric("Score", f"{round(score_val, 1)}", help=tooltip_help("score_total"))
        col_m3.metric("Rent.", f"{round(row.get('rentabilidad_estimada', 0), 1)}%", help=tooltip_help("rentabilidad_estimada"))

        extra = f"{int(row.get('metros', 0))} m2"
        if row.get("rooms"):
            extra += f" · {int(row['rooms'])} hab."
        if row.get("bathrooms"):
            extra += f" · {int(row['bathrooms'])} banos"
        st.caption(extra)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Analizar", type="primary" if i == 0 else "secondary", key=f"top3_go_{i}"):
                st.session_state.selected_property = row.to_dict()
                st.switch_page("pages/3_propiedad.py")
        with col_b2:
            if _is_selected:
                if st.button("Quitar de comparacion", key=f"top3_rm_{i}"):
                    props = st.session_state.compare_properties
                    names = st.session_state.compare_names
                    pid = row.get("propiedad_id")
                    for idx, p in enumerate(props):
                        if p.get("propiedad_id") == pid:
                            props.pop(idx)
                            names.pop(idx)
                            break
                    st.session_state.compare_properties = props
                    st.session_state.compare_names = names
                    st.rerun()
            else:
                if st.button("Comparar", key=f"top3_add_{i}"):
                    st.session_state.compare_properties.append(row.to_dict())
                    st.session_state.compare_names.append(f"#{row.get('propiedad_id')} {row['barrio']}")
                    st.rerun()

    if i < 2:
        st.divider()

st.divider()

# ── COMPARE BAR (visible si hay seleccionadas) ──

if st.session_state.compare_properties:
    c_count = len(st.session_state.compare_properties)
    c_col1, c_col2 = st.columns([3, 1])
    with c_col1:
        st.info(f"{c_count} propiedad(es) seleccionada(s) para comparar")
    with c_col2:
        if st.button("Comparar ahora", type="primary", width="stretch"):
            st.switch_page("pages/5_Comparador.py")
    st.divider()

# ── RANKING COMPLETO ──

with st.expander(f"Ranking completo — Top 20 ({len(st.session_state.compare_properties)} seleccionadas)", expanded=False):
    top20 = df.head(20).copy()

    for idx, (_, row) in enumerate(top20.iterrows()):
        _pid = row.get("propiedad_id")
        _is_sel = any(p.get("propiedad_id") == _pid for p in st.session_state.compare_properties)

        col_r1, col_r2 = st.columns([1, 1])
        with col_r1:
            decision = row.get("decision", "")
            if "COMPRAR" in str(decision):
                badge_r = "COMPRAR"
            elif "NEGOCIAR" in str(decision):
                badge_r = "NEGOCIAR"
            else:
                badge_r = "DESCARTAR"

            extra_r = f"{int(row.get('metros', 0))} m2"
            if row.get("rooms"):
                extra_r += f" · {int(row['rooms'])} hab."
            st.markdown(
                f"**#{idx+1}** — {row['barrio']} — {badge_r} — "
                f"Score: {row['score_total']:.1f} — {int(row['precio_total']):,} EUR"
            )
            st.caption(extra_r)

        with col_r2:
            c_btn, a_btn = st.columns(2)
            with a_btn:
                if st.button("Analizar", key=f"rank_go_{idx}"):
                    st.session_state.selected_property = row.to_dict()
                    st.switch_page("pages/3_propiedad.py")
            with c_btn:
                if _is_sel:
                    if st.button("Quitar", key=f"rank_rm_{idx}"):
                        props = st.session_state.compare_properties
                        names = st.session_state.compare_names
                        for j, p in enumerate(props):
                            if p.get("propiedad_id") == _pid:
                                props.pop(j)
                                names.pop(j)
                                break
                        st.session_state.compare_properties = props
                        st.session_state.compare_names = names
                        st.rerun()
                else:
                    if st.button("Comparar", key=f"rank_add_{idx}"):
                        st.session_state.compare_properties.append(row.to_dict())
                        st.session_state.compare_names.append(
                            f"#{row.get('propiedad_id')} {row['barrio']}"
                        )
                        st.rerun()


# ========================
# 📡 ACTIVIDAD DEL MERCADO
# ========================

with st.expander("📡 Actividad del mercado", expanded=False):
    if _is_real_data:
        st.info("📡 Datos en vivo de Idealista — los eventos de mercado se generan automáticamente con cada actualización.")
    else:
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

        st.dataframe(scoring_df, width="stretch")

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
                    st.plotly_chart(fig, width="stretch", key=f"radar_top3_{i}")

st.divider()

if not df.empty and perfil.get("mostrar_detalle_scoring"):
    best_row = df.iloc[0].to_dict() if len(df) > 0 else None
    if best_row:
        render_score_breakdown(best_row, perfil, expanded=False)

render_footer(show_sources=False, show_disclaimer=True)
