import streamlit as st
from utils.auth import require_auth, get_user
from utils.user_store import save_tour_completed

st.set_page_config(
    page_title="Bienvenido — Vivienda AI",
    page_icon="🎉",
    layout="centered",
)

require_auth()

user = get_user()

st.markdown("""
<style>
    .tour-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .tour-card h3 { color: white; margin-bottom: 0.5rem; }
    .tour-card p { color: rgba(255,255,255,0.7); }
    .tour-step { margin-bottom: 1rem; }
    .tour-step summary { cursor: pointer; font-weight: 600; color: #4ade80; }
    .tour-step[open] summary { margin-bottom: 0.75rem; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="tour-card" style="text-align: center;">', unsafe_allow_html=True)
    st.markdown("## 🎉 ¡Bienvenido a Vivienda AI!")
    st.markdown(f"👤 **{user.email}**")
    st.markdown("---")
    st.markdown(
        "Estás a punto de descubrir cómo la inteligencia artificial "
        "puede transformar tu manera de invertir en inmuebles en Madrid."
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("## 🗺️ Tour guiado")

st.markdown('<div class="tour-card">', unsafe_allow_html=True)
st.markdown("Explora cada funcionalidad a tu ritmo. Haz clic en cada paso para expandirlo.")

steps = [
    ("📊 Dashboard Global",
     "Tu centro de comando. Acá ves KPIs del mercado madrileño: cantidad de propiedades, "
     "score promedio, oportunidades detectadas, precio y rentabilidad media. "
     "También ves la distribución de scores, el top de barrios y los eventos recientes."),
    ("📡 Radar de Oportunidades",
     "La herramienta estrella. El Radar analiza miles de propiedades y aplica un "
     "scoring multifactor en 5 dimensiones: Descuento (40pts), Precio vs Barrio (25pts), "
     "Liquidez (15pts), Tamaño (10pts) y Ruido (10pts). "
     "El score se ajusta según tu perfil de inversor (Básico, Intermedio, Avanzado)."),
    ("🗺️ Mapa de Calor",
     "Visualiza la concentración de oportunidades en el mapa de Madrid. "
     "Las zonas más calientes tienen mayor densidad de propiedades con alto score. "
     "Usa el distrito mapping para entender qué zonas priorizar."),
    ("🏠 Análisis de Propiedad",
     "Simulación completa de compra: precios, rentabilidad estimada, cashflow mensual, "
     "break-even, margen. Compará contra el promedio del barrio y tomá decisiones "
     "informadas. Generá históricos de precio con sparklines."),
    ("🤖 AI Copilot",
     "El asistente inteligente que analiza propiedades por vos. "
     "Usa OpenAI para generar recomendaciones de compra, estrategias de negociación "
     "y análisis de riesgo. Ideal para inversores que quieren un segundo opinion."),
    ("⚖️ Comparador",
     "Selecciona 2+ propiedades desde el Radar y compáralas lado a lado. "
     "Vas a ver KPIs comparativos, un radar overlay, tabla de diferencias "
     "y una simulación compartida. Decisión informada en segundos."),
    ("🚨 Alertas & Watchlist",
     "Sigue propiedades y barrios. Recibe notificaciones de bajadas de precio "
     "y subidas de rentabilidad. Las Flash Drops te muestran propiedades con "
     "caídas temporales. Todo persiste entre sesiones."),
    ("🎯 Perfiles de Inversor",
     "En el sidebar puedes elegir entre 3 perfiles: Básico (seguridad, cashflow mínimo 200€/mes), "
     "Intermedio (equilibrio, cashflow mínimo 100€/mes) y Avanzado (máxima rentabilidad, "
     "sin cashflow mínimo). Cada perfil ajusta los umbrales de decisión en TODA la app."),
]

for i, (title, desc) in enumerate(steps, 1):
    with st.expander(f"**Paso {i}:** {title}", expanded=(i == 1)):
        st.markdown(desc)

st.markdown("</div>", unsafe_allow_html=True)

st.divider()

col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
with col_b2:
    st.markdown(
        "¿Listo para empezar a invertir de forma inteligente?"
    )
    if st.button("🚀 Ir al Dashboard", type="primary", use_container_width=True):
        save_tour_completed()
        st.switch_page("app.py")

st.caption("Siempre puedes volver a este tour desde la configuración de tu perfil.")
