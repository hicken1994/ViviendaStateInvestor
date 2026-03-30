def property_card(row):
    with st.container():
        st.markdown(f"""
        ### 🏠 {row['barrio']}
        💰 {int(row['precio_total']):,} €  
        📐 {row['metros']} m²  
        📊 Score: **{row['opportunity_score']}**
        """)
        
        col1, col2, col3 = st.columns(3)

        col1.metric("€/m²", int(row["precio_m2"]))
        col2.metric("Barrio €/m²", int(row["precio_m2_barrio"]))
        col3.metric("Descuento", f"{row['descuento_pct']}%")

        st.divider()