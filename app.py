import logging
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.profiles import get_perfil

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
from utils.db import add_is_premium_column
from utils.migrations import run_migrations
from utils.services import get_dashboard_kpis
from utils.datasources import get_dataset_stats, get_last_event_timestamp, METODOLOGIA
from utils.timefmt import time_ago
from components.footer import render_footer
from utils.auth import get_user, sign_in, sign_up, sign_out
from utils.user_store import load_preferences, save_preference, is_tour_completed, save_tour_completed

# ========================
# ⚙️ CONFIGURACIÓN GENERAL
# ========================

st.set_page_config(
    page_title="Vivienda AI — Madrid Investment Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

user = get_user()

if user is None:
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown("""
        <div style="padding: 3rem 2rem;">
            <h1 style="color: white; font-size: 2.8rem; margin-bottom: 0.5rem;">🏠 Vivienda AI</h1>
            <p style="color: rgba(255,255,255,0.5); font-size: 1.1rem; margin-bottom: 1.5rem;">
                Madrid Investment Intelligence
            </p>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.05rem; line-height: 1.7;">
                La plataforma que usa inteligencia artificial para detectar <strong>oportunidades de inversión inmobiliaria</strong> en Madrid.
                Analizamos miles de propiedades en tiempo real y te mostramos las que mejor se ajustan a tu perfil inversor.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚡ Características")
        feats = [
            ("📡 Radar de oportunidades", "Detecta propiedades infravaloradas con scoring multi-factor"),
            ("🗺️ Mapa de calor interactivo", "Visualiza concentración de oportunidades por zona"),
            ("🤖 AI Copilot", "Análisis inteligente y recomendaciones de compra"),
            ("⚖️ Comparador", "Compara 2+ propiedades lado a lado con simulación"),
            ("🚨 Alertas & Watchlist", "Sigue propiedades y recibe notificaciones de mercado"),
            ("📊 Dashboard global", "KPIs, tendencias y eventos del mercado madrileño"),
        ]
        for icon, desc in feats:
            st.markdown(f"**{icon}** — {desc}")

    with col_r:
        st.markdown("""
        <div style="padding: 3rem 0;">
            <h2 style="color: white; text-align: center;">⚡ Planes</h2>
        </div>
        """, unsafe_allow_html=True)

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); padding: 1.5rem; text-align: center; height: 100%;">
                <h3 style="color: #4ade80; margin-bottom: 0.25rem;">Starter</h3>
                <p style="font-size: 2rem; color: white; margin: 0.5rem 0;"><strong>Gratis</strong></p>
                <p style="color: rgba(255,255,255,0.5); font-size: 0.85rem;">Siempre</p>
                <hr style="border-color: rgba(255,255,255,0.08); margin: 1rem 0;">
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">50 propiedades/mes</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Radar básico</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Alertas estándar</p>
                <p style="color: rgba(255,255,255,0.3); font-size: 0.9rem;">✕ Comparador</p>
                <p style="color: rgba(255,255,255,0.3); font-size: 0.9rem;">✕ AI Copilot</p>
            </div>
            """, unsafe_allow_html=True)

        with col_p2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1a3a2e 0%, #1a2a3e 100%); border-radius: 12px; border: 2px solid #4ade80; padding: 1.5rem; text-align: center; height: 100%; position: relative;">
                <div style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #4ade80; color: #0a0a1a; padding: 2px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: 700;">RECOMENDADO</div>
                <h3 style="color: #4ade80; margin-bottom: 0.25rem; margin-top: 0.5rem;">Pro</h3>
                <p style="font-size: 2rem; color: white; margin: 0.5rem 0;"><strong>19€</strong> <span style="font-size: 1rem; color: rgba(255,255,255,0.5);">/mes</span></p>
                <hr style="border-color: rgba(255,255,255,0.08); margin: 1rem 0;">
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Propiedades ilimitadas</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Radar completo</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Comparador + Watchlist</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">AI Copilot</p>
                <p style="color: rgba(255,255,255,0.3); font-size: 0.9rem;">✕ API access</p>
            </div>
            """, unsafe_allow_html=True)

        with col_p3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); padding: 1.5rem; text-align: center; height: 100%;">
                <h3 style="color: #fbbf24; margin-bottom: 0.25rem;">Enterprise</h3>
                <p style="font-size: 2rem; color: white; margin: 0.5rem 0;"><strong>49€</strong> <span style="font-size: 1rem; color: rgba(255,255,255,0.5);">/mes</span></p>
                <hr style="border-color: rgba(255,255,255,0.08); margin: 1rem 0;">
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Todo lo de Pro</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">API de datos en tiempo real</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Datos multi-ciudad</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Soporte prioritario 24/7</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Onboarding personalizado</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.markdown("<h3 style='text-align: center; color: white;'>🔐 Accede a la plataforma</h3>", unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["Iniciar Sesión", "Crear Cuenta"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="tu@email.com", key="login_email")
                password = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_pass")
                submitted = st.form_submit_button("Iniciar Sesión", type="primary", width="stretch")
                if submitted:
                    if not email or not password:
                        st.error("Completa todos los campos")
                    else:
                        with st.spinner("Autenticando..."):
                            try:
                                resp = sign_in(email, password)
                                if resp and resp.user:
                                    st.rerun()
                                else:
                                    st.error("Email o contraseña incorrectos")
                            except Exception as e:
                                st.error(f"Error de conexión: {e}")

        with tab_signup:
            with st.form("signup_form"):
                email = st.text_input("Email", placeholder="tu@email.com", key="signup_email")
                password = st.text_input("Contraseña", type="password", placeholder="••••••••", key="signup_pass")
                confirm = st.text_input("Confirmar contraseña", type="password", placeholder="••••••••", key="signup_confirm")
                submitted = st.form_submit_button("Crear Cuenta", type="primary", width="stretch")
                if submitted:
                    if not email or not password:
                        st.error("Completa todos los campos")
                    elif password != confirm:
                        st.error("Las contraseñas no coinciden")
                    elif len(password) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres")
                    else:
                        with st.spinner("Registrando..."):
                            try:
                                resp = sign_up(email, password)
                                if resp and resp.user:
                                    st.success("Registro exitoso. Revisa tu email para confirmar la cuenta.")
                                else:
                                    st.info("Registro creado. Revisa tu email para confirmar.")
                            except Exception as e:
                                st.error(f"Error al registrarse: {e}")

    st.stop()

# Tour redirect for new users
if not is_tour_completed():
    st.switch_page("pages/0_Bienvenida.py")
    st.stop()

# ========================
# 🛠️ INICIALIZACIÓN DB (UNA SOLA VEZ)
# ========================

if "db_initialized" not in st.session_state:
    run_migrations()
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


</style>
""", unsafe_allow_html=True)

