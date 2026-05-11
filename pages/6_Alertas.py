"""
Alertas de mercado y watchlist de propiedades vigiladas.
"""

import streamlit as st
import pandas as pd
from utils.db import get_recent_events, get_top_opportunities
from utils.profiles import get_perfil

st.set_page_config(page_title="Alertas", page_icon="🚨", layout="wide")

# ========================
# WATCHLIST — init
# ========================

if "watchlist" not in st.session_state:
    st.session_state.watchlist = {"propiedades": [], "barrios": []}

wl = st.session_state.watchlist


# ========================
# CARGA DE DATOS
# ========================

events = get_recent_events(200)
props = get_top_opportunities(300)

# Armar dict de propiedades por propiedad_id para búsqueda rápida
prop_by_id = {}
for _, row in props.iterrows():
    pid = str(row.get("propiedad_id", ""))
    if pid:
        prop_by_id[pid] = row
    # También indexar por precio_total como fallback
    precio_key = str(int(row.get("precio_total", 0)))
    if precio_key not in prop_by_id:
        prop_by_id[precio_key] = row


# ========================
# ENRIQUECER EVENTOS
# ========================

def enrich_event(event: pd.Series) -> dict:
    """Intenta asociar un evento a una propiedad conocida."""
    pid = str(event.get("property_id", ""))
    prop = prop_by_id.get(pid)
    return {
        "event": event,
        "prop": prop,
        "property_id": pid,
        "barrio": prop.get("barrio", "—") if prop is not None else "—",
        "precio": prop.get("precio_total", 0) if prop is not None else 0,
        "matched": prop is not None,
        "event_type": event.get("event_type", ""),
        "old_value": event.get("old_value"),
        "new_value": event.get("new_value"),
        "timestamp": event.get("timestamp"),
    }


enriched = [enrich_event(events.iloc[i]) for i in range(len(events))]


# ========================
# FILTROS
# ========================

# Solo vigiladas?
show_watched = st.checkbox(
    "🔍 Solo mis propiedades vigiladas",
    value=False,
    help="Mostrar solo eventos de propiedades o barrios en tu watchlist.",
)

filtered = enriched
if show_watched:
    watched_ids = [str(p) for p in wl.get("propiedades", [])]
    watched_barrios = wl.get("barrios", [])
    filtered = [
        e for e in enriched
        if e["property_id"] in watched_ids
        or e["barrio"] in watched_barrios
    ]

# Filtro por tipo de evento
event_types = sorted(set(e["event_type"] for e in filtered))
if event_types:
    selected_types = st.multiselect(
        "Tipo de evento",
        options=event_types,
        default=event_types,
        key="alert_type_filter",
    )
    filtered = [e for e in filtered if e["event_type"] in selected_types]

# Filtro por barrio
barrios = sorted(set(e["barrio"] for e in filtered if e["barrio"] != "—"))
if barrios:
    selected_barrios = st.multiselect(
        "Barrio",
        options=barrios,
        default=[],
        key="alert_barrio_filter",
    )
    if selected_barrios:
        filtered = [e for e in filtered if e["barrio"] in selected_barrios]


# ========================
# KPIs
# ========================

st.markdown("# 🚨 Alertas de mercado")

k1, k2, k3, k4, k5 = st.columns(5)

price_drops = len([e for e in filtered if e["event_type"] == "price_drop"])
new_listings = len([e for e in filtered if e["event_type"] == "new_listing"])
yield_ups = len([e for e in filtered if e["event_type"] == "yield_up"])
matched = len([e for e in filtered if e["matched"]])

k1.metric("📡 Total eventos", len(filtered))
k2.metric("💸 Bajadas de precio", price_drops)
k3.metric("🆕 Nuevas propiedades", new_listings)
k4.metric("📈 Mejora rentabilidad", yield_ups)
k5.metric("🔗 Identificadas", f"{matched}/{len(filtered)}")

st.divider()


# ========================
# LISTA DE EVENTOS
# ========================

if not filtered:
    st.info(
        "📭 No hay eventos aún. "
        "Simula el mercado desde el **Radar** (sidebar → Simular cambios de mercado) "
        "para generar actividad."
    )
    if st.button("← Ir al Radar", type="primary"):
        st.switch_page("pages/1_Radar.py")
    st.stop()

st.markdown(f"### 📋 Últimos eventos")

