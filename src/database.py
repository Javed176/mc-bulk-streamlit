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
    role: str,
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
            "id,username,role,active,created_at"
        )
        .order("created_at", desc=False)
        .execute()
    )

    return response.data or []


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
# 90-DAY RETENTION
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