# ========================
# SIDEBAR
# ========================

st.sidebar.markdown("## 🏠 Vivienda AI")
st.sidebar.caption("Madrid Investment Intelligence")

if user:
    _plan_badge = load_preferences().get("plan", "Starter")
    _plan_emoji = {"Starter": "🆓", "Pro": "⭐", "Enterprise": "👑"}
    st.sidebar.markdown(f"👤 {user.email} {_plan_emoji.get(_plan_badge, '')}")
    if st.sidebar.button("⚙️ Mi Cuenta", width="stretch", key="mi_cuenta_sidebar"):
        st.switch_page("pages/7_Mi_Cuenta.py")
    if st.sidebar.button("🚪 Cerrar sesión", width="stretch"):
        sign_out()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Tu perfil de inversión")

perfil_opciones = {
    "basico": "🟢 Básico — Seguridad ante todo",
    "intermedio": "🟡 Intermedio — Equilibrio riesgo/rentabilidad",
    "avanzado": "🔴 Avanzado — Máxima rentabilidad",
}

if user and "perfil_loaded" not in st.session_state:
    prefs = load_preferences()
    st.session_state["perfil_inversion"] = prefs.get("perfil_inversion", "intermedio")
    st.session_state["perfil_loaded"] = True
    st.session_state["perfil_synced"] = prefs.get("perfil_inversion", "intermedio")

perfil_seleccionado = st.sidebar.radio(
    "¿Qué tipo de inversor eres?",
    list(perfil_opciones.keys()),
    format_func=lambda x: perfil_opciones[x],
    index=list(perfil_opciones.keys()).index(
        st.session_state.get("perfil_inversion", "intermedio")
    ),
    help="Tu perfil ajusta umbrales, métricas y recomendaciones en toda la app."
)

if user and perfil_seleccionado != st.session_state.get("perfil_synced"):
    save_preference("perfil_inversion", perfil_seleccionado)
    st.session_state["perfil_synced"] = perfil_seleccionado

st.session_state["perfil_inversion"] = perfil_seleccionado
perfil = get_perfil(str(perfil_seleccionado))

st.sidebar.caption(f"_{perfil['descripcion']}_")
st.sidebar.markdown("---")

user_plan = load_preferences().get("plan", "Starter") if user else "Starter"
stats = get_dataset_stats(user_plan)
last_event = get_last_event_timestamp()

with st.sidebar.expander("📊 Estado del dataset", expanded=False):
    st.markdown(
        f"- 🏠 **{stats['propiedades']:,}** propiedades  \n"
        f"- 📍 **{stats['barrios']}** barrios  \n"
        f"- 🚨 **{stats['eventos']}** eventos  \n"
        f"- 📡 {stats.get('fuente', 'sintética')}"
    )
    st.caption(f"Última actividad: {time_ago(last_event) if last_event else 'sin datos'}")
st.sidebar.markdown("---")

# ========================
# 🧭 NAVEGACIÓN PRINCIPAL
# ========================

