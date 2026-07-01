import streamlit as st
from supabase import create_client
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL = "https://kozrvfyszumslfnvywtd.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtvenJ2ZnlzenVtc2xmbnZ5d3RkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI5MTI3NDUsImV4cCI6MjA5ODQ4ODc0NX0._-kucZIcoi4Q9l3BwHCEIh5J9Z5HTDo4K7IMvS0Bo78"


@st.cache_resource
def _get_client():
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def sign_up(email: str, password: str):
    supabase = _get_client()
    resp = supabase.auth.sign_up({"email": email, "password": password})
    if resp and resp.user and resp.user.email:
        st.session_state["supabase_session"] = resp
    return resp


def sign_in(email: str, password: str):
    supabase = _get_client()
    resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if resp and resp.user:
        st.session_state["supabase_session"] = resp
    return resp


def sign_out():
    supabase = _get_client()
    supabase.auth.sign_out()
    st.session_state.pop("supabase_session", None)
    st.rerun()


def get_user():
    session = st.session_state.get("supabase_session")
    if session and session.user:
        return session.user
    try:
        supabase = _get_client()
        s = supabase.auth.get_session()
        if s and s.user:
            st.session_state["supabase_session"] = s
            return s.user
    except Exception:
        pass
    return None


def require_auth():
    if get_user() is None:
        st.switch_page("app.py")
        st.stop()
