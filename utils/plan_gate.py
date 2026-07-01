import streamlit as st
from utils.user_store import load_preferences
from utils.stripe_utils import has_feature, is_configured as stripe_configured


def get_user_plan() -> str:
    prefs = load_preferences()
    return prefs.get("plan", "Starter")


def require_feature(feature: str) -> bool:
    plan = get_user_plan()
    if has_feature(plan, feature):
        return True
    return False


def check_feature(feature: str) -> bool:
    return require_feature(feature)


def render_upgrade_cta(
    feature_name: str = "esta función",
    plan_name: str = "Pro",
):
    st.warning(f"### 🔒 {feature_name} está disponible solo en el plan {plan_name}")
    st.markdown(
        f"Actualiza tu plan para desbloquear {feature_name} y muchas más funcionalidades."
    )

    if stripe_configured():
        user_id = st.session_state.get("supabase_session")
        user_email = user_id.user.email if user_id and user_id.user else ""

        from utils.stripe_utils import create_checkout_session

        if st.button(f"⬆️ Actualizar a {plan_name}", type="primary", width="stretch"):
            url = create_checkout_session(
                user_id=user_id.user.id if user_id else "",
                user_email=user_email,
                price_key=plan_name,
            )
            if url:
                st.markdown(f"[Pagar ahora]({url})")
                st.info("Redirigiendo a Stripe para el pago seguro...")
            else:
                st.error(
                    "No se pudo crear la sesión de pago. "
                    "Contacta a soporte si el problema persiste."
                )
    else:
        st.info("💳 Próximamente: pago con tarjeta vía Stripe. Estamos ultimando los detalles.")
        st.button("⬆️ Actualizar a Pro", disabled=True, width="stretch")


def render_feature_gate(feature: str, feature_name: str = "esta función"):
    if not require_feature(feature):
        render_upgrade_cta(feature_name=feature_name)
        st.stop()
        return False
    return True
