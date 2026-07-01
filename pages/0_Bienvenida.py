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

if "tour_step" not in st.session_state:
    st.session_state.tour_step = 0

TOTAL_STEPS = 8

steps = [
    {
        "icon": "📊",
        "title": "Dashboard Global",
        "detail": (
            "Tu centro de comando. Aquí ves en tiempo real:\n\n"
            "- **KPIs del mercado**: propiedades analizadas, score promedio, oportunidades detectadas\n"
            "- **Distribución de scores**: gráfico que muestra cómo se distribuyen las puntuaciones\n"
            "- **Top barrios**: los 10 barrios con mayor índice de oportunidad\n"
            "- **Eventos recientes**: bajadas de precio y mejora de rentabilidad\n\n"
            "Es el primer lugar para entender el estado del mercado madrileño."
        ),
        "tip": "💡 Cambia tu perfil de inversor en el sidebar izquierdo y el dashboard se adapta automáticamente.",
    },
    {
        "icon": "📡",
        "title": "Radar de Oportunidades",
        "detail": (
            "El corazón de Vivienda AI. Evalúa cada propiedad con un **scoring multifactor** en 5 dimensiones:\n\n"
            "| Dimensión | Máx | ¿Qué mide? |\n"
            "|-----------|-----|------------|\n"
            "| **Descuento** | 40 pts | Diferencia entre precio y valor de mercado del barrio |\n"
            "| **Precio vs Barrio** | 25 pts | Ratio precio/m² vs media del barrio |\n"
            "| **Liquidez** | 15 pts | Facilidad para alquilar según tamaño |\n"
            "| **Tamaño** | 10 pts | Metros cuadrados útiles |\n"
            "| **Ruido** | 10 pts | Nivel de ruido estimado de la zona |\n\n"
            "El score total se pondera según tu **perfil de inversor**."
        ),
        "tip": "🎯 Las propiedades con score ≥ 70 son COMPRAR, ≥ 50 son NEGOCIAR, el resto DESCARTAR.",
    },
    {
        "icon": "🗺️",
        "title": "Mapa de Calor",
        "detail": (
            "Visualiza la concentración de oportunidades en el mapa de Madrid.\n\n"
            "- Las zonas **más cálidas** (rojo/naranja) tienen mayor densidad de propiedades con alto score\n"
            "- Las zonas **frías** (azul) tienen menos oportunidades según tu perfil\n"
            "- Usa el selector de distrito para filtrar por zona\n\n"
            "Ideal para identificar rápidamente **qué barrios prioritarios** explorar."
        ),
        "tip": "🔍 Combiná el mapa con el Radar: primero ubicación, después análisis detallado.",
    },
    {
        "icon": "🏠",
        "title": "Análisis de Propiedad",
        "detail": (
            "Simulación completa de inversión para cualquier propiedad:\n\n"
            "- **Precio, Score y Rentabilidad estimada** de un vistazo\n"
            "- **Histórico de precio** con sparkline mostrando tendencia a 60 días\n"
            "- **Simulación financiera**: entrada, hipoteca, intereses, cuota mensual\n"
            "- **Alquiler estimado** basado en precio/m² del barrio\n"
            "- **Cashflow mensual**, break-even y margen\n"
            "- **Recomendación adaptada** a tu perfil de inversor\n\n"
            "Todo lo que necesitas para decidir si una propiedad es buena inversión."
        ),
        "tip": "🧮 Ajustá los sliders de entrada, interés y años para ver cómo cambia tu cashflow.",
    },
    {
        "icon": "🤖",
        "title": "AI Copilot",
        "detail": (
            "Tu asistente personal con inteligencia artificial.\n\n"
            "Seleccioná una propiedad desde el Radar y el Copilot analiza:\n\n"
            "- **Recomendación de compra** con fundamentos\n"
            "- **Estrategia de negociación** según el margen\n"
            "- **Análisis de riesgo** personalizado\n"
            "- **Comparación con alternativas** en el mismo barrio\n\n"
            "Usa OpenAI para generar análisis en lenguaje natural, "
            "como si tuvieras un asesor inmobiliario senior sentado a tu lado."
        ),
        "tip": "🌟 Disponible en plan Pro y Enterprise. Actualiza desde Mi Cuenta.",
    },
    {
        "icon": "⚖️",
        "title": "Comparador",
        "detail": (
            "Seleccioná 2 o más propiedades desde el Radar y compáralas lado a lado:\n\n"
            "- **KPIs comparativos**: precio, score, rentabilidad, metros, días en mercado\n"
            "- **Radar overlay**: todas las propiedades superpuestas en un gráfico radial\n"
            "- **Tabla de diferencias**: cada dimensión de scoring detallada\n"
            "- **Simulación compartida**: mismos parámetros financieros para todas\n"
            "- **Veredicto inteligente**: el sistema elige la mejor opción según tu perfil\n\n"
            "Tomá decisiones informadas en segundos."
        ),
        "tip": "✅ En el Radar, hacé clic en ➕ en las propiedades que quieras comparar y luego en 'Comparar N seleccionadas'.",
    },
    {
        "icon": "🚨",
        "title": "Alertas y Watchlist",
        "detail": (
            "Seguí propiedades y barrios para no perderte ninguna oportunidad:\n\n"
            "- **Propiedades vigiladas**: recibí alertas cuando cambian de precio\n"
            "- **Barrios vigilados**: monitoreá actividad completa de una zona\n"
            "- **Flash Drops**: propiedades con caídas temporales de precio\n"
            "- **Filtros por tipo de evento**: bajadas, mejoras de rentabilidad, nuevas propiedades\n\n"
            "Todo persiste entre sesiones — tu watchlist te espera donde la dejaste."
        ),
        "tip": "👁️ Usá el botón 'Vigilar' en cualquier propiedad del Radar para agregarla a tu watchlist.",
    },
    {
        "icon": "🎯",
        "title": "Perfiles de Inversor",
        "detail": (
            "Elegí tu perfil en el sidebar y toda la app se adapta:\n\n"
            "| Perfil | Cashflow mínimo | Precio máximo | Ideal para |\n"
            "|--------|----------------|---------------|------------|\n"
            "| 🟢 **Básico** | 200€/mes | 250.000€ | Primera inversión, seguridad |\n"
            "| 🟡 **Intermedio** | 100€/mes | 400.000€ | Inversores con experiencia |\n"
            "| 🔴 **Avanzado** | 0€/mes | 1.000.000€ | Máxima rentabilidad |\n\n"
            "Cada perfil ajusta:\n"
            "- Los **pesos del scoring** (prioriza liquidez vs rentabilidad)\n"
            "- Los **umbrales de decisión** (COMPRAR / NEGOCIAR / DESCARTAR)\n"
            "- Las **métricas visibles** y la profundidad del análisis"
        ),
        "tip": "🔄 Podés cambiar de perfil en cualquier momento desde el sidebar — no hay compromiso.",
    },
]

