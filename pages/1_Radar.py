import streamlit as st
import pandas as pd
from utils.db import get_top_opportunities, simulate_market, get_recent_events, get_barrio_avg_scores
from utils.images import add_images
from utils.tooltips import tooltip_help
from utils.profiles import compute_score_with_profile
from utils.charts import create_radar_chart
from components.footer import render_footer
from components.sidebar import render_sidebar
from utils.auth import require_auth
from components.score_help import render_score_breakdown
from utils.pdf_report import generar_informe_top3


require_auth()

if "compare_properties" not in st.session_state:
    st.session_state.compare_properties = []
if "compare_names" not in st.session_state:
    st.session_state.compare_names = []

perfil = render_sidebar()


# ========================
# HEADER
# ========================

st.markdown("# 📡 Radar de inversión")
st.caption("Análisis de oportunidades inmobiliarias en Madrid ordenadas por puntuación según tu perfil.")

# ── DATA FRESHNESS BADGE ──
from utils.datasources import _detect_data_source as _dds
_fuente = _dds()
if "2018" in _fuente:
    st.markdown(
        f"<span style='background: rgba(245,158,11,0.12); color: #f59e0b; padding: 0.15rem 0.6rem; "
        f"border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>"
        f"📅 Datos de {_fuente} — referencia histórica, no refleja el mercado actual</span>",
        unsafe_allow_html=True,
    )
elif "sintético" in _fuente.lower():
    st.markdown(
        f"<span style='background: rgba(245,158,11,0.12); color: #f59e0b; padding: 0.15rem 0.6rem; "
        f"border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>"
        f"🧪 Datos sintéticos — demo educativa</span>",
        unsafe_allow_html=True,
    )

st.markdown(f"**{perfil['emoji']} {perfil['nombre']}** — _{perfil['descripcion']}_")


# ========================
# 🎨 CSS SEMÁFORO FINANCIERO
# ========================

