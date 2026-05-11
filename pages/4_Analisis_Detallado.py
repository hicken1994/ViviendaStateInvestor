import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import get_top_opportunities, simulate_market, get_recent_events
from utils.images import add_images
from utils.tooltips import tooltip_help
from utils.profiles import get_perfil, compute_score_with_profile
import json


# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)


# ========================
# HEADER
# ========================

st.title("🤖 Copilot de inversión")
st.caption("Análisis del mercado inmobiliario de Madrid adaptado a tu perfil.")
st.markdown(f"**{perfil['emoji']} {perfil['nombre']}** — _{perfil['descripcion']}_")


# ========================
# CARGA DE DATOS + SIMULACIÓN
# ========================

df = get_top_opportunities(300)

with st.sidebar:
    st.markdown("### 📊 Simulación")
    if st.button("📊 Simular cambios de mercado", key="sim_copilot", use_container_width=True):
        df_sim = simulate_market(df.copy())
        st.session_state["copilot_simulated"] = df_sim.to_dict("records")
        st.rerun()

if "copilot_simulated" in st.session_state:
    df = pd.DataFrame(st.session_state["copilot_simulated"])
    st.sidebar.success("📊 Simulación activa")
    if st.sidebar.button("🔄 Resetear datos", key="reset_copilot", use_container_width=True):
        st.session_state.pop("copilot_simulated", None)
        st.rerun()

df = add_images(df)

profile_metrics = df.apply(
    lambda row: compute_score_with_profile(row, perfil),
    axis=1, result_type="expand"
)
for col in profile_metrics.columns:
    df[col] = profile_metrics[col]


# ========================
# SELECTOR DE MODO
# ========================

col_mode, col_clear = st.columns([4, 1])
with col_mode:
    mode = st.radio(
        "Modo", ["📈 Mercado", "🏠 Propiedad"],
        horizontal=True, label_visibility="collapsed",
    )
with col_clear:
    if st.button("🧹 Limpiar", use_container_width=True):
        st.session_state.pop("copilot_property", None)
        st.rerun()

prop = st.session_state.get("copilot_property")


# ========================
# FUNCIONES AUXILIARES
# ========================

def get_top_deals(n=5):
    return df.sort_values("score_total", ascending=False).head(n)


def estimate_target_price(row):
    precio = row.get("precio_total", 0)
    descuento = row.get("descuento", 0)
    if descuento > 10:
        return int(precio * 0.90)
    elif descuento > 5:
        return int(precio * 0.95)
    return int(precio * 0.97)


def render_scatter(df, highlight_prop=None):
    """Gráfico de dispersión precio vs score, opcionalmente con una propiedad destacada."""
    fig = px.scatter(
        df,
        x="precio_total",
        y="score_total",
        color="decision",
        color_discrete_map={
            "COMPRAR": "#22c55e",
            "NEGOCIAR": "#eab308",
            "DESCARTAR": "#ef4444",
        },
        size="rentabilidad_estimada",
        size_max=20,
        hover_name="barrio",
        hover_data={
            "precio_total": ":,.0f",
            "score_total": ":.1f",
            "rentabilidad_estimada": ":.1f",
            "decision": True,
        },
        title="Oportunidades según precio y puntuación",
        labels={
            "precio_total": "Precio (€)",
            "score_total": "Score total",
            "decision": "Decisión",
            "rentabilidad_estimada": "Rent. (%)",
        },
    )

    if highlight_prop is not None:
        fig.add_trace(
            go.Scatter(
                x=[highlight_prop.get("precio_total", 0)],
                y=[highlight_prop.get("score_total", 0)],
                mode="markers",
                marker=dict(size=24, color="#f59e0b", symbol="star", line=dict(width=2, color="white")),
                name="📍 Propiedad seleccionada",
                hovertext=highlight_prop.get("barrio", ""),
            )
        )

    fig.update_layout(
        xaxis=dict(tickformat=",.0f"),
        height=450,
        hovermode="closest",
    )
    return fig


# ============================================================
# 📈 MODO MERCADO
# ============================================================

if mode == "📈 Mercado":

    st.markdown("## 📊 Panorama del mercado")
    st.caption(f"Distribución de las mejores oportunidades filtradas por tu perfil **{perfil['nombre']}**.")

    # ── KPIs ──
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("🏠 Analizadas", len(df))
    kpi2.metric("📊 Score medio", f"{df['score_total'].mean():.1f}")
    kpi3.metric("📈 Rent. media", f"{df['rentabilidad_estimada'].mean():.1f}%")
    kpi4.metric(
        "🎯 Para invertir",
        len(df[df["decision"] == "COMPRAR"]),
        help="Propiedades que superan todos los umbrales de tu perfil",
    )

    # ── Scatter plot ──
    fig = render_scatter(df)
    st.plotly_chart(fig, use_container_width=True)

    # ── Eventos recientes ──
    with st.expander("📡 Actividad reciente del mercado", expanded=False):
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

    # ── Top candidatos ──
    st.markdown("### 🎯 Mejores candidatos para invertir")
    deals = get_top_deals(5)

    for idx, (_, row) in enumerate(deals.iterrows()):
        score = row["score_total"]
        badge = "🟢" if score >= 70 else ("🟡" if score >= 50 else "🔴")
        target = estimate_target_price(row)

        col_b, col_p, col_s, col_r, col_o, col_a = st.columns([2, 1.5, 1, 1, 1.5, 1.2])

        with col_b:
            st.markdown(f"**{badge} {row['barrio']}**")
        with col_p:
            st.write(f"💰 {int(row['precio_total']):,} €")
        with col_s:
            st.write(f"📊 Score **{score:.1f}**")
        with col_r:
            rent = row.get("rentabilidad_estimada", 0)
            st.write(f"📈 {rent:.1f}%")
        with col_o:
            st.write(f"💸 Oferta: **{target:,} €**")
        with col_a:
            if st.button("Analizar →", key=f"deal_{idx}", use_container_width=True):
                st.session_state.selected_property = row.to_dict()
                st.switch_page("pages/3_propiedad.py")

    st.caption("💡 Haz clic en **Analizar** para ver el desglose completo de una propiedad.")

    # ── Detalle scoring (solo avanzado) ──
    if perfil.get("mostrar_detalle_scoring"):
        st.divider()
        st.markdown("### 🧪 Detalle del scoring")

        scoring_cols = [
            "barrio", "score_total", "score_descuento",
            "score_precio", "score_liquidez", "score_tamano",
        ]
        if "score_ruido" in df.columns:
            scoring_cols.append("score_ruido")

        available = [c for c in scoring_cols if c in df.columns]
        scoring_df = deals[available].copy()
        for col in scoring_df.select_dtypes(include="number").columns:
            scoring_df[col] = scoring_df[col].round(2)

        st.dataframe(scoring_df, use_container_width=True)