for e in filtered:
    ev = e["event"]
    etype = e["event_type"]
    prop = e["prop"]
    pid = e["property_id"]

    with st.container(border=True):
        cols = st.columns([0.05, 0.5, 0.2, 0.15, 0.1])

        with cols[0]:
            if etype == "price_drop":
                st.markdown("💸")
            elif etype == "new_listing":
                st.markdown("🆕")
            elif etype == "yield_up":
                st.markdown("📈")
            else:
                st.markdown("📌")

        with cols[1]:
            if prop is not None:
                barrio = prop.get("barrio", "—")
                precio = prop.get("precio_total", 0)
                score = prop.get("score_total", 0)
                decision = prop.get("decision", "")
                st.markdown(f"**{barrio}** — {int(precio):,} € · Score: {round(score, 1)}")

                # Botón para ver propiedad
                if st.button(f"🔍 Ver {barrio}", key=f"view_{pid}_{ev.get('id', '')}"):
                    st.session_state.selected_property = prop.to_dict()
                    st.switch_page("pages/3_propiedad.py")
            else:
                st.markdown(f"Propiedad **{pid}**")

        with cols[2]:
            if etype == "price_drop":
                old_v = e.get("old_value", 0)
                new_v = e.get("new_value", 0)
                if old_v and new_v:
                    st.markdown(
                        f"~~{int(old_v):,}€~~ → **{int(new_v):,}€**"
                    )
            elif etype == "yield_up":
                old_v = e.get("old_value", 0)
                new_v = e.get("new_value", 0)
                if old_v and new_v:
                    st.markdown(
                        f"{round(old_v, 2)}% → **{round(new_v, 2)}%**"
                    )
            elif etype == "new_listing":
                st.markdown("🆕 Nueva")

        with cols[3]:
            ts = e.get("timestamp")
            if ts:
                st.caption(str(ts)[:19])

        with cols[4]:
            # Watch/unwatch button
            pid_str = pid
            is_watched = pid_str in [str(p) for p in wl.get("propiedades", [])]
            watch_label = "👁️" if not is_watched else "✅"
            if st.button(
                watch_label,
                key=f"watch_{pid_str}_{ev.get('id', '')}",
                help="Quitar de vigiladas" if is_watched else "Vigilar esta propiedad",
            ):
                if is_watched:
                    wl["propiedades"] = [p for p in wl["propiedades"] if str(p) != pid_str]
                else:
                    wl["propiedades"].append(pid_str)
                st.session_state.watchlist = wl
                st.rerun()

st.divider()


# ========================
# WATCHLIST MANAGEMENT
# ========================

with st.expander("👁️ Mi watchlist — propiedades vigiladas", expanded=False):
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**🏠 Propiedades vigiladas**")
        watched_props = wl.get("propiedades", [])
        if watched_props:
            for pid_val in watched_props:
                prop = prop_by_id.get(str(pid_val))
                label = (
                    f"{prop['barrio']} — {int(prop['precio_total']):,}€"
                    if prop is not None
                    else f"ID: {pid_val}"
                )
                if st.button(f"✕ {label}", key=f"unwatch_prop_{pid_val}"):
                    wl["propiedades"] = [p for p in wl["propiedades"] if str(p) != str(pid_val)]
                    st.session_state.watchlist = wl
                    st.rerun()
        else:
            st.caption("Ninguna. Vigila propiedades desde el Radar o desde aquí.")

    with col_b:
        st.markdown("**📍 Barrios vigilados**")
        watched_barrios = wl.get("barrios", [])
        if watched_barrios:
            for barrio in watched_barrios:
                if st.button(f"✕ {barrio}", key=f"unwatch_brr_{barrio}"):
                    wl["barrios"] = [b for b in wl["barrios"] if b != barrio]
                    st.session_state.watchlist = wl
                    st.rerun()
        else:
            st.caption("Ninguno. Podés vigilar barrios completos.")

        # Add barrio input
        all_barrios = sorted(props["barrio"].unique())
        new_barrio = st.selectbox(
            "➕ Agregar barrio a watchlist",
            options=[""] + all_barrios,
            key="add_barrio_wl",
        )
        if new_barrio and new_barrio not in wl.get("barrios", []):
            wl["barrios"].append(new_barrio)
            st.session_state.watchlist = wl
            st.rerun()

st.divider()

# ========================
# NAV
# ========================

st.button("← Volver al Radar", use_container_width=True, on_click=lambda: st.switch_page("pages/1_Radar.py"))