st.markdown("""
<style>
    .property-card {
        border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.75rem;
        position: relative; transition: all 0.2s;
    }
    .property-card:hover {
        transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .card-comprar {
        background: linear-gradient(135deg, rgba(34,197,94,0.08) 0%, rgba(34,197,94,0.02) 100%);
        border-left: 4px solid #22c55e;
    }
    .card-negociar {
        background: linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(245,158,11,0.02) 100%);
        border-left: 4px solid #f59e0b;
    }
    .card-descartar {
        background: linear-gradient(135deg, rgba(239,68,68,0.08) 0%, rgba(239,68,68,0.02) 100%);
        border-left: 4px solid #ef4444;
    }
    .decision-badge {
        display: inline-block; padding: 0.2rem 0.7rem; border-radius: 4px;
        font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.3px; margin-right: 0.6rem;
    }
    .badge-comprar { background: #22c55e; color: white; }
    .badge-negociar { background: #f59e0b; color: white; }
    .badge-descartar { background: #ef4444; color: white; }
    .card-title { color: white; font-size: 1.15rem; font-weight: 700; }
    .card-metrics { display: flex; gap: 1.5rem; margin: 0.6rem 0 0.3rem 0; }
    .card-metric { display: flex; flex-direction: column; }
    .metric-label { color: rgba(255,255,255,0.35); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.3px; }
    .metric-value { color: white; font-size: 1.25rem; font-weight: 700; line-height: 1.3; }
    .card-extra { color: rgba(255,255,255,0.3); font-size: 0.8rem; margin-bottom: 0.2rem; }
    .card-compact {
        border-radius: 8px; padding: 0.45rem 0.8rem; margin-bottom: 0.35rem;
        border-left: 3px solid; transition: all 0.15s;
    }
    .card-compact:hover { opacity: 0.85; }
    .rank-num { color: rgba(255,255,255,0.4); font-weight: 700; margin-right: 0.4rem; }
    .badge-small {
        display: inline-block; padding: 0.1rem 0.4rem; border-radius: 3px;
        font-size: 0.65rem; font-weight: 700; margin-right: 0.4rem; vertical-align: middle;
    }
    .rank-barrio { color: white; font-weight: 600; margin-right: 0.4rem; }
    .rank-sep { color: rgba(255,255,255,0.15); margin: 0 0.3rem; }
    .rank-value { color: white; font-weight: 600; }
    .rank-extra { color: rgba(255,255,255,0.3); font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


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
# 🥇 TOP 3 — DECISIONES DE INVERSIÓN
# ========================

st.markdown("## 🎯 Top 3 — Decisiones de inversión")
st.caption(f"Propiedades ordenadas por score. Cada card indica COMPRAR, NEGOCIAR o DESCARTAR según tu perfil **{perfil['nombre']}**.")

top3 = df.head(3).reset_index(drop=True)

for i, (_, row) in enumerate(top3.iterrows()):
    score_val = row["score_total"]
    decision_val = row.get("decision", "")

    if "COMPRAR" in str(decision_val):
        dec_icon, decision, dec_css = "🟢", "COMPRAR", "comprar"
    elif "NEGOCIAR" in str(decision_val):
        dec_icon, decision, dec_css = "🟡", "NEGOCIAR", "negociar"
    else:
        dec_icon, decision, dec_css = "🔴", "DESCARTAR", "descartar"

    precio_str = f"{int(row['precio_total']):,} €"
    score_str = f"{score_val:.1f}"
    rent_str = f"{round(row.get('rentabilidad_estimada', 0), 1)}%"

    extra_parts = [f"{int(row.get('metros', 0))} m²"]
    if row.get("rooms"):
        extra_parts.append(f"{int(row['rooms'])} hab.")
    if row.get("bathrooms"):
        extra_parts.append(f"{int(row['bathrooms'])} baños")
    extra_str = " · ".join(extra_parts)

    _is_selected = any(p.get("propiedad_id") == row.get("propiedad_id") for p in st.session_state.compare_properties)

    st.markdown(f"""
    <div class="property-card card-{dec_css}">
        <div>
            <span class="decision-badge badge-{dec_css}">{dec_icon} {decision}</span>
            <span class="card-title">{row['barrio']}</span>
        </div>
        <div class="card-metrics">
            <div class="card-metric">
                <span class="metric-label">Precio</span>
                <span class="metric-value">{precio_str}</span>
            </div>
            <div class="card-metric">
                <span class="metric-label">Score</span>
                <span class="metric-value">{score_str}</span>
            </div>
            <div class="card-metric">
                <span class="metric-label">Rentabilidad</span>
                <span class="metric-value">{rent_str}</span>
            </div>
        </div>
        <div class="card-extra">{extra_str}</div>
    </div>
    """, unsafe_allow_html=True)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🔍 Analizar propiedad", type="primary" if i == 0 else "secondary", key=f"top3_go_{i}"):
            st.session_state.selected_property = row.to_dict()
            st.switch_page("pages/3_propiedad.py")
    with col_b2:
        if _is_selected:
            if st.button("✕ Quitar de comparación", key=f"top3_rm_{i}"):
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
            if st.button("➕ Comparar", key=f"top3_add_{i}"):
                st.session_state.compare_properties.append(row.to_dict())
                st.session_state.compare_names.append(f"#{row.get('propiedad_id')} {row['barrio']}")
                st.rerun()

    # ── Exportar Top 3 a PDF ──
    pdf_bytes = generar_informe_top3(top3.to_dict("records"))
    st.download_button(
        label="📄 Exportar Top 3 como PDF",
        data=pdf_bytes,
        file_name="top_3_oportunidades.pdf",
        mime="application/pdf",
        type="secondary",
        width="stretch",
        key="pdf_top3",
    )

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

        decision = row.get("decision", "")
        if "COMPRAR" in str(decision):
            dec_css = "comprar"
        elif "NEGOCIAR" in str(decision):
            dec_css = "negociar"
        else:
            dec_css = "descartar"

        extra_r = f"{int(row.get('metros', 0))} m²"
        if row.get("rooms"):
            extra_r += f" · {int(row['rooms'])} hab."

        st.markdown(f"""
        <div class="card-compact card-{dec_css}">
            <span class="rank-num">#{idx+1}</span>
            <span class="badge-small badge-{dec_css}">{decision[:4]}</span>
            <span class="rank-barrio">{row['barrio']}</span>
            <span class="rank-value">{row['score_total']:.1f}</span>
            <span class="rank-sep">·</span>
            <span class="rank-value">{int(row['precio_total']):,} €</span>
            <span class="rank-sep">·</span>
            <span class="rank-extra">{extra_r}</span>
        </div>
        """, unsafe_allow_html=True)

        col_r1, col_r2, col_r3 = st.columns([6, 1, 1])
        with col_r1:
            st.markdown("")
        with col_r2:
            if st.button("🔍", key=f"rank_go_{idx}", help="Analizar propiedad"):
                st.session_state.selected_property = row.to_dict()
                st.switch_page("pages/3_propiedad.py")
        with col_r3:
            if _is_sel:
                if st.button("✕", key=f"rank_rm_{idx}", help="Quitar de comparación"):
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
                if st.button("➕", key=f"rank_add_{idx}", help="Comparar"):
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
