import streamlit as st
import pandas as pd
import plotly.express as px
from utils.profiles import get_perfil
from utils.db import add_is_premium_column
from utils.services import (
    get_dashboard_kpis,
    get_decision_distribution,
    get_score_distribution,
    get_top_barrios,
    get_dashboard_events,
)
from utils.datasources import get_dataset_stats, get_last_event_timestamp, METODOLOGIA
from utils.timefmt import time_ago, format_timestamp
from components.footer import render_footer
from components.score_help import render_score_legend

# ========================
# ⚙️ CONFIGURACIÓN GENERAL
# ========================

st.set_page_config(
    page_title="Vivienda AI — Madrid Investment Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# 🛠️ INICIALIZACIÓN DB (UNA SOLA VEZ)
# ========================

if "db_initialized" not in st.session_state:
    add_is_premium_column()
    st.session_state["db_initialized"] = True

# ========================
# 🎨 CSS PREMIUM (CORREGIDO)
# ========================

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        color: white;
    }

    div[data-testid="stMetric"] label {
        color: rgba(255,255,255,0.7) !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: white !important;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Imágenes de propiedades: tamaño uniforme */
    div[data-testid="stImage"] img {
        max-height: 200px;
        width: 100%;
        object-fit: cover;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* Página de detalle: imagen más grande */
    .stApp [data-testid="stImage"]:only-child img {
        max-height: 320px;
    }

    /* Dashboard KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        text-align: center;
    }

    /* Event feed */
    .event-item {
        padding: 0.4rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        font-size: 0.85rem;
    }
    .event-item:last-child {
        border-bottom: none;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# SIDEBAR
# ========================

st.sidebar.markdown("## 🏠 Vivienda AI")
st.sidebar.caption("Madrid Investment Intelligence")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Tu perfil de inversión")

perfil_opciones = {
    "basico": "🟢 Básico — Seguridad ante todo",
    "intermedio": "🟡 Intermedio — Equilibrio riesgo/rentabilidad",
    "avanzado": "🔴 Avanzado — Máxima rentabilidad",
}

perfil_seleccionado = st.sidebar.radio(
    "¿Qué tipo de inversor eres?",
    list(perfil_opciones.keys()),
    format_func=lambda x: perfil_opciones[x],
    index=list(perfil_opciones.keys()).index(
        st.session_state.get("perfil_inversion", "intermedio")
    ),
    help="Tu perfil ajusta umbrales, métricas y recomendaciones en toda la app."
)

st.session_state["perfil_inversion"] = perfil_seleccionado
perfil = get_perfil(str(perfil_seleccionado))

st.sidebar.caption(f"_{perfil['descripcion']}_")
st.sidebar.markdown("---")

stats = get_dataset_stats()
last_event = get_last_event_timestamp()

st.sidebar.markdown("### 📊 Estado del dataset")
st.sidebar.markdown(
    f"- 🏠 **{stats['propiedades']:,}** propiedades  \n"
    f"- 📍 **{stats['barrios']}** barrios en **{stats['distritos']}** distritos  \n"
    f"- 🚨 **{stats['eventos']}** eventos registrados"
)
st.sidebar.caption(
    f"Última actividad: {time_ago(last_event) if last_event else 'sin datos'}"
)
st.sidebar.markdown("---")

# ========================
# 📊 FUNCIONES DEL DASHBOARD
# ========================

def format_price(price):
    """Formatea precio al estilo 245K € / 1.25M €"""
    if price >= 1_000_000:
        return f"{price / 1_000_000:.2f}M €"
    elif price >= 1_000:
        return f"{price / 1_000:.0f}K €"
    return f"{price:,.0f} €"


def format_pct(val):
    """Formatea porcentaje con 1 decimal: 8.5%"""
    return f"{val:.1f}%"


# Las funciones get_dashboard_kpis, get_decision_distribution,
# get_score_distribution, get_top_barrios y get_dashboard_events
# ahora viven en utils/services.py


EVENT_EMOJIS = {
    "price_drop": "💸 Bajada de precio",
    "yield_up":   "📈 Subida de rentabilidad",
}

# ========================
# DASHBOARD — HEADER
# ========================

st.markdown("# 🏠 Vivienda AI — Dashboard")
st.markdown("#### Inteligencia artificial aplicada a la inversión inmobiliaria en Madrid")

st.markdown(f"""
> **Perfil activo:** {perfil['nombre']} — _{perfil['descripcion']}_
""")

# ========================
# DASHBOARD — KPIs GLOBALES
# ========================

kpis = get_dashboard_kpis()

col_k1, col_k2, col_k3, col_k4, col_k5, col_k6 = st.columns(6)

with col_k1:
    st.metric("🏠 Propiedades", f"{kpis['total_props']:,}")

with col_k2:
    st.metric("⭐ Score medio", f"{kpis['avg_score']:.1f}")

with col_k3:
    st.metric("🎯 Oportunidades", f"{kpis['oportunidades']:,}")

with col_k4:
    st.metric("💰 Precio medio", format_price(kpis['avg_price']))

with col_k5:
    st.metric("📈 Rent. media", format_pct(kpis['avg_rent']))

with col_k6:
    st.metric("🚨 Eventos (7d)", f"{kpis['recent_events']}")

st.divider()

# ========================
# DASHBOARD — GRÁFICOS
# ========================

col_ch1, col_ch2 = st.columns(2)

with col_ch1:
    df_scores = get_score_distribution()
    mean_score = df_scores["opportunity_score"].mean()

    fig_hist = px.histogram(
        df_scores,
        x="opportunity_score",
        nbins=30,
        title="📊 Distribución de Scores",
        color_discrete_sequence=["#1f77b4"],
        labels={"opportunity_score": "Opportunity Score"},
    )
    fig_hist.add_vline(
        x=mean_score,
        line_dash="dash",
        line_color="#d4a017",
        annotation_text=f"Media: {mean_score:.1f}",
        annotation_position="top right",
    )
    fig_hist.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with col_ch2:
    df_barrios_top = get_top_barrios(limit=10)

    fig_bar = px.bar(
        df_barrios_top,
        y="barrio",
        x="opportunity_index",
        title="🏘️ Top Barrios por Índice de Oportunidad",
        orientation="h",
        text="opportunity_index",
        color="opportunity_index",
        color_continuous_scale="Blues",
        labels={"barrio": "", "opportunity_index": "Índice"},
    )
    fig_bar.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
    )
    fig_bar.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        yaxis=dict(autorange="reversed", showgrid=False),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
        coloraxis_showscale=False,
        hovermode="y unified",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ========================
# DASHBOARD — ANÁLISIS
# ========================

col_a1, col_a2 = st.columns(2)

with col_a1:
    # Pie chart de decisiones
    df_decisions = get_decision_distribution()

    color_map = {
        "COMPRAR":   "#00c853",
        "NEGOCIAR":  "#ffc107",
        "DESCARTAR": "#ff5252",
    }
    fig_pie = px.pie(
        df_decisions,
        names="decision",
        values="count",
        title="🎯 Distribución de Decisiones",
        color="decision",
        color_discrete_map=color_map,
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="label+percent",
        hole=0.4,
        marker=dict(line=dict(color="rgba(0,0,0,0.3)", width=1)),
    )
    fig_pie.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        showlegend=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_a2:
    st.markdown("#### 🚨 Eventos Recientes")

    df_events = get_dashboard_events(limit=5)

    if df_events.empty:
        st.info("Sin eventos recientes")
    else:
        for _, ev in df_events.iterrows():
            event_label = EVENT_EMOJIS.get(
                ev["event_type"], ev["event_type"]
            )

            # Formatear valores según el tipo
            old_val = ev["old_value"]
            new_val = ev["new_value"]
            if ev["event_type"] == "price_drop":
                old_str = format_price(old_val) if pd.notna(old_val) else "—"
                new_str = format_price(new_val) if pd.notna(new_val) else "—"
            else:
                old_str = format_pct(old_val) if pd.notna(old_val) else "—"
                new_str = format_pct(new_val) if pd.notna(new_val) else "—"

            ts = pd.Timestamp(ev["timestamp"])
            time_str = f"{ts.strftime('%d/%m %H:%M')} ({time_ago(ts)})"

            st.markdown(
                f"<div class='event-item'>"
                f"  <strong>#{ev['property_id']}</strong> &middot; {event_label}"
                f"  <br><span style='opacity:0.7;font-size:0.8rem;'>"
                f"    {old_str} → {new_str} &middot; {time_str}"
                f"  </span>"
                f"</div>",
                unsafe_allow_html=True,
            )

st.divider()

# ========================
# NAVEGACIÓN
# ========================

st.markdown("### ¿Qué quieres hacer?")

col_n1, col_n2, col_n3 = st.columns(3)

with col_n1:
    st.markdown("#### 📡 Radar")
    st.caption("Detecta las mejores oportunidades del mercado en tiempo real.")
    if st.button("Abrir Radar", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Radar.py")

with col_n2:
    st.markdown("#### 🗺️ Mapa")
    st.caption("Visualiza oportunidades por zona y compara barrios.")
    if st.button("Abrir Mapa", use_container_width=True):
        st.switch_page("pages/2_Mapa.py")

with col_n3:
    st.markdown("#### ⚖️ Comparador")
    st.caption("Compara 2+ propiedades lado a lado con simulación.")
    if st.button("Abrir Comparador", use_container_width=True):
        st.switch_page("pages/5_Comparador.py")

col_n4, col_n5, col_n6 = st.columns(3)

with col_n4:
    st.markdown("#### 🏠 Propiedad")
    st.caption("Simulación completa de inversión inmobiliaria.")
    if st.button("Abrir Propiedad", use_container_width=True):
        st.switch_page("pages/3_propiedad.py")

with col_n5:
    st.markdown("#### 🤖 AI Copilot")
    st.caption("Análisis inteligente y estrategias de compra.")
    if st.button("Abrir Copilot", use_container_width=True):
        st.switch_page("pages/4_Analisis_Detallado.py")

with col_n6:
    st.markdown("#### 🚨 Alertas")
    st.caption("Eventos de mercado y propiedades vigiladas.")
    if st.button("Abrir Alertas", use_container_width=True):
        st.switch_page("pages/6_Alertas.py")

st.divider()

# ========================
# PERFILES
# ========================

st.markdown("### 💡 ¿Cómo funciona el perfil de inversión?")

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.success("""
    **🟢 Básico**
    - Cashflow mínimo: 200€/mes
    - Margen mínimo: 25%
    - Precio máximo: 250K€
    - Ideal para tu primera inversión
    """)

with col_p2:
    st.warning("""
    **🟡 Intermedio**
    - Cashflow mínimo: 100€/mes
    - Margen mínimo: 15%
    - Precio máximo: 400K€
    - Perfil equilibrado
    """)

with col_p3:
    st.error("""
    **🔴 Avanzado**
    - Cashflow mínimo: 0€/mes
    - Margen mínimo: 5%
    - Precio máximo: 1M€
    - Inversor experimentado
    """)

st.caption(
    "Cambia tu perfil en el sidebar izquierdo → "
    "se ajustan métricas y recomendaciones en toda la app."
)

st.divider()

with st.expander("📖 Metodología — ¿Cómo se calcula todo?", expanded=False):
    st.markdown(METODOLOGIA)

render_footer(show_sources=True, show_disclaimer=True)
