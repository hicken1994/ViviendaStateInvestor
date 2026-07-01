import streamlit as st
from utils.auth import require_auth, get_user, sign_out
from utils.user_store import load_preferences, load_watchlist, save_tour_completed

st.set_page_config(page_title="Mi Cuenta", page_icon="👤", layout="wide")

require_auth()

user = get_user()
prefs = load_preferences()
wl = load_watchlist()

st.markdown("""
<style>
    .acct-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 1.5rem;
        height: 100%;
    }
    .acct-card h3 { color: white; margin-bottom: 0.5rem; }
    .acct-card p { color: rgba(255,255,255,0.7); margin-bottom: 0.25rem; }
    .plan-badge {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .plan-starter { background: rgba(100,100,100,0.3); color: #aaa; }
    .plan-pro { background: rgba(74,222,128,0.2); color: #4ade80; }
    .plan-enterprise { background: rgba(251,191,36,0.2); color: #fbbf24; }
    .stat-value { font-size: 1.8rem; font-weight: 700; color: white; }
    .stat-label { font-size: 0.8rem; color: rgba(255,255,255,0.5); }
</style>
""", unsafe_allow_html=True)

st.markdown("# 👤 Mi Cuenta")

col_left, col_right = st.columns([1, 2])

with col_left:
    plan = prefs.get("plan", "Starter")
    plan_class = {"Starter": "plan-starter", "Pro": "plan-pro", "Enterprise": "plan-enterprise"}.get(plan, "plan-starter")

    st.markdown('<div class="acct-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Perfil")
    st.markdown(f"**Email:** {user.email if user else '—'}")
    st.markdown(
        f"**Plan:** <span class='plan-badge {plan_class}'>{plan}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Perfil de inversión:** {prefs.get('perfil_inversion', 'intermedio').capitalize()}")
    if plan == "Starter":
        st.markdown("---")
        st.markdown("### ⬆️ Mejora tu plan")
        st.markdown("Desbloquea propiedades ilimitadas, AI Copilot y más.")
        if st.button("Ver planes", width="stretch", type="primary"):
            st.switch_page("app.py")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="acct-card">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Acciones")
    if st.button("🔄 Repetir tour de bienvenida", width="stretch"):
        save_tour_completed()
        st.session_state.pop("watchlist", None)
        st.switch_page("pages/0_Bienvenida.py")
    if st.button("🚪 Cerrar sesión", width="stretch"):
        sign_out()
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="acct-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Resumen de actividad")

    props_count = len(wl.get("propiedades", []))
    barrios_count = len(wl.get("barrios", []))

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown(f'<div class="stat-value">{props_count}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Propiedades vigiladas</div>', unsafe_allow_html=True)
    with col_s2:
        st.markdown(f'<div class="stat-value">{barrios_count}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Barrios vigilados</div>', unsafe_allow_html=True)
    with col_s3:
        st.markdown(f'<div class="stat-value">3.000+</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Propiedades en base</div>', unsafe_allow_html=True)

    st.divider()

    if props_count > 0:
        st.markdown("**Últimas propiedades vigiladas:**")
        for pid in wl["propiedades"][:5]:
            st.markdown(f"- 🏠 Propiedad #{pid}")
    else:
        st.caption("No tienes propiedades vigiladas. Ve al Radar para empezar.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="acct-card">', unsafe_allow_html=True)
    st.markdown("### ℹ️ Sobre Vivienda AI")
    st.markdown("""
    **Versión:** 1.0.0  
    **Datos:** Mercado de Madrid (3.000+ propiedades sintéticas)  
    **Stack:** Streamlit + Supabase + Plotly + PyDeck  
    """)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption("Vivienda AI — Madrid Investment Intelligence. Todos los derechos reservados.")
