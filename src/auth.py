from __future__ import annotations

import streamlit as st
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from src.database import (
    create_user_record,
    get_user,
)


# =========================================================
# PASSWORD HASHER
# =========================================================

password_hasher = PasswordHasher()


# =========================================================
# SESSION STATE
# =========================================================

def initialize_auth():

    defaults = {
        "authenticated": False,
        "username": None,
        "role": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# HASH PASSWORD
# =========================================================

def hash_password(
    password: str,
) -> str:

    return password_hasher.hash(
        password
    )


# =========================================================
# VERIFY PASSWORD
# =========================================================

def verify_password(
    password_hash: str,
    password: str,
) -> bool:

    try:

        return password_hasher.verify(
            password_hash,
            password,
        )

    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError,
    ):

        return False


# =========================================================
# LOGIN
# =========================================================

def login(
    username: str,
    password: str,
) -> bool:

    username = username.strip()

    if not username or not password:
        return False

    user = get_user(username)

    if not user:
        return False

    if not user.get("active", False):
        return False

    stored_hash = user.get(
        "password_hash",
        "",
    )

    if not verify_password(
        stored_hash,
        password,
    ):
        return False

    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.role = user.get(
        "role",
        "standard_user",
    )

    return True


# =========================================================
# LOGOUT
# =========================================================

def logout():

    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None

    # Clear search state too.
    for key in (
        "running",
        "current_mc",
        "results",
        "start_mc",
        "searched_count",
    ):

        if key in st.session_state:

            if key == "results":
                st.session_state[key] = []

            elif key == "searched_count":
                st.session_state[key] = 0

            else:
                st.session_state[key] = (
                    None
                    if key == "current_mc"
                    else ""
                )


# =========================================================
# ROLE CHECKS
# =========================================================

def is_authenticated() -> bool:

    return bool(
        st.session_state.get(
            "authenticated",
            False,
        )
    )


def is_admin() -> bool:

    return st.session_state.get(
        "role"
    ) in (
        "master_admin",
        "super_admin",
    )


def is_super_admin() -> bool:

    return (
        st.session_state.get(
            "role"
        )
        == "super_admin"
    )


# =========================================================
# BOOTSTRAP ADMIN
# =========================================================

def ensure_bootstrap_admin():

    try:

        username = str(
            st.secrets.get(
                "ADMIN_USERNAME",
                "",
            )
        ).strip()

        password = str(
            st.secrets.get(
                "ADMIN_PASSWORD",
                "",
            )
        )

        if not username or not password:
            return

        existing = get_user(username)

        if existing:
            return

        password_hash = hash_password(
            password
        )

        create_user_record(
            username=username,
            password_hash=password_hash,
            role="super_admin",
        )

    except Exception:
        # Do not break the application if
        # the optional bootstrap credentials
        # haven't been configured yet.
        pass
