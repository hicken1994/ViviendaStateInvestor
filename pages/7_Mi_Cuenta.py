import streamlit as st
from utils.auth import require_auth, get_user, sign_out
from utils.user_store import load_preferences, load_watchlist, save_tour_completed, get_stripe_info
from utils.stripe_utils import create_checkout_session, create_customer_portal_session, is_configured, get_plan_features

st.set_page_config(page_title="Mi Cuenta", page_icon="👤", layout="wide")

require_auth()

user = get_user()
prefs = load_preferences()
wl = load_watchlist()
stripe_info = get_stripe_info()

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
    .feature-check { color: #4ade80; }
    .feature-cross { color: rgba(255,255,255,0.3); }
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

        if is_configured():
            if st.button("⬆️ Actualizar a Pro — 19€/mes", width="stretch", type="primary"):
                uid = user.id if user else ""
                email = user.email if user else ""
                url = create_checkout_session(uid, email, "Pro")
                if url:
                    st.markdown(f"[Pagar ahora en Stripe]({url})")
                    st.info("Serás redirigido a Stripe para el pago seguro.")
                else:
                    st.error("Error al crear sesión de pago.")
        else:
            st.info("💳 Pago con tarjeta disponible próximamente.")
            st.button("⬆️ Actualizar a Pro", disabled=True, width="stretch")
    else:
        st.markdown("---")
        features = get_plan_features(plan)
        if features.get("real_data"):
            st.success("✅ Datos en vivo de Idealista activados")
        if features.get("ai_copilot"):
            st.success("✅ AI Copilot disponible")
        if features.get("comparador"):
            st.success("✅ Comparador disponible")

        stripe_customer = stripe_info.get("stripe_customer_id")
        if stripe_customer and is_configured():
            if st.button("💳 Gestionar suscripción", width="stretch"):
                portal_url = create_customer_portal_session(stripe_customer)
                if portal_url:
                    st.markdown(f"[Ir al portal de Stripe]({portal_url})")

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
        data_label = "Datos en vivo" if plan in ("Pro", "Enterprise") else "3.000+ sintéticas"
        st.markdown(f'<div class="stat-value">{data_label.split()[0]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-label">{" ".join(data_label.split()[1:])}</div>', unsafe_allow_html=True)

    st.divider()

    if props_count > 0:
        st.markdown("**Últimas propiedades vigiladas:**")
        for pid in wl["propiedades"][:5]:
            st.markdown(f"- 🏠 Propiedad #{pid}")
    else:
        st.caption("No tienes propiedades vigiladas. Ve al Radar para empezar.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="acct-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Comparativa de planes")

    plan_cols = st.columns(3)
    plan_names = ["Starter", "Pro", "Enterprise"]
    plan_prices = ["Gratis", "19€/mes", "49€/mes"]

    for i, (pname, pprice) in enumerate(zip(plan_names, plan_prices)):
        with plan_cols[i]:
            feats = get_plan_features(pname)
            highlight = "🟢" if pname == plan else ""
            st.markdown(f"**{highlight} {pname}** — {pprice}")
            st.markdown(f"<span class='feature-check'>✅</span> Radar", unsafe_allow_html=True)
            st.markdown(
                f"<span class='feature-check'>✅</span> Comparador"
                if feats["comparador"]
                else f"<span class='feature-cross'>✕</span> Comparador",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<span class='feature-check'>✅</span> AI Copilot"
                if feats["ai_copilot"]
                else f"<span class='feature-cross'>✕</span> AI Copilot",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<span class='feature-check'>✅</span> Datos en vivo"
                if feats["real_data"]
                else f"<span class='feature-cross'>✕</span> Datos en vivo",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption("Vivienda AI — Madrid Investment Intelligence. Todos los derechos reservados.")
