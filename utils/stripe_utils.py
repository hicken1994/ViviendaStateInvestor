import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

PRICE_LOOKUP = {
    "Pro": os.environ.get("STRIPE_PRICE_PRO", ""),
    "Enterprise": os.environ.get("STRIPE_PRICE_ENTERPRISE", ""),
}

PRODUCT_URL = "https://viviendastateinvestor.streamlit.app"
SUCCESS_URL = f"{PRODUCT_URL}/?checkout=success"
CANCEL_URL = f"{PRODUCT_URL}/?checkout=cancel"


def is_configured() -> bool:
    return bool(STRIPE_SECRET_KEY)


def _get_stripe():
    if not is_configured():
        return None
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    return stripe


def create_checkout_session(
    user_id: str,
    user_email: str,
    price_key: str = "Pro",
) -> str | None:
    stripe = _get_stripe()
    if stripe is None:
        logger.warning("Stripe not configured, cannot create checkout session")
        return None

    price_id = PRICE_LOOKUP.get(price_key)
    if not price_id:
        logger.error("No price ID configured for plan: %s", price_key)
        return None

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            client_reference_id=user_id,
            customer_email=user_email,
            success_url=SUCCESS_URL + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=CANCEL_URL,
            metadata={"plan": price_key, "user_id": user_id},
        )
        return session.url
    except Exception as e:
        logger.error("Stripe checkout error: %s", e)
        return None


def create_customer_portal_session(
    stripe_customer_id: str,
) -> str | None:
    stripe = _get_stripe()
    if stripe is None:
        return None

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=SUCCESS_URL,
        )
        return session.url
    except Exception as e:
        logger.error("Stripe portal error: %s", e)
        return None


def verify_checkout_session(session_id: str) -> dict | None:
    stripe = _get_stripe()
    if stripe is None:
        return None

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            return {
                "session_id": session.id,
                "user_id": session.metadata.get("user_id"),
                "plan": session.metadata.get("plan", "Pro"),
                "stripe_customer_id": session.customer,
                "subscription_id": session.subscription,
            }
    except Exception as e:
        logger.error("Stripe session verification error: %s", e)

    return None


FEATURES = {
    "Starter": {
        "max_properties_per_month": 50,
        "radar": True,
        "comparador": False,
        "ai_copilot": False,
        "api_access": False,
        "real_data": False,
        "multi_city": False,
        "priority_support": False,
        "personal_onboarding": False,
    },
    "Pro": {
        "max_properties_per_month": 999999,
        "radar": True,
        "comparador": True,
        "ai_copilot": True,
        "api_access": False,
        "real_data": True,
        "multi_city": False,
        "priority_support": False,
        "personal_onboarding": False,
    },
    "Enterprise": {
        "max_properties_per_month": 999999,
        "radar": True,
        "comparador": True,
        "ai_copilot": True,
        "api_access": True,
        "real_data": True,
        "multi_city": True,
        "priority_support": True,
        "personal_onboarding": True,
    },
}


def get_plan_features(plan: str = "Starter") -> dict[str, Any]:
    return FEATURES.get(plan, FEATURES["Starter"])


def has_feature(plan: str, feature: str) -> bool:
    return get_plan_features(plan).get(feature, False)
