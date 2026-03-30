import streamlit as st
import sqlite3
import pandas as pd
from openai import OpenAI

client = OpenAI()

conn = sqlite3.connect("real_estate.db")

st.title("AI Real Estate Copilot - Madrid")
pregunta = st.text_input("Pregunta sobre inversión inmobiliaria")

def get_data():
    query = """
    SELECT barrio, metros, habitaciones, precio_total,
           precio_m2, precio_m2_barrio, descuento_pct, opportunity_score
    FROM vista_oportunidades_ai
    ORDER BY opportunity_score DESC
    LIMIT 100
    """
    return pd.read_sql(query, conn)

if pregunta:
    df = get_data()

    prompt = f"""
Eres un analista de inversión inmobiliaria en Madrid.

Usuario pregunta:
{pregunta}

Dataset:
{df.to_dict(orient="records")}

Responde como asesor inmobiliario.
"""

    with st.spinner("Analizando oportunidades inmobiliarias..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

    st.markdown("### Análisis de inversión")
    st.write(response.choices[0].message.content)
else:
    st.info("Escribe una pregunta para comenzar.")