st.markdown("""
<style>
    .tour-hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 2rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .tour-hero h1 { color: white; margin-bottom: 0.25rem; }
    .tour-hero p { color: rgba(255,255,255,0.6); font-size: 1.05rem; }
    .tour-step-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 2rem;
        min-height: 320px;
    }
    .tour-step-container h2 { color: white; margin-bottom: 1rem; }
    .tour-step-container p, .tour-step-container li { color: rgba(255,255,255,0.75); line-height: 1.6; }
    .tour-step-container table { width: 100%; margin: 0.75rem 0; }
    .tour-step-container th, .tour-step-container td {
        border: 1px solid rgba(255,255,255,0.1);
        padding: 0.4rem 0.75rem;
        font-size: 0.85rem;
    }
    .tour-step-container th {
        background: rgba(255,255,255,0.05);
        color: rgba(255,255,255,0.6);
        font-weight: 600;
    }
    .tour-step-container td { color: rgba(255,255,255,0.75); }
    .tour-tip {
        background: rgba(74,222,128,0.1);
        border: 1px solid rgba(74,222,128,0.2);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-top: 1rem;
        color: #4ade80;
        font-size: 0.9rem;
    }
    .tour-progress-container {
        margin: 1rem 0;
    }
    .tour-progress-bar {
        height: 6px;
        background: rgba(255,255,255,0.1);
        border-radius: 3px;
        overflow: hidden;
    }
    .tour-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #4ade80, #22d3ee);
        border-radius: 3px;
        transition: width 0.3s ease;
    }
    .tour-progress-label {
        display: flex;
        justify-content: space-between;
        color: rgba(255,255,255,0.4);
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

col_hero1, col_hero2, col_hero3 = st.columns([1, 2, 1])
with col_hero2:
    st.markdown('<div class="tour-hero">', unsafe_allow_html=True)
    st.markdown("## 🎉 ¡Bienvenido a Vivienda AI!")
    st.markdown(f"👤 **{user.email}**")
    st.markdown("---")
    st.markdown(
        "Descubrí cómo la inteligencia artificial puede transformar "
        "tu manera de invertir en inmuebles en Madrid."
    )
    st.markdown("</div>", unsafe_allow_html=True)

step = st.session_state.tour_step
current = steps[step]

progress_pct = int((step + 1) / TOTAL_STEPS * 100)

st.markdown("<div class='tour-progress-container'>", unsafe_allow_html=True)
st.markdown(
    f"<div class='tour-progress-bar'><div class='tour-progress-fill' style='width:{progress_pct}%'></div></div>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<div class='tour-progress-label'><span>Paso {step + 1} de {TOTAL_STEPS}</span><span>{progress_pct}% completado</span></div>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="tour-step-container">', unsafe_allow_html=True)
st.markdown(f"## {current['icon']} {current['title']}")
st.markdown(current['detail'])
st.markdown(f"<div class='tour-tip'>{current['tip']}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

nav_cols = st.columns([1, 1, 1, 1, 1])
with nav_cols[1]:
    if step > 0:
        if st.button("← Anterior", width="stretch"):
            st.session_state.tour_step -= 1
            st.rerun()

with nav_cols[3]:
    if step < TOTAL_STEPS - 1:
        if st.button("Siguiente →", type="primary", width="stretch"):
            st.session_state.tour_step += 1
            st.rerun()

if step == TOTAL_STEPS - 1:
    st.divider()
    col_final1, col_final2, col_final3 = st.columns([1, 2, 1])
    with col_final2:
        st.markdown(
            "### 🚀 ¡Ya conocés todas las funcionalidades!"
        )
        st.markdown(
            "Estás listo para empezar a invertir de forma inteligente. "
            "Recordá que siempre podés volver a este tour desde **Mi Cuenta**."
        )
        if st.button("🚀 Ir al Dashboard", type="primary", width="stretch"):
            save_tour_completed()
            st.switch_page("app.py")

st.caption("Usá los botones de navegación para moverte entre pasos.")
