import streamlit as st
from utils.profiles import get_perfil

st.set_page_config(
    page_title="Vivienda AI — Madrid Investment Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# 🎨 CSS PREMIUM
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
    div[data-testid="stMetric"] label { color: rgba(255,255,255,0.7) !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: white !important; }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
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

# ========================
# LANDING
# ========================

st.markdown("# 🏠 Vivienda AI")
st.markdown("#### Inteligencia artificial aplicada a la inversión inmobiliaria en Madrid")

st.markdown("")

col_hero1, col_hero2 = st.columns([2, 1])

with col_hero1:
    st.markdown(f"""
> **Perfil activo:** {perfil['nombre']} — _{perfil['descripcion']}_

Analiza **+3.000 propiedades** en tiempo real. El sistema detecta oportunidades,
calcula rentabilidad y te dice si comprar, negociar o descartar — adaptado a tu perfil.
""")

with col_hero2:
    st.metric("🎯 Perfil", perfil["nombre"])
    st.metric("📊 Score mínimo", f"{perfil['min_score']}+")
    st.metric("📈 Rent. mínima", f"{perfil['min_rentabilidad']}%+")

st.divider()

# ========================
# NAVEGACIÓN
# ========================

st.markdown("### ¿Qué quieres hacer?")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("#### 📡 Radar")
    st.caption("Detecta las mejores oportunidades del mercado en tiempo real. Score, rentabilidad y decisión automática.")
    if st.button("Abrir Radar", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Radar.py")

with col2:
    st.markdown("#### 🗺️ Mapa")
    st.caption("Visualiza oportunidades por zona. Filtra por score, compara barrios y selecciona desde el mapa.")
    if st.button("Abrir Mapa", use_container_width=True):
        st.switch_page("pages/2_Mapa.py")

with col3:
    st.markdown("#### 🏠 Propiedad")
    st.caption("Simulación completa: hipoteca, cashflow, break-even, margen y decisión adaptada a tu perfil.")
    if st.button("Abrir Propiedad", use_container_width=True):
        st.switch_page("pages/3_propiedad.py")

with col4:
    st.markdown("#### 🤖 AI Copilot")
    st.caption("Tu asistente inteligente. Analiza propiedades con IA y recibe estrategias de compra personalizadas.")
    if st.button("Abrir Copilot", use_container_width=True):
        st.switch_page("pages/4_Analisis_Detallado.py")

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
    - Ya has invertido antes
    """)

with col_p3:
    st.error("""
    **🔴 Avanzado**
    - Cashflow mínimo: 0€/mes
    - Margen mínimo: 5%
    - Precio máximo: 1M€
    - Inversor experimentado
    """)

st.caption("Cambia tu perfil en el sidebar izquierdo → se ajustan umbrales, métricas y recomendaciones en toda la app.")
