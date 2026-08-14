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
    search_delay_seconds: float = 0.5,
    session_duration_minutes: int = 60,
):

    client = get_supabase()

    role = str(role).strip().lower()

    if role == "user":
        role = "standard_user"

    if role not in {
        "standard_user",
        "admin",
    }:
        role = "standard_user"

    search_delay_seconds = max(
        0.1,
        min(
            60.0,
            float(search_delay_seconds),
        ),
    )

    session_duration_minutes = max(
        5,
        min(
            1440,
            int(session_duration_minutes),
        ),
    )

    response = (
        client.table("users")
        .insert(
            {
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "active": True,
                "search_delay_seconds": (
                    search_delay_seconds
                ),
                "session_duration_minutes": (
                    session_duration_minutes
                ),
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

    clean_values = dict(values)

    # -----------------------------------------------------
    # Normalize role
    # -----------------------------------------------------

    if "role" in clean_values:

        role = str(
            clean_values["role"]
        ).strip().lower()

        if role == "user":
            role = "standard_user"

        if role not in {
            "standard_user",
            "admin",
        }:
            raise ValueError(
                "Invalid user role."
            )

        clean_values["role"] = role

    # -----------------------------------------------------
    # Normalize search delay
    # -----------------------------------------------------

    if "search_delay_seconds" in clean_values:

        delay = float(
            clean_values[
                "search_delay_seconds"
            ]
        )

        if delay < 0.1 or delay > 60:
            raise ValueError(
                "Search delay must be between "
                "0.1 and 60 seconds."
            )

        clean_values[
            "search_delay_seconds"
        ] = delay

    # -----------------------------------------------------
    # Normalize session duration
    # -----------------------------------------------------

    if "session_duration_minutes" in clean_values:

        duration = int(
            clean_values[
                "session_duration_minutes"
            ]
        )

        if duration < 5 or duration > 1440:
            raise ValueError(
                "Session duration must be between "
                "5 and 1440 minutes."
            )

        clean_values[
            "session_duration_minutes"
        ] = duration

    response = (
        client.table("users")
        .update(clean_values)
        .eq("username", username)
        .execute()
    )

    return response


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
            session_duration_minutes
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

    response = update_user(
        username,
        {
            "active": bool(active),
        },
    )

    # -----------------------------------------------------
    # If a user is disabled, immediately invalidate the
    # server-side session as well.
    # -----------------------------------------------------

    if not active:
        invalidate_user_session(username)

    return response


# =========================================================
# ACTIVE SESSIONS
# =========================================================

def get_active_session(
    username: str,
):

    client = get_supabase()

    response = (
        client.table("active_sessions")
        .select("*")
        .eq("username", username)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_session_by_token(
    session_token: str,
):

    if not session_token:
        return None

    client = get_supabase()

    response = (
        client.table("active_sessions")
        .select("*")
        .eq(
            "session_token",
            session_token,
        )
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_active_session(
    username: str,
    session_token: str,
    duration_minutes: int,
):

    client = get_supabase()

    duration_minutes = max(
        5,
        min(
            1440,
            int(duration_minutes),
        ),
    )

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            minutes=duration_minutes
        )
    )

    # -----------------------------------------------------
    # Make sure an old/expired session doesn't block login.
    # -----------------------------------------------------

    client.table(
        "active_sessions"
    ).delete().eq(
        "username",
        username,
    ).lt(
        "expires_at",
        now.isoformat(),
    ).execute()

    # -----------------------------------------------------
    # Insert new active session.
    #
    # The UNIQUE(username) constraint prevents two active
    # sessions for the same account.
    # -----------------------------------------------------

    response = (
        client.table(
            "active_sessions"
        )
        .insert(
            {
                "username": username,
                "session_token": session_token,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "last_seen_at": now.isoformat(),
            }
        )
        .execute()
    )

    return response.data


def update_session_last_seen(
    session_token: str,
):

    if not session_token:
        return None

    client = get_supabase()

    now = datetime.now(
        timezone.utc
    )

    response = (
        client.table(
            "active_sessions"
        )
        .update(
            {
                "last_seen_at": now.isoformat(),
            }
        )
        .eq(
            "session_token",
            session_token,
        )
        .execute()
    )

    return response


def invalidate_session(
    session_token: str,
):

    if not session_token:
        return None

    client = get_supabase()

    return (
        client.table(
            "active_sessions"
        )
        .delete()
        .eq(
            "session_token",
            session_token,
        )
        .execute()
    )


def invalidate_user_session(
    username: str,
):

    client = get_supabase()

    return (
        client.table(
            "active_sessions"
        )
        .delete()
        .eq(
            "username",
            username,
        )
        .execute()
    )


def cleanup_expired_sessions():

    client = get_supabase()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    return (
        client.table(
            "active_sessions"
        )
        .delete()
        .lte(
            "expires_at",
            now,
        )
        .execute()
    )


def validate_active_session(
    username: str,
    session_token: str,
):

    if not username or not session_token:
        return None

    session = get_session_by_token(
        session_token
    )

    if not session:
        return None

    if str(
        session.get("username", "")
    ) != str(username):
        return None

    # -----------------------------------------------------
    # Check expiration.
    # -----------------------------------------------------

    expires_at_raw = session.get(
        "expires_at"
    )

    if not expires_at_raw:
        invalidate_session(
            session_token
        )
        return None

    try:

        expires_at = datetime.fromisoformat(
            str(expires_at_raw).replace(
                "Z",
                "+00:00",
            )
        )

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

    except Exception:

        invalidate_session(
            session_token
        )

        return None

    now = datetime.now(
        timezone.utc
    )

    if expires_at <= now:

        invalidate_session(
            session_token
        )

        return None

    # -----------------------------------------------------
    # Check that the account still exists and is active.
    # -----------------------------------------------------

    user = get_user(username)

    if not user:
        invalidate_session(
            session_token
        )
        return None

    if not bool(
        user.get(
            "active",
            True,
        )
    ):

        invalidate_session(
            session_token
        )

        return None

    # -----------------------------------------------------
    # Update last activity.
    # -----------------------------------------------------

    update_session_last_seen(
        session_token
    )

    return {
        "session": session,
        "user": user,
    }


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
            + timedelta(
                days=1
            )
        )

        query = query.lt(
            "created_at",
            end_exclusive.isoformat(),
        )

    response = query.execute()

    return response.data or []


# =========================================================
# AUDIT RETENTION
# =========================================================

def delete_old_audit_logs():

    client = get_supabase()

    cutoff = (
        datetime.now(
            timezone.utc
        )
        - timedelta(
            days=90
        )
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
