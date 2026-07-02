import streamlit as st
from utils.profiles import get_perfil
from utils.user_store import load_preferences, save_preference
from utils.datasources import get_dataset_stats, get_last_event_timestamp
from utils.timefmt import time_ago
from utils.auth import get_user, sign_out


def _inject_global_css():
    st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppToolbar {display: none;}
    .stAppDeployButton {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    section[data-testid="stSidebar"] + div {padding-top: 0;}
    .block-container { padding-top: 1rem; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1rem; border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        color: white;
    }
    div[data-testid="stMetric"] label { color: rgba(255,255,255,0.7) !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: white !important; }
    .stButton > button { border-radius: 8px; font-weight: 600; transition: all 0.2s; }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    div[data-testid="stImage"] img {
        max-height: 200px; width: 100%; object-fit: cover;
        border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stApp [data-testid="stImage"]:only-child img { max-height: 320px; }
</style>
""", unsafe_allow_html=True)


def render_sidebar() -> dict:
    _inject_global_css()
    user = get_user()

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
        help="Tu perfil ajusta umbrales, métricas y recomendaciones en toda la app.",
    )

    if user and perfil_seleccionado != st.session_state.get("perfil_synced"):
        save_preference("perfil_inversion", perfil_seleccionado)
        st.session_state["perfil_synced"] = perfil_seleccionado

    st.session_state["perfil_inversion"] = perfil_seleccionado
    perfil = get_perfil(str(perfil_seleccionado))

    st.sidebar.caption(f"_{perfil['descripcion']}_")
    st.sidebar.markdown("---")

    # ── NAVEGACIÓN RÁPIDA ──
    st.sidebar.markdown("### 🧭 Navegación")
    nav_items = [
        ("📡 Radar", "pages/1_Radar.py"),
        ("🗺️ Mapa", "pages/2_Mapa.py"),
        ("🏠 Propiedad", "pages/3_propiedad.py"),
        ("🤖 AI Copilot", "pages/4_Analisis_Detallado.py"),
        ("⚖️ Comparador", "pages/5_Comparador.py"),
        ("🚨 Alertas", "pages/6_Alertas.py"),
    ]
    for label, page in nav_items:
        if st.sidebar.button(label, key=f"nav_{page.split('/')[-1].replace('.py','')}", width="stretch"):
            st.switch_page(page)

    st.sidebar.markdown("---")

    # ── DATASET STATUS ──
    user_plan = load_preferences().get("plan", "Starter") if user else "Starter"
    stats = get_dataset_stats(user_plan)
    last_event = get_last_event_timestamp()

    _sync_icon = {"ok": "✅", "fallback": "⚡", "error": "❌"}.get(
        st.session_state.get("sync_status"), "❓"
    )
    st.sidebar.caption(
        f"{_sync_icon} Sync: {st.session_state.get('sync_status', 'pendiente')}"
    )

    with st.sidebar.expander("📊 Estado del dataset", expanded=False):
        fuente = stats.get("fuente", "—")
        anyo = "2018" if "2018" in fuente else "sintético"
        st.markdown(
            f"- 🏠 **{stats['propiedades']:,}** propiedades  \n"
            f"- 📍 **{stats['barrios']}** barrios  \n"
            f"- 🚨 **{stats['eventos']}** eventos  \n"
            f"- 📡 {fuente}  \n"
            f"- 📅 Año del dataset: **{anyo}**"
        )
        if stats["propiedades"] == 0:
            st.warning("No hay datos cargados — revisá secrets de Supabase")
        st.caption(
            f"Última actividad: {time_ago(last_event) if last_event else 'sin datos'}"
        )

    # ── UPGRADE CTA (solo usuarios Starter) ──
    if user and _plan_badge == "Starter":
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
        <div style="background: linear-gradient(135deg, rgba(74,222,128,0.06) 0%, rgba(74,222,128,0.02) 100%);
                    border: 1px solid rgba(74,222,128,0.15); border-radius: 12px; padding: 1rem; text-align: center;">
            <div style="font-size: 1.2rem; margin-bottom: 0.3rem;">⭐</div>
            <div style="color: white; font-weight: 700; font-size: 0.95rem; margin-bottom: 0.3rem;">Actualizá a Pro</div>
            <div style="color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-bottom: 0.8rem; line-height: 1.4;">
            Propiedades ilimitadas · Comparador · AI Copilot
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.sidebar.button("⭐ Próximamente", key="upgrade_cta", width="stretch"):
            st.toast("⚡ Plan Pro disponible pronto. Conectaremos la API de Idealista cuando tengamos tracción.")

    return perfil
