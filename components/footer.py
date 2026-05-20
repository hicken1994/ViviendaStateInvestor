import streamlit as st
from utils.datasources import FUENTES, DISCLAIMER, DATASET_VERSION, DATASET_DATE


def render_datasource_badge():
    cols = st.columns(4)
    for i, (key, fuente) in enumerate(FUENTES.items()):
        with cols[i]:
            icon = {
                "ine": "📊",
                "ministerio": "🏛️",
                "idealista": "🏠",
                "fotocasa": "📱",
            }.get(key, "📌")
            st.markdown(
                f"**{icon} {fuente['nombre']}**  \n"
                f"<small>{fuente['descripcion']}</small>",
                unsafe_allow_html=True,
            )


def render_footer(show_sources: bool = True, show_disclaimer: bool = True):
    st.divider()
    st.markdown(f"##### ℹ️ Sobre los datos")
    st.caption(
        f"**Vivienda AI** v{DATASET_VERSION} · Datos simulados basados en el mercado de Madrid · "
        f"{DATASET_DATE}"
    )

    if show_sources:
        render_datasource_badge()

    if show_disclaimer:
        st.markdown(DISCLAIMER)

    st.caption(
        "Hecho con ❤️ para inversores inmobiliarios — "
        "[Reportar un problema](mailto:dev@vivienda-ai.demo)"
    )
