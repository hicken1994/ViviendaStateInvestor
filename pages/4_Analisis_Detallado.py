import streamlit as st
from utils.db import get_top_opportunities
from openai import OpenAI
import json

client = OpenAI()

st.title("🤖 Copilot de inversión")

# ========================
# MODO
# ========================

mode = st.radio("Modo", ["Propiedad", "Mercado"], horizontal=True)

if st.button("🧹 Limpiar contexto"):
    st.session_state.pop("copilot_property", None)

prop = st.session_state.get("copilot_property")

df = get_top_opportunities(300)

# ========================
# 🏠 HEADER PROPIEDAD
# ========================

if mode == "Propiedad":

    if not prop:
        st.warning("Selecciona una propiedad primero")
        st.stop()

    st.markdown("## 🏠 Propiedad")

    col1, col2, col3 = st.columns(3)
    col1.metric("Precio", f"{int(prop.get('precio_total',0)):,} €")
    col2.metric("Cashflow", f"{int(prop.get('cashflow',0))} €/mes")
    col3.metric("Score", prop.get("score_modelo"))

    st.caption(prop.get("barrio"))

# ========================
# 🧠 DEAL FINDER (CLAVE)
# ========================

def get_top_deals():

    df_sorted = df.sort_values("score_radar", ascending=False)

    return df_sorted.head(5)

# ========================
# 💰 PRECIO OBJETIVO SIMPLE
# ========================

def estimate_target_price(row):
    precio = row.get("precio_total", 0)
    descuento = row.get("descuento", 0)

    if descuento > 10:
        return int(precio * 0.9)
    elif descuento > 5:
        return int(precio * 0.95)
    else:
        return int(precio * 0.97)

# ========================
# 🟢 MODO MERCADO (IMPRESCINDIBLE)
# ========================

def run_market():

    st.markdown("## 🔥 Oportunidades reales hoy")

    deals = get_top_deals()

    best = deals.iloc[0]

    st.success(f"""
👉 MEJOR OPORTUNIDAD:

{best['barrio']}  
💰 {int(best['precio_total']):,} €  
📊 Score: {round(best['score_radar'],1)}

💸 Oferta recomendada: {estimate_target_price(best):,} €
""")

    st.markdown("## 📊 Top oportunidades")

    for _, row in deals.iterrows():

        target = estimate_target_price(row)

        st.markdown(f"""
### {row['barrio']}
💰 {int(row['precio_total']):,} €  
📊 Score: {round(row['score_radar'],1)}  

👉 Ofertar: {target:,} €
""")

        if st.button(f"Analizar {row['barrio']} {row['precio_total']}"):
            st.session_state.selected_property = row.to_dict()
            st.switch_page("pages/3_Propiedad.py")

# ========================
# 🟡 MODO PROPIEDAD (DECISOR)
# ========================

def run_property():

    decision = prop.get("recomendacion_modelo")
    score = prop.get("score_modelo", 0)

    st.markdown("## 🧠 Decisión final")

    if "BUENA" in decision:
        st.success("🟢 COMPRAR")
    elif "JUSTA" in decision:
        st.warning("🟡 NEGOCIAR")
    else:
        st.error("🔴 DESCARTAR")

    st.markdown("### 🎯 Acción inmediata")

    if score > 70:
        st.success("👉 Comprar o lanzar oferta inmediata")
    elif score > 50:
        st.warning("👉 Negociar (5–10%)")
    else:
        st.error("👉 No entrar en esta operación")

    # ========================
    # IA SOLO PARA MEJORA
    # ========================

    prompt = f"""
Eres un inversor experto.

Propiedad:
{prop}

Mejora la estrategia de compra.

Devuelve JSON:
{{
 "precio_objetivo": number,
 "acciones": [],
 "riesgos": []
}}
"""

    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    try:
        txt = res.choices[0].message.content
        js = txt[txt.index("{"):txt.rindex("}")+1]
        data = json.loads(js)

        st.markdown("### 🤖 Optimización IA")

        if data.get("precio_objetivo"):
            st.success(f"💸 Precio objetivo IA: {int(data['precio_objetivo']):,} €")

        for a in data.get("acciones", []):
            st.write(f"- {a}")

        if data.get("riesgos"):
            st.markdown("⚠️ Riesgos")
            for r in data["riesgos"]:
                st.write(f"- {r}")

    except:
        pass

# ========================
# UI
# ========================

if mode == "Mercado":
    run_market()
else:
    run_property()