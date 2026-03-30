import streamlit as st

st.set_page_config(
    page_title="AI Real Estate Copilot",
    layout="wide"
)

# Sidebar = navegación SaaS
st.sidebar.title("🏠 AI Copilot")

page = st.sidebar.radio(
    "Navegación",
    ["Radar", "Mapa", "Propiedad", "AI Copilot"]
)

st.title("Madrid Investment Intelligence")

if page == "Radar":
    st.switch_page("pages/1_Radar.py")

elif page == "Mapa":
    st.switch_page("pages/2_Mapa.py")

elif page == "Propiedad":
    st.switch_page("pages/3_Propiedad.py")

elif page == "Detalle del Analisis":
    st.switch_page("pages/4_Analisis_Detallado.py")