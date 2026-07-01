import streamlit as st
from utils.tooltips import tooltip_help
from utils.db import get_recent_events, get_barrio_avg_scores
from utils.services import get_barrio_rent
from utils.profiles import get_perfil, get_recomendacion_perfil
from utils.charts import create_radar_chart, create_price_history_chart
from utils.history import generate_price_history, compute_price_trend
from utils.auth import require_auth
from utils.user_store import save_watchlist


require_auth()

# ========================
# BREADCRUMB
# ========================

st.markdown("""
<style>
    .breadcrumb a { color: rgba(255,255,255,0.4); text-decoration: none; font-size: 0.85rem; }
    .breadcrumb a:hover { color: rgba(255,255,255,0.7); }
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<div class='breadcrumb'><a href='javascript:history.back()'>← Volver</a></div>",
    unsafe_allow_html=True,
)

st.title("🏠 Análisis de propiedad")
st.caption("Simulación financiera completa para decidir si esta propiedad es buena inversión.")

# ========================
# PERFIL
# ========================

perfil_nombre = st.session_state.get("perfil_inversion", "intermedio")
perfil = get_perfil(perfil_nombre)

st.info(f"🎯 Perfil activo: **{perfil['nombre']}** — {perfil['descripcion']}")

# ========================
# VALIDACIÓN
# ========================

if "selected_property" not in st.session_state:
    st.warning("No hay propiedad seleccionada")
    st.stop()

prop = st.session_state.selected_property

# ========================
# IMAGEN + HEADER + KPIs
# ========================

if prop.get("image_url"):
    st.image(prop["image_url"], width="stretch")

precio = prop.get("precio_total", 0)
metros = prop.get("metros", 0)

nav_col1, nav_col2 = st.columns([3, 1])
with nav_col1:
    st.subheader(f"📍 {prop.get('barrio', 'Sin barrio')}")
with nav_col2:
    prop_id = str(prop.get("propiedad_id", ""))
    wl = st.session_state.get("watchlist", {"propiedades": [], "barrios": []})
    is_watched = prop_id in [str(p) for p in wl.get("propiedades", [])]
    if st.button(
        "✅ Vigilada" if is_watched else "👁️ Vigilar propiedad",
        key="watch_detail",
        width="stretch",
    ):
        if is_watched:
            wl["propiedades"] = [p for p in wl["propiedades"] if str(p) != prop_id]
        else:
            wl["propiedades"].append(prop_id)
        st.session_state.watchlist = wl
        save_watchlist(wl)
        st.rerun()

col1, col2, col3 = st.columns(3)
col1.metric("💰 Precio", f"{int(precio):,} €", help=tooltip_help("precio_total"))
col2.metric("📊 Score", round(prop.get("score_total", 0), 2), help=tooltip_help("score_total"))
col3.metric("📈 Rentabilidad estimada", f"{round(prop.get('rentabilidad_estimada', 0), 2)}%", help=tooltip_help("rentabilidad_estimada"))

st.divider()

# ========================
# PARÁMETROS (calculados inline o desde expander)
# ========================

# Defaults del perfil
_entrada_pct = perfil["entrada_pct"] / 100
_interes = float(perfil["interes"]) / 100
_años = perfil["años"]
_reforma = perfil["reforma"]
_gastos_pct = perfil["gastos_pct"] / 100

# Exposed in expander (collapsed by default) so user can tweak
with st.expander("⚙️ Ajustar parámetros de simulación", expanded=False):
    col1, col2, col3 = st.columns(3)
    _entrada_pct = col1.slider("Entrada (%)", 10, 40, perfil["entrada_pct"], help=tooltip_help("entrada")) / 100
    _interes = col2.slider("Interés (%)", 1.0, 6.0, float(perfil["interes"]), help=tooltip_help("interes")) / 100
    _años = col3.slider("Años", 10, 40, perfil["años"], help=tooltip_help("años_hipoteca"))
    _reforma = st.number_input("Coste reforma (€)", value=perfil["reforma"], help=tooltip_help("reforma"))
    _gastos_pct = st.slider("Gastos compra (%)", 5, 15, perfil["gastos_pct"], help=tooltip_help("gastos_compra")) / 100

# ========================
# CÁLCULOS
# ========================

entrada = precio * _entrada_pct
gastos = precio * _gastos_pct
total_inversion = entrada + gastos + _reforma
prestamo = precio - entrada
r = _interes / 12
n = _años * 12
cuota = round(prestamo * (r * (1 + r)**n) / ((1 + r)**n - 1), 2)

barrio = prop.get("barrio", "")
precio_m2_alquiler = get_barrio_rent(barrio)
base_alquiler = round(precio_m2_alquiler * metros, 2)
alquiler = round(base_alquiler * 1.15, 2)
gastos_mensuales = round(alquiler * 0.15, 2)
gastos_fijos = 100
cashflow = round(alquiler - cuota - gastos_mensuales - gastos_fijos, 2)
break_even = round((cuota + gastos_fijos) / (1 - 0.15), 2)
rentabilidad_real = round((alquiler * 12) / total_inversion * 100, 2) if total_inversion else 0
margen_euros = round(alquiler - break_even, 2)
margen_pct = round((margen_euros / alquiler) * 100, 2) if alquiler else 0
score_total = prop.get("score_total", 0)
recomendacion = get_recomendacion_perfil(perfil, cashflow, margen_pct, score_total)

# ========================
# 🚀 DECISIÓN
# ========================

st.markdown("## 🎯 Decisión")
st.markdown(f"### 👉 {recomendacion}")

# ========================
# 📊 3 ESCENARIOS VISIBLES
# ========================

st.markdown("### 📈 Escenarios de inversión")
st.caption("Ingreso mensual estimado según distintos niveles de ocupación.")

sc_col1, sc_col2, sc_col3 = st.columns(3)

for col, (nombre, val, emoji) in zip(
    [sc_col1, sc_col2, sc_col3],
    [
        ("Conservador", base_alquiler, "🟢"),
        ("Esperado", alquiler, "🟡"),
        ("Optimista", base_alquiler * 1.25, "🔵"),
    ],
):
    cf = round(val - cuota - (val * 0.15) - gastos_fijos, 2)
    label = f"{emoji} {nombre}"
    with col:
        st.metric(label, f"{val:.0f} €/mes", delta=f"{cf:+.0f} € cashflow", delta_color="normal" if cf > 0 else "inverse")

# ========================
# CASHFLOW + BREAK-EVEN + MARGEN
# ========================

st.divider()
col1, col2, col3 = st.columns(3)
col1.metric("💰 Cashflow", f"{cashflow:,.2f} €/mes", help=tooltip_help("cashflow"))
col2.metric("🎯 Break-even", f"{break_even:,.2f} €/mes", help=tooltip_help("break_even"))
col3.metric("🛡️ Margen", f"{margen_euros:,.2f} €", help=tooltip_help("margen"))

if cashflow <= 0:
    st.error("Esta operación pierde dinero mensualmente")
elif margen_pct < 10:
    st.error("Margen muy bajo — alta probabilidad de problemas")
elif margen_pct < 25:
    st.warning("Margen limitado — depende del mercado")
else:
    st.success("Margen sólido — operación defensiva")

# ========================
# 📡 HISTÓRICO + EVENTOS (EXPANDERS)
# ========================

if precio > 0 and prop.get("propiedad_id"):
    with st.expander("📈 Histórico de precio (60 días)", expanded=False):
        prop_id_hist = str(prop.get("propiedad_id", prop.get("id", prop.get("precio_total", 0))))
        hist = generate_price_history(prop_id_hist, float(precio), days=60)
        trend = compute_price_trend(hist)
        trend_icon = "📈" if trend["trend"] == "subiendo" else ("📉" if trend["trend"] == "bajando" else "➡️")
        st.caption(
            f"Tendencia: {trend_icon} {trend['change_pct']:+.1f}%  ·  "
            f"Mín: {int(trend['min']):,}€  ·  "
            f"Máx: {int(trend['max']):,}€  ·  "
            f"Media: {int(trend['avg']):,}€"
        )
        fig_hist = create_price_history_chart(hist, height=200, show_xaxis=True)
        st.plotly_chart(fig_hist, width="stretch", key="hist_detail")

prop_id = str(prop.get("id", prop.get("precio_total", "")))
events = get_recent_events(50)
if not events.empty:
    prop_events = events[events["property_id"] == prop_id]
    if not prop_events.empty:
        with st.expander("🚨 Actividad reciente", expanded=False):
            for _, e in prop_events.iterrows():
                etype = e.get("event_type", "")
                old_val = e.get("old_value")
                new_val = e.get("new_value")
                if etype == "price_drop":
                    delta = f"de {int(old_val):,}€ a {int(new_val):,}€" if old_val and new_val else ""
                    st.error(f"💸 **Bajada de precio** {delta}")
                elif etype == "yield_up":
                    delta = f"de {round(old_val, 2)}% a {round(new_val, 2)}%" if old_val and new_val else ""
                    st.info(f"📈 **Mejora de rentabilidad** {delta}")

# ========================
# 🧪 DETALLE SCORING (AVANZADO)
# ========================

if perfil.get("mostrar_detalle_scoring"):
    with st.expander("🧪 Desglose del scoring", expanded=False):
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

        barrio_nombre = prop.get("barrio", "")
        if barrio_nombre:
            barrio_avg = get_barrio_avg_scores(barrio_nombre, perfil)
            if barrio_avg:
                fig = create_radar_chart(
                    property_scores=prop,
                    barrio_avg=barrio_avg,
                    property_name=f"📍 {barrio_nombre}",
                    barrio_name=f"🏙️ Promedio {barrio_nombre}",
                    height=380,
                )
                st.plotly_chart(fig, width="stretch", key="radar_detalle")

# ========================
# 🧠 VALIDAR CON IA
# ========================

st.divider()
st.info("👉 Validá esta decisión con un análisis más profundo usando IA")

if st.button("🔍 Validar con IA", type="primary"):
    st.session_state.copilot_property = {
        **prop,
        "score_total": round(score_total, 2),
        "cashflow": round(cashflow, 2),
        "break_even": round(break_even, 2),
        "margen": round(margen_euros, 2),
        "margen_pct": round(margen_pct, 2),
        "recomendacion_modelo": recomendacion,
        "perfil_inversion": perfil_nombre,
    }
    st.switch_page("pages/4_Analisis_Detallado.py")
