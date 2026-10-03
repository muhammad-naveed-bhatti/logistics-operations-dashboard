import base64
import json

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


def decode_access_token(access_token):
    if not access_token:
        return {}

    try:
        payload = access_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except Exception:
        return {}


def role_from_session(user, session):
    claims = decode_access_token(session.access_token if session else None)
    app_metadata = getattr(user, "app_metadata", None) or {}

    role_slug = (
        claims.get("user_role")
        or app_metadata.get("role")
        or app_metadata.get("user_role")
    )
    role_name = ROLE_BY_SLUG.get(role_slug)

    identity = {
        "driver_name": claims.get("driver_name") or app_metadata.get("driver_name"),
        "personnel_id": claims.get("personnel_id") or app_metadata.get("personnel_id"),
    }
    return role_name, role_slug, identity


def resolve_database_identity(client, user_id):
    role_response = (
        client.table("user_roles")
        .select("role")
        .eq("user_id", str(user_id))
        .maybe_single()
        .execute()
    )
    role_row = role_response.data or {}
    role_slug = role_row.get("role")
    role_name = ROLE_BY_SLUG.get(role_slug)

    profile_response = (
        client.table("personnel_profiles")
        .select("personnel_id,driver_name")
        .eq("user_id", str(user_id))
        .maybe_single()
        .execute()
    )
    profile = profile_response.data or {}

    return role_name, role_slug, {
        "driver_name": profile.get("driver_name"),
        "personnel_id": profile.get("personnel_id"),
    }


def sign_in(email, password):
    client = new_auth_client()
    response = client.auth.sign_in_with_password(
        {"email": email, "password": password}
    )

    user = response.user
    session = response.session
    role_name, role_slug, identity = role_from_session(user, session)

    if not role_name:
        try:
            role_name, role_slug, db_identity = resolve_database_identity(client, user.id)
            identity["driver_name"] = identity["driver_name"] or db_identity["driver_name"]
            identity["personnel_id"] = identity["personnel_id"] or db_identity["personnel_id"]
        except Exception:
            role_name = None

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
        "driver_name": identity["driver_name"],
        "personnel_id": identity["personnel_id"],
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
