import streamlit as st
import pandas as pd
from utils.connection import get_conn_ro
from utils.services import get_top_opportunities
from utils.user_store import load_watchlist, save_preference


def check_new_opportunities() -> list[dict]:
    detected = []
    wl = load_watchlist()
    watched_barrios = wl.get("barrios", [])
    if not watched_barrios:
        return detected

    df = get_top_opportunities(300)
    if df.empty:
        return detected

    seen_ids = set(st.session_state.get("seen_notification_ids", []))

    for _, row in df.iterrows():
        barrio = str(row.get("barrio", ""))
        pid = str(row.get("propiedad_id", ""))
        score = row.get("score_total", 0)
        decision = str(row.get("decision", ""))

        if pid in seen_ids:
            continue

        if barrio in watched_barrios and score >= 70:
            detected.append({
                "type": "new_opportunity",
                "property_id": pid,
                "barrio": barrio,
                "score": round(score, 1),
                "precio": int(row.get("precio_total", 0)),
                "decision": decision,
                "rentabilidad": round(row.get("rentabilidad_estimada", 0), 1),
            })
            seen_ids.add(pid)

    st.session_state["seen_notification_ids"] = list(seen_ids)
    return detected


def check_price_drops() -> list[dict]:
    detected = []
    wl = load_watchlist()
    watched_props = [str(p) for p in wl.get("propiedades", [])]
    if not watched_props:
        return detected

    seen_drop_ids = set(st.session_state.get("seen_drop_ids", []))

    with get_conn_ro() as conn:
        df = pd.read_sql(
            "SELECT * FROM events WHERE event_type = 'price_drop' ORDER BY timestamp DESC LIMIT 100",
            conn,
        )

    for _, row in df.iterrows():
        pid = str(row.get("property_id", ""))
        if pid in seen_drop_ids:
            continue
        if pid in watched_props:
            detected.append({
                "type": "price_drop",
                "property_id": pid,
                "old_value": row.get("old_value"),
                "new_value": row.get("new_value"),
                "timestamp": row.get("timestamp"),
            })
            seen_drop_ids.add(pid)

    st.session_state["seen_drop_ids"] = list(seen_drop_ids)
    return detected


def get_unread_count() -> int:
    opportunities = check_new_opportunities()
    drops = check_price_drops()
    return len(opportunities) + len(drops)


def mark_all_read():
    wl = load_watchlist()
    watched_barrios = wl.get("barrios", [])
    df = get_top_opportunities(300)
    seen = set(st.session_state.get("seen_notification_ids", []))
    for _, row in df.iterrows():
        pid = str(row.get("propiedad_id", ""))
        barrio = str(row.get("barrio", ""))
        if barrio in watched_barrios:
            seen.add(pid)
    st.session_state["seen_notification_ids"] = list(seen)
    st.session_state["seen_drop_ids"] = []
