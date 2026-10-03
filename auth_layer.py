import streamlit as st
from supabase import create_client

from rbac import ROLE_CONFIG


ROLE_BY_SLUG = {
    config["slug"]: display_name
    for display_name, config in ROLE_CONFIG.items()
}


def supabase_configured():
    try:
        return bool(st.secrets.get("SUPABASE_URL")) and bool(
            st.secrets.get("SUPABASE_KEY")
        )
    except Exception:
        return False


def new_auth_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


def current_auth():
    return st.session_state.get("auth_context")


def role_from_user(user):
    app_metadata = getattr(user, "app_metadata", None) or {}
    role_slug = app_metadata.get("role") or app_metadata.get("user_role")
    role_name = ROLE_BY_SLUG.get(role_slug)
    return role_name, role_slug


def sign_in(email, password):
    client = new_auth_client()
    response = client.auth.sign_in_with_password(
        {"email": email, "password": password}
    )

    user = response.user
    session = response.session
    role_name, role_slug = role_from_user(user)

    if not role_name:
        try:
            client.auth.sign_out()
        finally:
            raise PermissionError(
                "Account authenticated, but no approved application role is assigned."
            )

    st.session_state.auth_client = client
    st.session_state.auth_context = {
        "mode": "authenticated",
        "user_id": str(user.id),
        "email": user.email,
        "role_name": role_name,
        "role_slug": role_slug,
        "driver_name": app_metadata.get("driver_name"),
        "personnel_id": app_metadata.get("personnel_id"),
        "access_token": session.access_token if session else None,
        "refresh_token": session.refresh_token if session else None,
    }
    return st.session_state.auth_context


def sign_out():
    client = st.session_state.get("auth_client")
    if client is not None:
        try:
            client.auth.sign_out()
        except Exception:
            pass

    for key in (
        "auth_client",
        "auth_context",
        "demo_authenticated",
        "demo_role",
    ):
        st.session_state.pop(key, None)


def enter_demo(role_name="Senior Officers"):
    st.session_state.demo_authenticated = True
    st.session_state.demo_role = role_name
    st.session_state.auth_context = {
        "mode": "demo",
        "user_id": None,
        "email": "portfolio-demo",
        "role_name": role_name,
        "role_slug": ROLE_CONFIG[role_name]["slug"],
    }


def set_demo_role(role_name):
    if st.session_state.get("auth_context", {}).get("mode") != "demo":
        return
    st.session_state.demo_role = role_name
    st.session_state.auth_context["role_name"] = role_name
    st.session_state.auth_context["role_slug"] = ROLE_CONFIG[role_name]["slug"]


def authenticated_client():
    if current_auth() and current_auth().get("mode") == "authenticated":
        return st.session_state.get("auth_client")
    return None
