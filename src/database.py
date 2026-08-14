from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import streamlit as st
from supabase import Client, create_client


# =========================================================
# SAFE SECRET READER
# =========================================================

def _get_secret(
    name: str,
    default: str = "",
) -> str:
    """
    Safely read a Streamlit secret.

    Falls back to environment variables.
    """

    try:
        value = st.secrets.get(
            name,
            None,
        )

        if value is not None:
            return str(value).strip()

    except Exception:
        pass

    return str(
        os.getenv(
            name,
            default,
        )
    ).strip()


# =========================================================
# SUPABASE CONNECTION
# =========================================================

@st.cache_resource
def get_supabase() -> Client:
    """
    Create and cache the Supabase client.

    IMPORTANT:
    The service-role key must only be stored in
    Streamlit Secrets / environment variables.
    """

    url = _get_secret(
        "SUPABASE_URL"
    )

    key = _get_secret(
        "SUPABASE_SERVICE_ROLE_KEY"
    )

    if not url:
        raise RuntimeError(
            "SUPABASE_URL is missing from "
            "Streamlit Secrets."
        )

    if not key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY is missing "
            "from Streamlit Secrets."
        )

    return create_client(
        url,
        key,
    )


# =========================================================
# USERS
# =========================================================

def get_user(
    username: str,
) -> dict[str, Any] | None:

    client = get_supabase()

    response = (
        client.table("users")
        .select("*")
        .eq(
            "username",
            str(username).strip(),
        )
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

    clean_username = str(
        username
    ).strip()

    clean_role = str(
        role
    ).strip().lower()

    if clean_role not in {
        "standard_user",
        "admin",
    }:
        clean_role = "standard_user"

    response = (
        client.table("users")
        .insert(
            {
                "username": clean_username,
                "password_hash": password_hash,
                "role": clean_role,
                "active": True,

                # Current database schema supports this.
                "search_delay_seconds": 0.5,

                # This is the field used by the application.
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
        .eq(
            "username",
            str(username).strip(),
        )
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


def delete_user(
    username: str,
):

    client = get_supabase()

    return (
        client.table("users")
        .delete()
        .eq(
            "username",
            str(username).strip(),
        )
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
        .eq(
            "username",
            str(username).strip(),
        )
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

    values: dict[str, Any] = {}

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
        .eq(
            "username",
            str(username).strip(),
        )
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

    response = (
        client.table("users")
        .update(
            {
                "session_token": str(
                    session_token
                ),
                "session_started_at": now,
            }
        )
        .eq(
            "username",
            str(username).strip(),
        )
        .eq(
            "active",
            True,
        )
        .execute()
    )

    return response.data


def get_user_session(
    username: str,
):

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
        .eq(
            "username",
            str(username).strip(),
        )
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

    record = get_user_session(
        username
    )

    if not record:
        return False, "missing"

    if not bool(
        record.get(
            "active",
            True,
        )
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
                or 60
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
        .eq(
            "username",
            str(username).strip(),
        )
    )

    if session_token:

        query = query.eq(
            "session_token",
            str(session_token),
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
                "username": str(username),
                "action": str(action),
                "mc_number": str(mc_number),
                "details": str(details),
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
# ACCESS REQUESTS
# =========================================================

def create_access_request(
    whatsapp_number: str,
):

    client = get_supabase()

    number = str(
        whatsapp_number
    ).strip()

    if not number:
        raise ValueError(
            "WhatsApp number is required."
        )

    # -----------------------------------------------------
    # Find most recent request
    # -----------------------------------------------------

    response = (
        client.table("access_requests")
        .select("*")
        .eq(
            "whatsapp_number",
            number,
        )
        .order(
            "created_at",
            desc=True,
        )
        .limit(1)
        .execute()
    )

    existing = (
        response.data[0]
        if response.data
        else None
    )

    if existing:

        status = str(
            existing.get(
                "status",
                "waiting",
            )
        ).lower()

        if status == "waiting":

            return {
                "success": False,
                "status": "waiting",
                "message": (
                    "Your request is already "
                    "waiting for admin review."
                ),
                "request": existing,
            }

        if status == "approved":

            return {
                "success": False,
                "status": "approved",
                "message": (
                    "Your access request has "
                    "already been approved. "
                    "Please contact the administrator "
                    "on WhatsApp."
                ),
                "request": existing,
            }

        # Rejected requests can submit again.

    # -----------------------------------------------------
    # Insert request
    # -----------------------------------------------------

    response = (
        client.table("access_requests")
        .insert(
            {
                "whatsapp_number": number,
                "status": "waiting",
            }
        )
        .execute()
    )

    request_record = (
        response.data[0]
        if response.data
        else None
    )

    return {
        "success": True,
        "status": "waiting",
        "message": (
            "Request submitted successfully. "
            "The administrator will contact you "
            "on WhatsApp."
        ),
        "request": request_record,
    }


def get_access_request(
    whatsapp_number: str,
):

    client = get_supabase()

    number = str(
        whatsapp_number
    ).strip()

    if not number:
        return None

    response = (
        client.table("access_requests")
        .select("*")
        .eq(
            "whatsapp_number",
            number,
        )
        .order(
            "created_at",
            desc=True,
        )
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def list_access_requests(
    status: str | None = None,
):

    client = get_supabase()

    query = (
        client.table("access_requests")
        .select("*")
        .order(
            "created_at",
            desc=True,
        )
    )

    if status:

        query = query.eq(
            "status",
            str(status).strip().lower(),
        )

    response = query.execute()

    return response.data or []


def update_access_request_status(
    request_id: str,
    status: str,
    reviewed_by: str = "",
):

    clean_status = str(
        status
    ).strip().lower()

    if clean_status not in {
        "waiting",
        "approved",
        "rejected",
    }:

        raise ValueError(
            "Invalid access request status."
        )

    client = get_supabase()

    values = {
        "status": clean_status,
    }

    if clean_status in {
        "approved",
        "rejected",
    }:

        values["reviewed_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        values["reviewed_by"] = str(
            reviewed_by
        ).strip()

    else:

        values["reviewed_at"] = None
        values["reviewed_by"] = None

    return (
        client.table("access_requests")
        .update(values)
        .eq(
            "id",
            str(request_id),
        )
        .execute()
    )


# =========================================================
# AUDIT RETENTION
# =========================================================

def delete_old_audit_logs():

    client = get_supabase()

    cutoff = (
        datetime.now(
            timezone.utc
        )
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