st.markdown(
    f"<div style='margin-bottom: 1.5rem;'>"
    f"<h1 style='color: white; font-size: 1.8rem; margin-bottom: 0.25rem;'>🏠 ¿Qué quieres hacer hoy?</h1>"
    f"<p style='color: rgba(255,255,255,0.5);'>Perfil activo: {perfil['nombre']} — {perfil['descripcion']}</p>"
    f"</div>",
    unsafe_allow_html=True,
)

kpis = get_dashboard_kpis()

st.markdown("""
<style>
    .nav-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 1.5rem;
        height: 100%;
        transition: all 0.2s;
        cursor: pointer;
    }
    .nav-card:hover {
        transform: translateY(-2px);
        border-color: rgba(74,222,128,0.3);
        box-shadow: 0 8px 24px rgba(74,222,128,0.1);
    }
    .nav-card-icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .nav-card-title { color: white; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem; }
    .nav-card-desc { color: rgba(255,255,255,0.5); font-size: 0.85rem; line-height: 1.4; }
    .mini-kpi {
        background: rgba(255,255,255,0.04);
        border-radius: 10px;
        padding: 0.6rem 0.8rem;
        text-align: center;
    }
    .mini-kpi-value { color: white; font-size: 1.2rem; font-weight: 700; }
    .mini-kpi-label { color: rgba(255,255,255,0.4); font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# Mini KPIs compactos
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f"<div class='mini-kpi'><div class='mini-kpi-value'>{kpis['total_props']:,}</div>"
        f"<div class='mini-kpi-label'>🏠 Propiedades</div></div>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"<div class='mini-kpi'><div class='mini-kpi-value'>{kpis['avg_score']:.1f}</div>"
        f"<div class='mini-kpi-label'>⭐ Score medio</div></div>",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"<div class='mini-kpi'><div class='mini-kpi-value'>{kpis['oportunidades']:,}</div>"
        f"<div class='mini-kpi-label'>🎯 Oportunidades</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# TARJETAS DE NAVEGACIÓN
nav_items = [
    ("📡", "Radar", "Encontrá oportunidades con scoring inteligente", "pages/1_Radar.py"),
    ("🗺️", "Mapa", "Explorá oportunidades por zona", "pages/2_Mapa.py"),
    ("🏠", "Propiedad", "Simulá una inversión completa", "pages/3_propiedad.py"),
    ("🤖", "AI Copilot", "Analizá con inteligencia artificial", "pages/4_Analisis_Detallado.py"),
    ("⚖️", "Comparador", "Compará propiedades lado a lado", "pages/5_Comparador.py"),
    ("🚨", "Alertas", "Eventos de mercado y watchlist", "pages/6_Alertas.py"),
]

for i in range(0, len(nav_items), 2):
    row = nav_items[i : i + 2]
    cols = st.columns(2)
    for col, (icon, title, desc, page) in zip(cols, row):
        with col:
            st.markdown(
                f"<div class='nav-card'>"
                f"<div class='nav-card-icon'>{icon}</div>"
                f"<div class='nav-card-title'>{title}</div>"
                f"<div class='nav-card-desc'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button(f"Abrir {title}", key=f"nav_{title.lower().replace(' ', '_')}", width="stretch", type="primary"):
                st.switch_page(page)

st.divider()

# SECCIONES PLEGABLES
with st.expander("📊 Ver estadísticas del mercado", expanded=False):
    kpis = get_dashboard_kpis()
    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("💰 Precio medio", f"{kpis['avg_price']:,.0f} €")
    col_k2.metric("📈 Rentabilidad media", f"{kpis['avg_rent']:.1f}%")
    col_k3.metric("🚨 Eventos (7d)", f"{kpis['recent_events']}")

    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        from utils.services import get_score_distribution
        df_scores = get_score_distribution()
        mean_score = df_scores["opportunity_score"].mean()
        fig_hist = px.histogram(
            df_scores, x="opportunity_score", nbins=30,
            title="Distribución de Scores",
            color_discrete_sequence=["#1f77b4"],
            labels={"opportunity_score": "Score"},
        )
        fig_hist.add_vline(x=mean_score, line_dash="dash", line_color="#d4a017",
            annotation_text=f"Media: {mean_score:.1f}", annotation_position="top right")
        fig_hist.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=30),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig_hist, width="stretch")

    with col_ch2:
        from utils.services import get_top_barrios
        df_barrios = get_top_barrios(limit=8)
        fig_bar = px.bar(df_barrios, y="barrio", x="opportunity_index",
            title="Top Barrios por Oportunidad", orientation="h",
            text="opportunity_index", color="opportunity_index",
            color_continuous_scale="Blues", labels={"barrio": "", "opportunity_index": "Índice"})
        fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_bar.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=30),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white",
            yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(fig_bar, width="stretch")

with st.expander("📖 Metodología — ¿Cómo se calcula todo?", expanded=False):
    st.markdown(METODOLOGIA)

render_footer(show_sources=True, show_disclaimer=True)
