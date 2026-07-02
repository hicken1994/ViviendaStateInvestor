import os
import logging
import streamlit as st

logger = logging.getLogger(__name__)

SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"


def _is_enabled() -> bool:
    key = st.secrets.get("SENDGRID_API_KEY") or os.environ.get("SENDGRID_API_KEY")
    return bool(key)


def _get_from_email() -> str:
    return st.secrets.get("SENDGRID_FROM_EMAIL") or os.environ.get("SENDGRID_FROM_EMAIL", "noreply@vivienda-ai.com")


def send_opportunity_alert(opp: dict, user_email: str):
    if not _is_enabled():
        logger.info("SendGrid no configurado — omitiendo email")
        return False
    if not user_email:
        return False

    import requests

    barrio = opp.get("barrio", "—")
    precio = opp.get("precio", 0)
    score = opp.get("score", 0)
    rent = opp.get("rentabilidad", 0)
    decision = opp.get("decision", "N/A")

    html = f"""
    <h2>Nueva oportunidad detectada en {barrio}</h2>
    <table style="border-collapse:collapse;width:100%">
        <tr><td style="padding:8px;border:1px solid #ddd"><strong>Barrio</strong></td>
            <td style="padding:8px;border:1px solid #ddd">{barrio}</td></tr>
        <tr><td style="padding:8px;border:1px solid #ddd"><strong>Precio</strong></td>
            <td style="padding:8px;border:1px solid #ddd">{int(precio):,} EUR</td></tr>
        <tr><td style="padding:8px;border:1px solid #ddd"><strong>Score</strong></td>
            <td style="padding:8px;border:1px solid #ddd">{score}/100</td></tr>
        <tr><td style="padding:8px;border:1px solid #ddd"><strong>Rentabilidad</strong></td>
            <td style="padding:8px;border:1px solid #ddd">{rent}%</td></tr>
        <tr><td style="padding:8px;border:1px solid #ddd"><strong>Decision</strong></td>
            <td style="padding:8px;border:1px solid #ddd">{decision}</td></tr>
    </table>
    <p style="color:#888;font-size:12px;">Vivienda AI — Madrid Investment Intelligence</p>
    """

    try:
        resp = requests.post(
            SENDGRID_URL,
            headers={
                "Authorization": f"Bearer {st.secrets.get('SENDGRID_API_KEY') or os.environ.get('SENDGRID_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": user_email}]}],
                "from": {"email": _get_from_email(), "name": "Vivienda AI"},
                "subject": f"Nueva oportunidad en {barrio} — Score: {score}",
                "content": [{"type": "text/html", "value": html}],
            },
        )
        if resp.ok:
            logger.info(f"Email enviado a {user_email} sobre {barrio}")
            return True
        else:
            logger.warning(f"Error SendGrid: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        logger.warning(f"Error al enviar email: {e}")
        return False
