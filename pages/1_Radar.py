import streamlit as st
import pandas as pd
from utils.db import get_top_opportunities, simulate_market

st.title("📡 Radar de oportunidades")

# ========================
# DATA
# ========================

df = get_top_opportunities(300)

if df.empty:
    st.warning("No hay datos disponibles")
    st.stop()

df = simulate_market(df)  # 🔥 ACTIVAR

# ========================
# SCORING CONSERVADOR (ALINEADO CON PROPIEDAD)
# ========================

def compute_radar_score(row):

    score = 0

    # ========================
    # RENTABILIDAD (proxy cashflow)
    # ========================
    rent = row.get("rentabilidad_estimada", 0)

    if rent > 8:
        score += 25
    elif rent > 6:
        score += 15
    elif rent > 5:
        score += 5

    # ========================
    # DESCUENTO (proxy margen)
    # ========================
    desc = row.get("descuento", 0)

    if desc > 15:
        score += 25
    elif desc > 10:
        score += 15
    elif desc > 5:
        score += 5

    # ========================
    # PRECIO VS BARRIO
    # ========================
    metros = row.get("metros", 0)
    precio = row.get("precio_total", 0)
    precio_m2_barrio = row.get("precio_m2_barrio", 0)

    if metros and precio_m2_barrio:
        precio_m2 = precio / metros

        if precio_m2 < precio_m2_barrio * 0.9:
            score += 20
        elif precio_m2 < precio_m2_barrio:
            score += 10

    # ========================
    # LIQUIDEZ (oportunidad oculta)
    # ========================
    if row.get("dias", 0) > 60:
        score += 10

    return min(score, 100)

df["score_radar"] = df.apply(compute_radar_score, axis=1)

# ORDENAR POR NUEVO SCORE
df = df.sort_values("score_radar", ascending=False).reset_index(drop=True)

# ========================
# LABEL (COHERENTE CON PROPIEDAD)
# ========================

def get_label(score):
    if score >= 65:
        return "🔥 Alta prioridad"
    elif score >= 45:
        return "👍 Interesante"
    else:
        return "⚠️ Débil"

# ========================
# HERO
# ========================

st.markdown("## 🔥 Mejores oportunidades ahora")

top3 = df.head(3)

for i, row in top3.iterrows():

    label = get_label(row["score_radar"])

    st.markdown(f"""
### 🏆 {row['barrio']} — {label}

💰 {int(row['precio_total']):,} €  
📊 Score: {round(row['score_radar'],1)}  
📈 Rentabilidad: {round(row.get('rentabilidad_estimada',0),1)}%  

👉 **Acción: Analizar en detalle**
""")

    if st.button(f"Ver propiedad {i}"):
        st.session_state.selected_property = row.to_dict()
        st.switch_page("pages/3_Propiedad.py")

st.caption("⚠️ Radar usa estimaciones. La decisión final se valida en análisis de propiedad (cashflow real).")

st.divider()

# ========================
# TABLA
# ========================

st.markdown("## 📊 Ranking de oportunidades")

display_df = df[[
    "barrio",
    "precio_total",
    "score_radar",
    "rentabilidad_estimada"
]].copy()

display_df.columns = [
    "Barrio",
    "Precio (€)",
    "Score",
    "Rentabilidad (%)"
]

st.dataframe(display_df.head(20), use_container_width=True)

# ========================
# 🔥 NUEVAS OPORTUNIDADES (FOMO)
# ========================

st.markdown("## 🚨 Oportunidades detectadas")

def is_opportunity(row):
    return (
        row.get("score_radar", 0) >= 65 and
        row.get("rentabilidad_estimada", 0) >= 6
    )

opps = df[df.apply(is_opportunity, axis=1)].copy()

if not opps.empty:

    opps = opps.sort_values("score_radar", ascending=False).head(5)

    for _, row in opps.iterrows():
        st.error(f"""
🔥 NUEVA OPORTUNIDAD

📍 {row['barrio']}
💰 {int(row['precio_total']):,} €
📊 Score: {round(row['score_radar'],1)}
📈 {round(row.get('rentabilidad_estimada',0),1)}%
⏱️ Lleva {row.get('dias', '?')} días en mercado

👉 **Revisar ahora**
""")
        if st.button(f"Ver oportunidad {row['barrio']} {row['precio_total']}"):
            st.session_state.selected_property = row.to_dict()
            st.switch_page("pages/3_Propiedad.py")

else:
    st.info("No hay oportunidades claras ahora")

# ========================
# INSIGHT
# ========================

st.markdown("## 🧠 Insight rápido")

best = df.iloc[0]

st.success(f"""
👉 Mejor candidata a analizar: **{best['barrio']}**

💰 {int(best['precio_total']):,} €
📊 Score: {round(best['score_radar'],1)}

➡️ Validar en detalle antes de tomar decisión.
""")