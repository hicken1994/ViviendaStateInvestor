import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://kozrvfyszumslfnvywtd.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

try:
    from supabase import create_client
except ImportError:
    create_client = None

try:
    import stripe
except ImportError:
    stripe = None


def handle_checkout_completed(session: dict) -> bool:
    user_id = session.get("metadata", {}).get("user_id")
    plan = session.get("metadata", {}).get("plan", "Pro")
    stripe_customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    if not user_id or not SUPABASE_SERVICE_KEY:
        logger.error("Missing user_id or SUPABASE_SERVICE_ROLE_KEY")
        return False

    if not create_client:
        logger.error("supabase package not installed")
        return False

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    try:
        supabase.table("user_preferences").upsert({
            "user_id": user_id,
            "plan": plan,
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": subscription_id,
            "subscription_status": "active",
        }, on_conflict="user_id").execute()
        logger.info("Plan updated for user %s → %s", user_id, plan)
        return True
    except Exception as e:
        logger.error("Failed to update plan: %s", e)
        return False


def handle_subscription_deleted(subscription: dict) -> bool:
    customer_id = subscription.get("customer")
    if not customer_id or not SUPABASE_SERVICE_KEY or not create_client:
        return False

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    try:
        result = supabase.table("user_preferences").update({
            "plan": "Starter",
            "subscription_status": "canceled",
        }).eq("stripe_customer_id", customer_id).execute()
        logger.info("Subscription canceled for customer %s", customer_id)
        return bool(result.data)
    except Exception as e:
        logger.error("Failed to cancel subscription: %s", e)
        return False


if os.environ.get("WEBHOOK_MODE") == "flask":
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    @app.route("/webhook/stripe", methods=["POST"])
    def stripe_webhook():
        if not stripe or not STRIPE_WEBHOOK_SECRET:
            return jsonify({"error": "Stripe not configured"}), 500

        payload = request.get_data()
        sig_header = request.headers.get("Stripe-Signature")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except ValueError:
            return jsonify({"error": "Invalid payload"}), 400
        except stripe.error.SignatureVerificationError:
            return jsonify({"error": "Invalid signature"}), 400

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            handle_checkout_completed(session)
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            handle_subscription_deleted(subscription)

        return jsonify({"status": "ok"}), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    if os.environ.get("WEBHOOK_MODE") == "flask":
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    else:
        print("Set WEBHOOK_MODE=flask to run the webhook server")
