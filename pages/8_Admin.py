import streamlit as st
from utils.auth import require_auth
from utils.admin import require_admin, listar_usuarios, actualizar_plan

require_auth()
require_admin()

st.title("⚙️ Panel de Administración")
st.caption("Gestión de usuarios y configuración de la plataforma.")

# ========================
# SECCIÓN: CONFIGURACIÓN
# ========================

with st.expander("🔐 Configuración requerida", expanded=False):
    has_svc = bool(
        st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
        or __import__("os").environ.get("SUPABASE_SERVICE_ROLE_KEY")
    )
    if has_svc:
        st.success("✅ Service Role Key configurada")
    else:
        st.error("❌ Service Role Key NO configurada")
        st.info(
            "Andá a Supabase Dashboard → Settings → API → `service_role key` "
            "y agregala a `.streamlit/secrets.toml` como `SUPABASE_SERVICE_ROLE_KEY`."
        )
        st.stop()

    has_rapidapi = bool(
        st.secrets.get("RAPIDAPI_KEY")
        or __import__("os").environ.get("RAPIDAPI_KEY")
    )
    if has_rapidapi:
        st.success("✅ RapidAPI Key configurada (Idealista)")
    else:
        st.warning("⚠️ RapidAPI Key no configurada — los datos Pro seguirán siendo sintéticos")

# ========================
# SECCIÓN: USUARIOS
# ========================

st.divider()
st.subheader("👥 Usuarios")

usuarios = listar_usuarios()

if not usuarios:
    st.info("No se encontraron usuarios o no hay conexión con Supabase.")
    st.stop()

# --- Filtro ---
busqueda = st.text_input("🔍 Filtrar por email o user_id", "")

cols = st.columns([2, 1.5, 1, 1, 1])
cols[0].markdown("**Email / User ID**")
cols[1].markdown("**Plan**")
cols[2].markdown("**Perfil**")
cols[3].markdown("**Admin**")
cols[4].markdown("**Acción**")

st.markdown("---")

for u in usuarios:
    uid = u.get("user_id", "")
    plan = u.get("plan", "Starter")
    perfil = u.get("perfil_inversion", "")
    admin = "✅" if u.get("is_admin") else ""

    if busqueda and busqueda.lower() not in uid.lower() and busqueda.lower() not in str(u.get("user_id", "")).lower():
        continue

    cols = st.columns([2, 1.5, 1, 1, 1])
    cols[0].markdown(f"`{uid[:12]}...`")
    cols[1].markdown(f"**{plan}**")

    with cols[2]:
        st.caption(perfil)

    cols[3].markdown(admin)

    with cols[4]:
        nuevo_plan = st.selectbox(
            "Cambiar plan",
            ["Starter", "Pro", "Enterprise"],
            index=["Starter", "Pro", "Enterprise"].index(plan) if plan in ["Starter", "Pro", "Enterprise"] else 0,
            key=f"plan_{uid}",
            label_visibility="collapsed",
        )
        if nuevo_plan != plan:
            if st.button(f"Guardar", key=f"save_{uid}", type="primary"):
                if actualizar_plan(uid, nuevo_plan):
                    st.success(f"✅ Plan de `{uid[:12]}...` actualizado a **{nuevo_plan}**")
                    st.rerun()
