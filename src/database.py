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
        .eq("username", username.strip())
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
    search_delay_seconds: float = 1.0,
    session_timeout_minutes: int = 60,
):

    client = get_supabase()

    response = (
        client.table("users")
        .insert(
            {
                "username": username.strip(),
                "password_hash": password_hash,
                "role": role,
                "active": True,
                "search_delay_seconds": float(
                    max(0.0, search_delay_seconds)
                ),
                "session_timeout_minutes": int(
                    max(1, session_timeout_minutes)
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
            session_timeout_minutes
            """
        )
        .order(
            "created_at",
            desc=False,
        )
        .execute()
    )

    users = response.data or []

    # Add live session information separately.
    for user in users:

        username = str(
            user.get("username", "")
        )

        session = get_active_session(
            username
        )

        if session:

            user["session_active"] = True
            user["session_started_at"] = (
                session.get("created_at")
            )
            user["session_expires_at"] = (
                session.get("expires_at")
            )

        else:

            user["session_active"] = False
            user["session_started_at"] = None
            user["session_expires_at"] = None

    return users


def delete_user(username: str):

    # Destroy any active session first.
    clear_user_sessions(username)

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

    result = (
        client.table("users")
        .update(
            {
                "active": bool(active),
            }
        )
        .eq("username", username)
        .execute()
    )

    # Immediately terminate sessions when disabling.
    if not active:
        clear_user_sessions(username)

    return result


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


def get_user_search_delay(
    username: str,
) -> float:

    user = get_user(username)

    if not user:
        return 1.0

    try:

        return max(
            0.0,
            float(
                user.get(
                    "search_delay_seconds",
                    1.0,
                )
            ),
        )

    except Exception:

        return 1.0


def get_user_session_timeout(
    username: str,
) -> int:

    user = get_user(username)

    if not user:
        return 60

    try:

        return max(
            1,
            int(
                user.get(
                    "session_timeout_minutes",
                    60,
                )
            ),
        )

    except Exception:

        return 60


# =========================================================
# GLOBAL APPLICATION SETTINGS
# =========================================================

def get_app_setting(
    setting_key: str,
    default=None,
):

    client = get_supabase()

    try:

        response = (
            client.table("app_settings")
            .select("setting_value")
            .eq(
                "setting_key",
                setting_key,
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return default

        return response.data[0].get(
            "setting_value",
            default,
        )

    except Exception:

        return default


def set_app_setting(
    setting_key: str,
    setting_value,
):

    client = get_supabase()

    existing = (
        client.table("app_settings")
        .select("id")
        .eq(
            "setting_key",
            setting_key,
        )
        .limit(1)
        .execute()
    )

    value = str(setting_value)

    if existing.data:

        return (
            client.table("app_settings")
            .update(
                {
                    "setting_value": value,
                    "updated_at":
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                }
            )
            .eq(
                "setting_key",
                setting_key,
            )
            .execute()
        )

    return (
        client.table("app_settings")
        .insert(
            {
                "setting_key": setting_key,
                "setting_value": value,
            }
        )
        .execute()
    )


def get_default_search_delay() -> float:

    value = get_app_setting(
        "default_search_delay",
        "1",
    )

    try:
        return max(
            0.0,
            float(value),
        )
    except Exception:
        return 1.0


def get_default_session_timeout() -> int:

    value = get_app_setting(
        "default_session_timeout",
        "60",
    )

    try:
        return max(
            1,
            int(float(value)),
        )
    except Exception:
        return 60


# =========================================================
# ACTIVE SESSION MANAGEMENT
# =========================================================

def get_active_session(
    username: str,
):

    client = get_supabase()

    response = (
        client.table("active_sessions")
        .select("*")
        .eq(
            "username",
            username.strip(),
        )
        .eq(
            "active",
            True,
        )
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    session = response.data[0]

    # Automatically remove expired sessions.
    expires_at = session.get(
        "expires_at"
    )

    if expires_at:

        try:

            expires = datetime.fromisoformat(
                str(expires_at).replace(
                    "Z",
                    "+00:00",
                )
            )

            if expires.tzinfo is None:
                expires = expires.replace(
                    tzinfo=timezone.utc
                )

            if datetime.now(
                timezone.utc
            ) >= expires:

                clear_user_session_by_id(
                    session.get("id")
                )

                return None

        except Exception:
            pass

    return session


def create_user_session(
    username: str,
    session_token: str,
    timeout_minutes: int | None = None,
):

    username = username.strip()

    # Verify account first.
    user = get_user(username)

    if not user:
        return False, "missing"

    if not bool(
        user.get("active", True)
    ):
        return False, "inactive"

    # Get timeout from the user account.
    if timeout_minutes is None:

        timeout_minutes = (
            get_user_session_timeout(
                username
            )
        )

    timeout_minutes = max(
        1,
        int(timeout_minutes),
    )

    # -----------------------------------------------------
    # Existing session
    # -----------------------------------------------------

    existing = get_active_session(
        username
    )

    if existing:

        return False, "already_logged_in"

    # -----------------------------------------------------
    # Create new session
    # -----------------------------------------------------

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            minutes=timeout_minutes
        )
    )

    client = get_supabase()

    try:

        response = (
            client.table(
                "active_sessions"
            )
            .insert(
                {
                    "username": username,
                    "session_token":
                        session_token,
                    "created_at":
                        now.isoformat(),
                    "last_seen_at":
                        now.isoformat(),
                    "expires_at":
                        expires_at.isoformat(),
                    "active": True,
                }
            )
            .execute()
        )

        if not response.data:
            return False, "create_failed"

        return True, response.data[0]

    except Exception as exc:

        # Unique index protects against two
        # simultaneous logins.
        message = str(exc).lower()

        if (
            "duplicate"
            in message
            or "unique"
            in message
        ):
            return False, "already_logged_in"

        raise


def validate_user_session(
    username: str,
    session_token: str,
):

    username = username.strip()

    user = get_user(username)

    if not user:
        return False, "missing"

    if not bool(
        user.get("active", True)
    ):
        clear_user_sessions(username)
        return False, "inactive"

    session = get_active_session(
        username
    )

    if not session:

        return False, "no_session"

    database_token = str(
        session.get(
            "session_token",
            "",
        )
        or ""
    )

    if not database_token:

        return False, "no_token"

    if not hmac_compare(
        database_token,
        str(session_token),
    ):

        return False, "session_replaced"

    expires_at = session.get(
        "expires_at"
    )

    if not expires_at:

        return False, "invalid_time"

    try:

        expires = datetime.fromisoformat(
            str(expires_at).replace(
                "Z",
                "+00:00",
            )
        )

        if expires.tzinfo is None:

            expires = expires.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(
            timezone.utc
        )

        if now >= expires:

            clear_user_session(
                username,
                session_token,
            )

            return False, "expired"

    except Exception:

        return False, "invalid_time"

    return True, "ok"


def hmac_compare(
    first: str,
    second: str,
) -> bool:

    import hmac

    return hmac.compare_digest(
        str(first),
        str(second),
    )


def touch_user_session(
    username: str,
    session_token: str,
):

    client = get_supabase()

    now = datetime.now(
        timezone.utc
    ).isoformat()

    response = (
        client.table(
            "active_sessions"
        )
        .update(
            {
                "last_seen_at": now,
            }
        )
        .eq(
            "username",
            username.strip(),
        )
        .eq(
            "session_token",
            session_token,
        )
        .eq(
            "active",
            True,
        )
        .execute()
    )

    return response.data


def clear_user_session(
    username: str,
    session_token: str | None = None,
):

    client = get_supabase()

    query = (
        client.table(
            "active_sessions"
        )
        .update(
            {
                "active": False,
            }
        )
        .eq(
            "username",
            username.strip(),
        )
        .eq(
            "active",
            True,
        )
    )

    if session_token:

        query = query.eq(
            "session_token",
            session_token,
        )

    return query.execute()


def clear_user_session_by_id(
    session_id,
):

    if not session_id:
        return None

    client = get_supabase()

    return (
        client.table(
            "active_sessions"
        )
        .update(
            {
                "active": False,
            }
        )
        .eq(
            "id",
            session_id,
        )
        .execute()
    )


def clear_user_sessions(
    username: str,
):

    client = get_supabase()

    return (
        client.table(
            "active_sessions"
        )
        .update(
            {
                "active": False,
            }
        )
        .eq(
            "username",
            username.strip(),
        )
        .eq(
            "active",
            True,
        )
        .execute()
    )


def force_logout_user(
    username: str,
):

    return clear_user_sessions(
        username
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
        .update(
            {
                "active": False,
            }
        )
        .eq(
            "active",
            True,
        )
        .lt(
            "expires_at",
            now,
        )
        .execute()
    )


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
