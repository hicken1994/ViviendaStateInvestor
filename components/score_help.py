import streamlit as st
import pandas as pd


def render_score_breakdown(score_row: dict, perfil: dict, expanded: bool = False):
    """Muestra el desglose visual del score en 5 dimensiones."""
    with st.expander("📊 Desglose del score", expanded=expanded):
        st.markdown(
            f"**Score total: {score_row.get('score_total', 0):.1f}/100**  \n"
            f"Perfil aplicado: **{perfil['nombre']}**  \n"
            f"Cada dimensión tiene un peso distinto según tu perfil."
        )

        dims = [
            ("💰 Descuento", "score_descuento", 40, "Qué tan por debajo del mercado está"),
            ("📉 Precio vs Barrio", "score_precio", 25, "Relación precio/m² vs media del barrio"),
            ("💧 Liquidez", "score_liquidez", 15, "Facilidad para alquilar según tamaño"),
            ("📐 Tamaño", "score_tamano", 10, "Metros cuadrados útiles"),
            ("🔇 Ruido", "score_ruido", 10, "Nivel de ruido estimado de la zona"),
        ]

        for label, key, max_val, desc in dims:
            val = score_row.get(key, 0) or 0
            pct = min(val / max_val * 100, 100) if max_val > 0 else 0

            st.markdown(f"**{label}** — `{val:.1f}/{max_val}`")
            st.markdown(f"<small>{desc}</small>", unsafe_allow_html=True)
            st.progress(pct / 100, text=f"{pct:.0f}%")
            st.markdown("")


def render_score_legend():
    """Pequeña leyenda de colores de score."""
    st.markdown("""
    <div style="display:flex; gap:1rem; padding:0.25rem 0; font-size:0.85rem;">
        <span style="color:#00c853;">🟢 ≥ 70 — COMPRAR</span>
        <span style="color:#ffc107;">🟡 50–69 — NEGOCIAR</span>
        <span style="color:#ff5252;">🔴 &lt; 50 — DESCARTAR</span>
    </div>
    """, unsafe_allow_html=True)
