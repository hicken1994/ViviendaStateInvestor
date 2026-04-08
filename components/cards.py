import streamlit as st
from utils.tooltips import tooltip_help


def property_card(row):
    with st.container():
        st.markdown(f"""
        ### 🏠 {row['barrio']}
        💰 {int(row['precio_total']):,} €  
        📐 {row['metros']} m²  
        📊 Score: **{row['opportunity_score']}**
        """)
        
        col1, col2, col3 = st.columns(3)

        col1.metric("€/m²", int(row["precio_m2"]), help=tooltip_help("precio_m2"))
        col2.metric("Barrio €/m²", int(row["precio_m2_barrio"]), help=tooltip_help("precio_m2_barrio"))
        col3.metric("Descuento", f"{row['descuento_pct']}%", help=tooltip_help("descuento"))

        st.divider()