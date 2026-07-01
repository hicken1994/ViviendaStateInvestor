import os
import streamlit as st
from supabase import create_client
from utils.auth import get_user
from utils.user_store import get_user_id

ADMIN_EMAILS = ["julianrincon434@gmail.com"]


def _get_admin_client():
    key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    if not key or not url:
        return None
    return create_client(url, key)


def es_admin() -> bool:
    user = get_user()
    if not user or not user.email:
        return False
    return user.email in ADMIN_EMAILS


def require_admin():
    if not es_admin():
        st.warning("🔒 Acceso restringido. Necesitás permisos de administrador.")
        st.stop()


def listar_usuarios() -> list[dict]:
    client = _get_admin_client()
    if not client:
        return []
    try:
        resp = client.table("user_preferences").select("*").order("created_at", desc=True).execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Error al cargar usuarios: {e}")
        return []


def actualizar_plan(user_id: str, plan: str) -> bool:
    client = _get_admin_client()
    if not client:
        return False
    try:
        client.table("user_preferences").update({"plan": plan}).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar plan: {e}")
        return False
