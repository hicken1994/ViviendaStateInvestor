import streamlit as st
from utils.db import get_top_opportunities, simulate_market, get_recent_events
from utils.tooltips import tooltip_help
from utils.profiles import get_perfil, compute_score_with_profile
import json


st.title("🤖 Copilot de inversión")
st.caption("💡 Tu asistente inteligente para tomar decisiones de inversión informadas.")

# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)

st.info(f"🎯 Perfil activo: **{perfil['nombre']}** — {perfil['descripcion']}")

# ========================
# MODO
# ========================

mode = st.radio("Modo", ["Propiedad", "Mercado"], horizontal=True)

if st.button("🧹 Limpiar contexto"):
    st.session_state.pop("copilot_property", None)

prop = st.session_state.get("copilot_property")

df = get_top_opportunities(300)
df = simulate_market(df)  # 🔥 ACTIVAR

# ========================
# SCORING CON PERFIL (IGUAL QUE RADAR)
# ========================

profile_metrics = df.apply(
    lambda row: compute_score_with_profile(row, perfil),
    axis=1,
    result_type="expand"
)

for col in profile_metrics.columns:
    df[col] = profile_metrics[col]

# ========================
# 🏆 OPORTUNIDAD DEL DÍA
# ========================

if not df.empty:
    best = df.sort_values("score_total", ascending=False).iloc[0]

    st.markdown("## 🏆 Oportunidad del Día")
    st.caption(tooltip_help("oportunidad_dia"))

    st.success(f"""
🔥 MEJOR OPORTUNIDAD HOY

{best['barrio']}
💰 {int(best['precio_total']):,} €
📊 Score: {round(best['score_total'], 1)}
📈 Rentabilidad: {round(best.get('rentabilidad_estimada', 0), 1)}%

👉 Si encaja contigo, revisa ahora
👉 Este tipo de oportunidades no duran mucho
""")

    st.divider()

# ========================
# 📡 ACTIVIDAD RECIENTE DEL MERCADO
# ========================

with st.expander("🔥 Actividad reciente del mercado", expanded=False):
    events = get_recent_events(10)

    if events.empty:
        st.info("No se han detectado eventos recientes.")
    else:
        for _, e in events.iterrows():
            etype = e.get("event_type", "")
            prop_id = e.get("property_id", "—")
            old_val = e.get("old_value")
            new_val = e.get("new_value")

            if etype == "price_drop":
                delta = f"de {int(old_val):,}€ a {int(new_val):,}€" if old_val and new_val else ""
                st.error(f"💸 **Bajada de precio** — {prop_id} {delta}")
            elif etype == "yield_up":
                delta = f"de {round(old_val, 2)}% a {round(new_val, 2)}%" if old_val and new_val else ""
                st.info(f"📈 **Mejora de rentabilidad** — {prop_id} {delta}")
            elif etype == "new_listing":
                st.success(f"🆕 **Nueva propiedad** — {prop_id}")
            else:
                st.write(f"📌 {etype} — {prop_id}")

st.divider()

# ========================
# 🏠 HEADER PROPIEDAD
# ========================

if mode == "Propiedad":

    if not prop:
        st.warning("Selecciona una propiedad primero desde el Radar o el Mapa.")
        st.stop()

    st.markdown("## 🏠 Propiedad seleccionada")

    col1, col2, col3 = st.columns(3)
    col1.metric("Precio", f"{int(prop.get('precio_total', 0)):,} €", help=tooltip_help("precio_total"))
    col2.metric("Cashflow", f"{int(prop.get('cashflow', 0))} €/mes", help=tooltip_help("cashflow"))
    col3.metric("Score", round(prop.get("score_total", 0), 2), help=tooltip_help("score_total"))

    st.caption(f"📍 {prop.get('barrio', 'Sin barrio')}")

# ========================
# 🧠 DEAL FINDER
# ========================

def get_top_deals():
    return df.sort_values("score_total", ascending=False).head(5)

# ========================
# 💰 PRECIO OBJETIVO
# ========================

def estimate_target_price(row):
    precio = row.get("precio_total", 0)
    descuento = row.get("descuento", 0)

    if descuento > 10:
        return int(precio * 0.90)
    elif descuento > 5:
        return int(precio * 0.95)
    else:
        return int(precio * 0.97)

# ========================
# 🟢 MODO MERCADO
# ========================

