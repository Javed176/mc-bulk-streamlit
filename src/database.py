from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import streamlit as st
from supabase import Client, create_client


# =========================================================
# SUPABASE CONNECTION
# =========================================================

@st.cache_resource
def get_supabase() -> Client:

    url = str(
        st.secrets.get(
            "SUPABASE_URL",
            os.getenv("SUPABASE_URL", ""),
        )
    ).strip()

    key = str(
        st.secrets.get(
            "SUPABASE_SERVICE_ROLE_KEY",
            os.getenv(
                "SUPABASE_SERVICE_ROLE_KEY",
                "",
            ),
        )
    ).strip()

    if not url or not key:
        raise RuntimeError(
            "Supabase configuration is missing. "
            "Add SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY "
            "to Streamlit Secrets."
        )

    return create_client(url, key)


# =========================================================
# USERS
# =========================================================

def get_user(username: str):

    client = get_supabase()

    response = (
        client.table("users")
        .select("*")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_user_record(
    username: str,
    password_hash: str,
    role: str = "standard_user",
):

    client = get_supabase()

    response = (
        client.table("users")
        .insert(
            {
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "active": True,

                # DEFAULT SEARCH DELAY
                "search_delay_seconds": 0.5,

                # DEFAULT SESSION TIMEOUT
                "session_timeout_minutes": 60,

                "session_token": None,
                "session_started_at": None,
            }
        )
        .execute()
    )

    return response.data


def update_user(
    username: str,
    values: dict,
):

    client = get_supabase()

    return (
        client.table("users")
        .update(values)
        .eq("username", username)
        .execute()
    )


def list_users():

    client = get_supabase()

    response = (
        client.table("users")
        .select(
            """
            id,
            username,
            role,
            active,
            created_at,
            search_delay_seconds,
            session_timeout_minutes,
            session_token,
            session_started_at
            """
        )
        .order(
            "created_at",
            desc=False,
        )
        .execute()
    )

    return response.data or []


def delete_user(username: str):

    client = get_supabase()

    return (
        client.table("users")
        .delete()
        .eq("username", username)
        .execute()
    )


# =========================================================
# USER STATUS
# =========================================================

def set_user_active(
    username: str,
    active: bool,
):

    client = get_supabase()

    values = {
        "active": bool(active),
    }

    if not active:

        values["session_token"] = None
        values["session_started_at"] = None

    return (
        client.table("users")
        .update(values)
        .eq("username", username)
        .execute()
    )


# =========================================================
# USER SETTINGS
# =========================================================

def update_user_settings(
    username: str,
    search_delay_seconds: float | None = None,
    session_timeout_minutes: int | None = None,
):

    values = {}

    if search_delay_seconds is not None:

        # ZERO IS VALID
        values["search_delay_seconds"] = max(
            0.0,
            float(search_delay_seconds),
        )

    if session_timeout_minutes is not None:

        values["session_timeout_minutes"] = max(
            1,
            int(session_timeout_minutes),
        )

    if not values:
        return None

    client = get_supabase()

    return (
        client.table("users")
        .update(values)
        .eq("username", username)
        .execute()
    )


# =========================================================
# SESSION MANAGEMENT
# =========================================================

def create_user_session(
    username: str,
    session_token: str,
):

    client = get_supabase()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    # Updating the existing session_token automatically
    # invalidates the previous browser/tab session.
    response = (
        client.table("users")
        .update(
            {
                "session_token": session_token,
                "session_started_at": now,
            }
        )
        .eq("username", username)
        .eq("active", True)
        .execute()
    )

    return response.data


def get_user_session(username: str):

    client = get_supabase()

    response = (
        client.table("users")
        .select(
            """
            username,
            active,
            search_delay_seconds,
            session_timeout_minutes,
            session_token,
            session_started_at
            """
        )
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def validate_user_session(
    username: str,
    session_token: str,
):

    record = get_user_session(username)

    if not record:
        return False, "missing"

    if not bool(
        record.get("active", True)
    ):
        return False, "inactive"

    database_token = str(
        record.get(
            "session_token",
            "",
        )
        or ""
    )

    if not database_token:
        return False, "no_session"

    if database_token != str(
        session_token
    ):
        return False, "session_replaced"

    started_at = record.get(
        "session_started_at"
    )

    if not started_at:
        return False, "no_start_time"

    try:

        started = datetime.fromisoformat(
            str(started_at).replace(
                "Z",
                "+00:00",
            )
        )

        if started.tzinfo is None:

            started = started.replace(
                tzinfo=timezone.utc
            )

        timeout_minutes = max(
            1,
            int(
                record.get(
                    "session_timeout_minutes",
                    60,
                )
            ),
        )

        expires_at = (
            started
            + timedelta(
                minutes=timeout_minutes
            )
        )

        if datetime.now(
            timezone.utc
        ) >= expires_at:

            clear_user_session(
                username,
                session_token,
            )

            return False, "expired"

    except Exception:

        return False, "invalid_time"

    return True, "ok"


def clear_user_session(
    username: str,
    session_token: str | None = None,
):

    client = get_supabase()

    query = (
        client.table("users")
        .update(
            {
                "session_token": None,
                "session_started_at": None,
            }
        )
        .eq("username", username)
    )

    if session_token:

        query = query.eq(
            "session_token",
            session_token,
        )

    return query.execute()


# =========================================================
# AUDIT
# =========================================================

def insert_audit(
    username: str,
    action: str,
    mc_number: str = "",
    details: str = "",
):

    client = get_supabase()

    return (
        client.table("audit_logs")
        .insert(
            {
                "username": username,
                "action": action,
                "mc_number": mc_number,
                "details": details,
            }
        )
        .execute()
    )


def get_audit_logs(
    username: str | None = None,
    action: str | None = None,
    start_date=None,
    end_date=None,
):

    client = get_supabase()

    query = (
        client.table("audit_logs")
        .select("*")
        .order(
            "created_at",
            desc=True,
        )
    )

    if username:

        query = query.eq(
            "username",
            username,
        )

    if action:

        query = query.eq(
            "action",
            action,
        )

    if start_date:

        query = query.gte(
            "created_at",
            start_date.isoformat(),
        )

    if end_date:

        end_exclusive = (
            end_date
            + timedelta(days=1)
        )

        query = query.lt(
            "created_at",
            end_exclusive.isoformat(),
        )

    response = query.execute()

    return response.data or []


# =========================================================
# ACCESS REQUEST
# =========================================================

def create_access_request(
    whatsapp_number: str,
):

    number = str(
        whatsapp_number
    ).strip()

    if not number:
        raise ValueError(
            "WhatsApp number is required."
        )

    # Keep the request limited to the phone number.
    # No username or password is requested.
    return insert_audit(
        username="ACCESS_REQUEST",
        action="ACCESS_REQUEST",
        mc_number="",
        details=(
            f"WhatsApp: {number}"
        ),
    )


# =========================================================
# 90-DAY AUDIT RETENTION
# =========================================================

def delete_old_audit_logs():

    client = get_supabase()

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=90)
    ).isoformat()

    return (
        client.table("audit_logs")
        .delete()
        .lt(
            "created_at",
            cutoff,
        )
        .execute()
    )
