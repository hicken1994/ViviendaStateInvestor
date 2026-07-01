import os
import streamlit as st
from supabase import create_client
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY")


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
