import sqlite3
import logging
import streamlit as st

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
from utils.db import add_is_premium_column
from utils.migrations import run_migrations
from utils.seed_data import seed_all as seed_synthetic, get_counts as seed_counts
from utils.supabase_sync import sync_from_supabase, needs_sync
from utils.auth import get_user, sign_in, sign_up, sign_out, send_magic_link, sign_in_with_google
from utils.bootstrap import bootstrap as bootstrap_db
from utils.user_store import is_tour_completed

# ========================
# ⚙️ CONFIGURACIÓN GENERAL
# ========================

st.set_page_config(
    page_title="Vivienda AI — Madrid Investment Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

user = get_user()

if user is None:
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown("""
        <div style="padding: 3rem 2rem;">
            <h1 style="color: white; font-size: 2.8rem; margin-bottom: 0.5rem;">🏠 Vivienda AI</h1>
            <p style="color: rgba(255,255,255,0.5); font-size: 1.1rem; margin-bottom: 1.5rem;">
                Madrid Investment Intelligence
            </p>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.05rem; line-height: 1.7;">
                La plataforma que usa inteligencia artificial para detectar <strong>oportunidades de inversión inmobiliaria</strong> en Madrid.
                Analizamos miles de propiedades en tiempo real y te mostramos las que mejor se ajustan a tu perfil inversor.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚡ Características")
        feats = [
            ("📡 Radar de oportunidades", "Detecta propiedades infravaloradas con scoring multi-factor"),
            ("🗺️ Mapa de calor interactivo", "Visualiza concentración de oportunidades por zona"),
            ("🤖 AI Copilot", "Análisis inteligente y recomendaciones de compra"),
            ("⚖️ Comparador", "Compara 2+ propiedades lado a lado con simulación"),
            ("🚨 Alertas & Watchlist", "Sigue propiedades y recibe notificaciones de mercado"),
            ("📊 Dashboard global", "KPIs, tendencias y eventos del mercado madrileño"),
        ]
        for icon, desc in feats:
            st.markdown(f"**{icon}** — {desc}")

    with col_r:
        st.markdown("""
        <div style="padding: 3rem 0;">
            <h2 style="color: white; text-align: center;">⚡ Planes</h2>
        </div>
        """, unsafe_allow_html=True)

        # ── CSS extra para cards de planes ──
        st.markdown("""
        <style>
            .plan-card { border-radius: 12px; padding: 1.5rem; text-align: center; height: 100%; transition: all 0.2s; }
            .plan-card:hover { transform: translateY(-2px); }
            .plan-card.free { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid rgba(255,255,255,0.08); }
            .plan-card.pro {
                background: linear-gradient(135deg, #0a2a1e 0%, #0a1a2e 100%);
                border: 2px solid #4ade80; position: relative;
                box-shadow: 0 0 20px rgba(74,222,128,0.1);
            }
            .plan-card.enterprise { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #fbbf24; }
            .plan-badge {
                position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
                background: linear-gradient(135deg, #4ade80, #22c55e); color: #0a0a1a;
                padding: 2px 14px; border-radius: 8px; font-size: 0.7rem; font-weight: 700;
                letter-spacing: 0.5px;
            }
            .plan-name { font-size: 1.2rem; font-weight: 700; margin-bottom: 0.25rem; }
            .plan-price { font-size: 2rem; font-weight: 700; color: white; margin: 0.5rem 0; }
            .plan-price-sub { font-size: 0.85rem; color: rgba(255,255,255,0.4); }
            .plan-divider { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 1rem 0; }
            .plan-feature { font-size: 0.85rem; padding: 0.2rem 0; }
            .plan-feature.avail { color: rgba(255,255,255,0.7); }
            .plan-feature.unavail { color: rgba(255,255,255,0.2); }
            .plan-feature.highlight { color: #4ade80; font-weight: 600; }
        </style>
        """, unsafe_allow_html=True)

        col_p1, col_p2, col_p3 = st.columns(3)

        with col_p1:
            st.markdown("""
            <div class="plan-card free">
                <div class="plan-name" style="color: #4ade80;">Starter</div>
                <div class="plan-price">Gratis</div>
                <div class="plan-price-sub">Siempre</div>
                <hr class="plan-divider">
                <div class="plan-feature avail">🏠 50 propiedades / mes</div>
                <div class="plan-feature avail">📡 Radar con scoring</div>
                <div class="plan-feature highlight">📊 Cards semáforo</div>
                <div class="plan-feature unavail">✕ Comparador + Watchlist</div>
                <div class="plan-feature unavail">✕ AI Copilot</div>
                <div style="margin-top: 0.8rem;"><span style="color: rgba(255,255,255,0.3); font-size: 0.75rem;">Datos demo sintéticos</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col_p2:
            st.markdown("""
            <div class="plan-card pro">
                <div class="plan-badge">MÁS ELEGIDO</div>
                <div class="plan-name" style="color: #4ade80; margin-top: 0.5rem;">Pro</div>
                <div class="plan-price"><strong>19€</strong> <span style="font-size: 1rem; color: rgba(255,255,255,0.4);">/mes</span></div>
                <div class="plan-price-sub">Cancela cuando quieras</div>
                <hr class="plan-divider">
                <div class="plan-feature highlight">🏠 Propiedades sin límite</div>
                <div class="plan-feature highlight">📡 Radar + semáforo financiero</div>
                <div class="plan-feature highlight">📊 86.183 propiedades reales (2018)</div>
                <div class="plan-feature avail">⚖️ Comparador multi-propiedad</div>
                <div class="plan-feature avail">🤖 AI Copilot + Watchlist</div>
                <div class="plan-feature avail">🚨 Alertas de mercado prioritarias</div>
                <div style="margin-top: 0.8rem;"><span style="color: rgba(255,255,255,0.3); font-size: 0.75rem;">Datos históricos Idealista18</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col_p3:
            st.markdown("""
            <div class="plan-card enterprise">
                <div class="plan-name" style="color: #fbbf24;">Enterprise</div>
                <div class="plan-price"><strong>49€</strong> <span style="font-size: 1rem; color: rgba(255,255,255,0.4);">/mes</span></div>
                <div class="plan-price-sub">Para equipos</div>
                <hr class="plan-divider">
                <div class="plan-feature avail">Todo lo de Pro</div>
                <div class="plan-feature avail">🔌 API de datos en tiempo real</div>
                <div class="plan-feature avail">🏙️ Datos multi-ciudad</div>
                <div class="plan-feature avail">🎓 Onboarding personalizado</div>
                <div class="plan-feature avail">📞 Soporte prioritario 24/7</div>
                <div class="plan-feature avail">🚀 Nuevas features primero</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.markdown("<h3 style='text-align: center; color: white;'>🔐 Accede a la plataforma</h3>", unsafe_allow_html=True)

        tab_login, tab_magic, tab_google, tab_signup = st.tabs([
            "🔑 Contraseña", "📧 Magic Link", "🔄 Google", "Crear Cuenta"
        ])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="tu@email.com", key="login_email")
                password = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_pass")
                submitted = st.form_submit_button("Iniciar Sesión", type="primary", width="stretch")
                if submitted:
                    if not email or not password:
                        st.error("Completa todos los campos")
                    else:
                        with st.spinner("Autenticando..."):
                            try:
                                resp = sign_in(email, password)
                                if resp and resp.user:
                                    st.rerun()
                                else:
                                    st.error("Email o contraseña incorrectos")
                            except Exception as e:
                                st.error(f"Error de conexión: {e}")

        with tab_magic:
            st.caption("Recibí un link mágico en tu email para entrar sin contraseña.")
            with st.form("magic_link_form"):
                ml_email = st.text_input("Email", placeholder="tu@email.com", key="ml_email")
                submitted_ml = st.form_submit_button("Enviar link mágico", type="primary", width="stretch")
                if submitted_ml:
                    if not ml_email:
                        st.error("Ingresá tu email")
                    else:
                        with st.spinner("Enviando link..."):
                            try:
                                resp = send_magic_link(ml_email)
                                if resp:
                                    st.success("Link mágico enviado. Revisá tu email (incluí spam).")
                                else:
                                    st.error("Error al enviar el link")
                            except Exception as e:
                                st.error(f"Error: {e}")

        with tab_google:
            st.caption("Accedé con tu cuenta de Google.")
            st.info("⚠️ Configurá Google OAuth en Supabase Auth Settings primero.")
            if st.button("🔄 Continuar con Google", type="primary", width="stretch"):
                try:
                    resp = sign_in_with_google()
                    if resp and resp.url:
                        st.markdown(f"[Abrir Google para iniciar sesión]({resp.url})")
                        st.success("Hacé clic en el link de arriba para continuar con Google.")
                except Exception as e:
                    st.error(f"Error: {e}")

        with tab_signup:
            with st.form("signup_form"):
                email = st.text_input("Email", placeholder="tu@email.com", key="signup_email")
                password = st.text_input("Contraseña", type="password", placeholder="••••••••", key="signup_pass")
                confirm = st.text_input("Confirmar contraseña", type="password", placeholder="••••••••", key="signup_confirm")
                submitted = st.form_submit_button("Crear Cuenta", type="primary", width="stretch")
                if submitted:
                    if not email or not password:
                        st.error("Completa todos los campos")
                    elif password != confirm:
                        st.error("Las contraseñas no coinciden")
                    elif len(password) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres")
                    else:
                        with st.spinner("Registrando..."):
                            try:
                                resp = sign_up(email, password)
                                if resp and resp.user:
                                    st.success("Registro exitoso. Revisa tu email para confirmar la cuenta.")
                                else:
                                    st.info("Registro creado. Revisa tu email para confirmar.")
                            except Exception as e:
                                st.error(f"Error al registrarse: {e}")

    st.stop()

# Tour redirect for new users
if not is_tour_completed():
    st.switch_page("pages/0_Bienvenida.py")
    st.stop()

# ========================
# FUNCIÓN: sincronizar desde Supabase, fallback sintético
# ========================

def _sync_or_seed():
    if not needs_sync():
        st.session_state["sync_status"] = "ok"
        return
    sync_from_supabase()
    if needs_sync():
        try:
            conn = sqlite3.connect("real_estate.db")
            conn.execute("PRAGMA foreign_keys=OFF")
            seed_synthetic(conn)
            for t, c in seed_counts(conn).items():
                print(f"  {t}: {c} rows")
            conn.close()
            st.toast("⚡ Datos sinteticos cargados (Supabase no disponible)")
            st.session_state["sync_status"] = "fallback"
        except Exception as e:
            print(f"Error al generar seed sintetico: {e}")
            st.session_state["sync_status"] = "error"
    else:
        st.toast("✅ Datos reales cargados desde Supabase!")
        st.session_state["sync_status"] = "ok"


# ========================
# 🛠️ INICIALIZACIÓN DB (UNA SOLA VEZ)
# ========================

if "db_initialized" not in st.session_state:
    bootstrap_db()
    run_migrations()
    add_is_premium_column()
    _sync_or_seed()
    st.session_state["db_initialized"] = True

# ========================
# REDIRECCIÓN AL RADAR (PÁGINA PRINCIPAL)
# ========================

st.switch_page("pages/1_Radar.py")