# ============================================================
# 🏠 MODO PROPIEDAD
# ============================================================

else:

    if not prop:
        st.warning("Selecciona una propiedad primero desde el **Radar**, el **Mapa**, o el modo **Mercado**.")
        st.stop()

    # ── Header con imagen ──
    col_img, col_head = st.columns([1, 2])
    with col_img:
        if prop.get("image_url"):
            st.image(prop["image_url"], use_container_width=True)

    with col_head:
        st.markdown(f"## 📍 {prop.get('barrio', 'Sin barrio')}")

        decision = prop.get("recomendacion_modelo", "")
        score = prop.get("score_total", 0)

        if "BUENA" in decision:
            st.success("## 🟢 COMPRAR")
            consejo = perfil["consejo_compra"]
        elif "JUSTA" in decision:
            st.warning("## 🟡 NEGOCIAR")
            consejo = perfil["consejo_negociar"]
        else:
            st.error("## 🔴 DESCARTAR")
            consejo = perfil["consejo_descartar"]

        st.caption(f"💡 {consejo}")

    st.divider()

    # ── Métricas clave ──
    st.markdown("### 📊 Métricas clave")

    precio = prop.get("precio_total", 0)
    score_val = prop.get("score_total", 0)
    rent = prop.get("rentabilidad_estimada", 0)
    cashflow = prop.get("cashflow", 0)
    metros = prop.get("metros", 0)
    precio_m2 = prop.get("precio_m2", 0)
    precio_m2_barrio = prop.get("precio_m2_barrio", 0)
    descuento = prop.get("descuento_pct", 0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Precio", f"{int(precio):,} €", help=tooltip_help("precio_total"))
    col2.metric("📊 Score", f"{score_val:.1f}", help=tooltip_help("score_total"))
    col3.metric("📈 Rentabilidad", f"{rent:.1f}%", help=tooltip_help("rentabilidad_estimada"))
    col4.metric("💸 Cashflow", f"{int(cashflow):,} €/mes" if cashflow else "—", help=tooltip_help("cashflow"))

    col1b, col2b, col3b, col4b = st.columns(4)
    col1b.metric("📐 Metros", f"{int(metros)} m²", help=tooltip_help("metros"))
    col2b.metric("€/m²", f"{int(precio_m2):,} €")
    col3b.metric("Barrio €/m²", f"{int(precio_m2_barrio):,} €", help=tooltip_help("precio_m2_barrio"))
    col4b.metric("Descuento", f"{descuento:.1f}%" if descuento else "—", help=tooltip_help("descuento"))

    st.divider()

    # ── Contexto de mercado ──
    st.markdown("### 📈 La propiedad en el mercado")
    st.caption("Cómo se compara esta propiedad con el resto de oportunidades.")

    fig = render_scatter(df, highlight_prop=prop)
    st.plotly_chart(fig, use_container_width=True)

    # ── Scoring breakdown ──
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

    # ── Análisis con IA ──
    st.divider()
    st.markdown("### 🤖 Análisis con IA")
    st.caption("Genera una estrategia de compra personalizada para esta propiedad.")

    if st.button("🤖 Generar análisis", type="primary", use_container_width=True):

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
Eres un asesor de inversión inmobiliaria. Perfil del inversor: {perfil['nombre']} - {perfil['descripcion']}.

Propiedad evaluada:
{prop}

Basado en estos datos, genera una estrategia de compra adaptada al perfil del inversor.

Devuelve SOLO JSON:
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
                        temperature=0.2,
                    )

                txt = res.choices[0].message.content
                js = txt[txt.index("{") : txt.rindex("}") + 1]
                data = json.loads(js)

                col_ia1, col_ia2 = st.columns([1, 1])

                with col_ia1:
                    if data.get("precio_objetivo"):
                        st.success(f"### 💸 Precio objetivo\n**{int(data['precio_objetivo']):,} €**")

                    if data.get("acciones"):
                        st.markdown("**📋 Acciones recomendadas:**")
                        for a in data["acciones"]:
                            st.write(f"✅ {a}")

                with col_ia2:
                    if data.get("riesgos"):
                        st.markdown("**⚠️ Riesgos identificados:**")
                        for r in data["riesgos"]:
                            st.write(f"🔸 {r}")

            except Exception as e:
                st.error(f"Error al consultar IA: {e}")
