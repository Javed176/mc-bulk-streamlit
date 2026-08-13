from __future__ import annotations

import pandas as pd
import streamlit as st

from src.database import (
    delete_old_audit_logs,
    get_audit_logs,
    insert_audit,
)


# =========================================================
# WRITE AUDIT EVENT
# =========================================================

def log_action(
    action: str,
    mc_number: str = "",
    details: str = "",
):

    username = st.session_state.get(
        "username",
        "",
    )

    if not username:
        return

    try:

        insert_audit(
            username=username,
            action=action,
            mc_number=str(mc_number),
            details=details,
        )

    except Exception:
        pass


# =========================================================
# CLEAN OLD RECORDS
# =========================================================

def cleanup_audit_logs():

    try:
        delete_old_audit_logs()
    except Exception:
        pass


# =========================================================
# GET AUDIT DATAFRAME
# =========================================================

def audit_dataframe(
    username=None,
    action=None,
    start_date=None,
    end_date=None,
):

    rows = get_audit_logs(
        username=username,
        action=action,
        start_date=start_date,
        end_date=end_date,
    )

    if not rows:

        return pd.DataFrame(
            columns=[
                "Date/Time",
                "Username",
                "Action",
                "MC Number",
                "Details",
            ]
        )

    df = pd.DataFrame(rows)

    rename_map = {
        "created_at": "Date/Time",
        "username": "Username",
        "action": "Action",
        "mc_number": "MC Number",
        "details": "Details",
    }

    df = df.rename(
        columns=rename_map
    )

    wanted = [
        "Date/Time",
        "Username",
        "Action",
        "MC Number",
        "Details",
    ]

    for column in wanted:

        if column not in df.columns:
            df[column] = ""

    return df[wanted]