def run_market():

    st.markdown("## 🔥 Oportunidades reales hoy")
    st.caption(tooltip_help("oportunidades_detectadas"))

    deals = get_top_deals()
    best_deal = deals.iloc[0]

    st.success(f"""
👉 MEJOR OPORTUNIDAD:

{best_deal['barrio']}
💰 {int(best_deal['precio_total']):,} €
📊 Score: {round(best_deal['score_total'], 1)}

💸 Oferta recomendada: {estimate_target_price(best_deal):,} €
""")

    st.markdown("## 📊 Top oportunidades")

    for idx, (_, row) in enumerate(deals.iterrows()):
        target = estimate_target_price(row)

        st.markdown(f"""
### {row['barrio']}
💰 {int(row['precio_total']):,} €
📊 Score: {round(row['score_total'], 1)}

👉 Ofertar: {target:,} €
""")

        if st.button(f"Analizar {row['barrio']} {int(row['precio_total'])}", key=f"market_{idx}"):
            st.session_state.selected_property = row.to_dict()
            st.switch_page("pages/3_propiedad.py")

    # Detalle scoring (solo avanzado)
    if perfil.get("mostrar_detalle_scoring"):
        st.divider()
        st.markdown("### 🧪 Detalle del scoring de mercado")

        scoring_cols = ["barrio", "score_total", "score_descuento", "score_precio", "score_liquidez", "score_tamano"]
        if "score_ruido" in df.columns:
            scoring_cols.append("score_ruido")

        available_cols = [c for c in scoring_cols if c in df.columns]
        scoring_df = deals[available_cols].copy()

        for col in scoring_df.select_dtypes(include="number").columns:
            scoring_df[col] = scoring_df[col].round(2)

        st.dataframe(scoring_df, use_container_width=True)

# ========================
# 🟡 MODO PROPIEDAD
# ========================

def run_property():

    decision = prop.get("recomendacion_modelo", "")
    score = prop.get("score_total", 0)

    st.markdown("## 🧠 Decisión final")
    st.caption(tooltip_help("score_total"))

    if "BUENA" in decision:
        st.success("🟢 COMPRAR")
    elif "JUSTA" in decision:
        st.warning("🟡 NEGOCIAR")
    else:
        st.error("🔴 DESCARTAR")

    st.markdown("### 🎯 Acción inmediata")

    if score > perfil["min_score"] + 20:
        st.success(f"👉 Comprar o lanzar oferta inmediata — {perfil['consejo_compra']}")
    elif score > perfil["min_score"]:
        st.warning(f"👉 Negociar (5–10%) — {perfil['consejo_negociar']}")
    else:
        st.error(f"👉 No entrar en esta operación — {perfil['consejo_descartar']}")

    # Detalle scoring (solo avanzado)
    if perfil.get("mostrar_detalle_scoring"):
        st.divider()
        st.markdown("### 🧪 Desglose del scoring")

        score_cols = {
            "score_descuento": "Descuento",
            "score_precio": "Precio vs Barrio",
            "score_liquidez": "Liquidez",
            "score_tamano": "Tamaño",
            "score_ruido": "Ruido",
        }

        cols = st.columns(len(score_cols))
        for idx, (key, label) in enumerate(score_cols.items()):
            val = prop.get(key, 0)
            cols[idx].metric(label, round(val, 2) if val else 0, help=tooltip_help(key))

    # ========================
    # IA SOLO PARA MEJORA
    # ========================

    st.divider()
    st.markdown("### 🤖 Análisis con IA")
    st.caption("Genera una estrategia de compra personalizada usando inteligencia artificial.")

    if st.button("🤖 Generar análisis con IA"):

        api_key = None
        try:
            api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass

        if not api_key:
            import os
            api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            st.warning("⚠️ No hay API key de OpenAI configurada. Añade `OPENAI_API_KEY` en Streamlit Secrets o como variable de entorno.")
        else:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)

                prompt = f"""
Eres un inversor experto. Perfil del inversor: {perfil['nombre']} - {perfil['descripcion']}.

Propiedad:
{prop}

Mejora la estrategia de compra adaptada al perfil del inversor.

Devuelve JSON:
{{
 "precio_objetivo": number,
 "acciones": [],
 "riesgos": []
}}
"""

                with st.spinner("Analizando con IA..."):
                    res = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2
                    )

                txt = res.choices[0].message.content
                js = txt[txt.index("{"):txt.rindex("}") + 1]
                data = json.loads(js)

                st.markdown("### 🤖 Optimización IA")

                if data.get("precio_objetivo"):
                    st.success(f"💸 Precio objetivo IA: {int(data['precio_objetivo']):,} €")
                    st.caption(tooltip_help("precio_objetivo"))

                if data.get("acciones"):
                    st.markdown("**📋 Acciones recomendadas:**")
                    for a in data["acciones"]:
                        st.write(f"✅ {a}")

                if data.get("riesgos"):
                    st.markdown("**⚠️ Riesgos identificados:**")
                    for r in data["riesgos"]:
                        st.write(f"🔸 {r}")

            except Exception as e:
                st.error(f"Error al consultar IA: {e}")

# ========================
# UI
# ========================

if mode == "Mercado":
    run_market()
else:
    run_property()