import streamlit as st
from utils.auth import _get_client
import logging

logger = logging.getLogger(__name__)


def get_user_id():
    session = st.session_state.get("supabase_session")
    if session and session.user:
        return session.user.id
    return None


def load_preferences() -> dict:
    user_id = get_user_id()
    if not user_id:
        return {"perfil_inversion": "intermedio"}
    try:
        supabase = _get_client()
        result = supabase.table("user_preferences").select("perfil_inversion").eq("user_id", user_id).maybe_single().execute()
        if result.data:
            return result.data
    except Exception as e:
        logger.warning(f"Error loading preferences: {e}")
    return {"perfil_inversion": "intermedio"}


def save_preference(key: str, value: str):
    user_id = get_user_id()
    if not user_id:
        return
    try:
        supabase = _get_client()
        data = {"user_id": user_id, key: value}
        supabase.table("user_preferences").upsert(data, on_conflict="user_id").execute()
    except Exception as e:
        logger.warning(f"Error saving preference {key}={value}: {e}")


def load_watchlist() -> dict:
    user_id = get_user_id()
    if not user_id:
        return {"propiedades": [], "barrios": []}
    try:
        supabase = _get_client()
        result = supabase.table("watchlists").select("property_ids, barrios").eq("user_id", user_id).maybe_single().execute()
        if result.data:
            return {
                "propiedades": result.data.get("property_ids", []),
                "barrios": result.data.get("barrios", []),
            }
    except Exception as e:
        logger.warning(f"Error loading watchlist: {e}")
    return {"propiedades": [], "barrios": []}


def save_watchlist(watchlist: dict):
    user_id = get_user_id()
    if not user_id:
        return
    try:
        supabase = _get_client()
        data = {
            "user_id": user_id,
            "property_ids": watchlist.get("propiedades", []),
            "barrios": watchlist.get("barrios", []),
        }
        supabase.table("watchlists").upsert(data, on_conflict="user_id").execute()
    except Exception as e:
        logger.warning(f"Error saving watchlist: {e}")
