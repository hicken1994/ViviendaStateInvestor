import streamlit as st
from utils.profiles import get_perfil

st.set_page_config(
    page_title="AI Real Estate Copilot",
    layout="wide"
)

# Sidebar = navegación SaaS
st.sidebar.title("🏠 AI Copilot")

# ========================
# 🎯 SELECTOR DE PERFIL DE INVERSIÓN
# ========================

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Perfil de inversión")

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
    help="Tu perfil ajusta los umbrales de decisión, métricas visibles y recomendaciones."
)

st.session_state["perfil_inversion"] = perfil_seleccionado
perfil = get_perfil(str(perfil_seleccionado))

st.sidebar.caption(perfil["descripcion"])

st.sidebar.markdown("---")

# ========================
# CONTENIDO PRINCIPAL (LANDING)
# ========================

st.title("🏠 Madrid Investment Intelligence")
st.markdown("### Tu copilot de inversión inmobiliaria con IA")

st.divider()

st.info(f"🎯 Perfil activo: **{perfil['nombre']}** — {perfil['descripcion']}")

st.markdown("""
Selecciona una sección para empezar a analizar el mercado:
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 📡 Radar")
    st.caption("Detecta las mejores oportunidades del mercado en tiempo real.")
    if st.button("Ir al Radar", use_container_width=True):
        st.switch_page("pages/1_Radar.py")

with col2:
    st.markdown("### 🗺️ Mapa")
    st.caption("Visualiza oportunidades por zona en el mapa de Madrid.")
    if st.button("Ir al Mapa", use_container_width=True):
        st.switch_page("pages/2_Mapa.py")

with col3:
    st.markdown("### 🏠 Propiedad")
    st.caption("Analiza en detalle si una propiedad es buena inversión.")
    if st.button("Ir a Propiedad", use_container_width=True):
        st.switch_page("pages/3_Propiedad.py")

with col4:
    st.markdown("### 🤖 AI Copilot")
    st.caption("Tu asistente inteligente para decisiones de inversión.")
    if st.button("Ir al Copilot", use_container_width=True):
        st.switch_page("pages/4_Analisis_Detallado.py")

st.divider()

st.markdown("#### 💡 ¿Cómo funciona el perfil de inversión?")
st.markdown("""
| Perfil | Descripción | Para quién |
|--------|-------------|------------|
| 🟢 **Básico** | Prioriza seguridad y cashflow positivo | Primera inversión |
| 🟡 **Intermedio** | Equilibra rentabilidad y riesgo | Ya has invertido antes |
| 🔴 **Avanzado** | Máxima rentabilidad, tolera riesgo | Inversor experimentado |

> Cambia tu perfil en el sidebar izquierdo. Esto ajusta umbrales, métricas visibles y recomendaciones en toda la app.
""")

