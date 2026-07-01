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
        return {"perfil_inversion": "intermedio", "tour_completed": False, "plan": "Starter"}
    try:
        supabase = _get_client()
        result = supabase.table("user_preferences").select("*").eq("user_id", user_id).maybe_single().execute()
        if result.data:
            return {
                "perfil_inversion": result.data.get("perfil_inversion", "intermedio"),
                "tour_completed": result.data.get("tour_completed", False),
                "plan": result.data.get("plan", "Starter"),
            }
    except Exception as e:
        logger.warning(f"Error loading preferences: {e}")
    return {"perfil_inversion": "intermedio", "tour_completed": False, "plan": "Starter"}


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


def update_stripe_info(
    stripe_customer_id: str | None = None,
    subscription_id: str | None = None,
    subscription_status: str | None = None,
):
    user_id = get_user_id()
    if not user_id:
        return
    try:
        supabase = _get_client()
        data = {"user_id": user_id}
        if stripe_customer_id is not None:
            data["stripe_customer_id"] = stripe_customer_id
        if subscription_id is not None:
            data["stripe_subscription_id"] = subscription_id
        if subscription_status is not None:
            data["subscription_status"] = subscription_status
        supabase.table("user_preferences").upsert(data, on_conflict="user_id").execute()
    except Exception as e:
        logger.warning(f"Error updating stripe info: {e}")


def get_stripe_info() -> dict:
    user_id = get_user_id()
    if not user_id:
        return {}
    try:
        supabase = _get_client()
        result = supabase.table("user_preferences").select(
            "stripe_customer_id, stripe_subscription_id, subscription_status"
        ).eq("user_id", user_id).maybe_single().execute()
        if result.data:
            return {
                "stripe_customer_id": result.data.get("stripe_customer_id"),
                "stripe_subscription_id": result.data.get("stripe_subscription_id"),
                "subscription_status": result.data.get("subscription_status", "inactive"),
            }
    except Exception as e:
        logger.warning(f"Error loading stripe info: {e}")
    return {}


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


def is_tour_completed() -> bool:
    prefs = load_preferences()
    return prefs.get("tour_completed", False)


def save_tour_completed():
    user_id = get_user_id()
    if not user_id:
        return
    try:
        supabase = _get_client()
        data = {"user_id": user_id, "tour_completed": True}
        supabase.table("user_preferences").upsert(data, on_conflict="user_id").execute()
    except Exception as e:
        logger.warning(f"Error saving tour_completed: {e}")


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
