from __future__ import annotations

import hashlib
import hmac
import secrets
import time

import streamlit as st

from src.database import get_user


# =========================================================
# SECURITY
# =========================================================

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


# =========================================================
# SESSION STATE
# =========================================================

def init_auth_state():

    defaults = {
        "authenticated": False,
        "username": "",
        "role": "",
        "session_token": "",
        "login_attempts": 0,
        "login_locked_until": 0.0,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# PASSWORD HASH
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# SECRET ADMIN
# =========================================================

def get_secret_admin_username() -> str:

    try:
        return str(
            st.secrets.get(
                "ADMIN_USERNAME",
                "",
            )
        ).strip()
    except Exception:
        return ""


def get_secret_admin_hash() -> str:

    try:
        return str(
            st.secrets.get(
                "ADMIN_PASSWORD_HASH",
                "",
            )
        ).strip()
    except Exception:
        return ""


# =========================================================
# PASSWORD CHECK
# =========================================================

def check_password(
    username: str,
    password: str,
) -> tuple[bool, str]:

    username = username.strip()

    # -----------------------------------------------------
    # First: Supabase user
    # -----------------------------------------------------

    try:

        user = get_user(username)

    except Exception:

        user = None

    if user:

        if not bool(
            user.get(
                "active",
                True,
            )
        ):

            return False, "inactive"

        stored_hash = str(
            user.get(
                "password_hash",
                "",
            )
        ).strip()

        supplied_hash = hash_password(
            password
        )

        if (
            stored_hash
            and hmac.compare_digest(
                supplied_hash,
                stored_hash,
            )
        ):

            return True, str(
                user.get(
                    "role",
                    "user",
                )
            )

        return False, "invalid"

    # -----------------------------------------------------
    # Fallback bootstrap administrator
    # -----------------------------------------------------

    secret_username = (
        get_secret_admin_username()
    )

    secret_hash = (
        get_secret_admin_hash()
    )

    if (
        secret_username
        and secret_hash
        and hmac.compare_digest(
            username,
            secret_username,
        )
        and hmac.compare_digest(
            hash_password(password),
            secret_hash,
        )
    ):

        return True, "admin"

    return False, "invalid"


# =========================================================
# LOCKOUT
# =========================================================

def is_locked() -> bool:

    return time.time() < float(
        st.session_state.get(
            "login_locked_until",
            0,
        )
    )


def seconds_remaining() -> int:

    remaining = (
        float(
            st.session_state.get(
                "login_locked_until",
                0,
            )
        )
        - time.time()
    )

    return max(
        0,
        int(remaining),
    )


# =========================================================
# LOGIN
# =========================================================

def login_user(
    username: str,
    password: str,
) -> tuple[bool, str]:

    init_auth_state()

    if is_locked():
        return False, "locked"

    success, role = check_password(
        username,
        password,
    )

    if success:

        st.session_state.authenticated = True

        st.session_state.username = (
            username.strip()
        )

        st.session_state.role = role

        st.session_state.session_token = (
            secrets.token_urlsafe(32)
        )

        st.session_state.login_attempts = 0

        st.session_state.login_locked_until = 0

        return True, role

    st.session_state.login_attempts += 1

    if (
        st.session_state.login_attempts
        >= MAX_LOGIN_ATTEMPTS
    ):

        st.session_state.login_locked_until = (
            time.time()
            + LOCKOUT_SECONDS
        )

        st.session_state.login_attempts = 0

        return False, "locked"

    return False, "invalid"


# =========================================================
# LOGOUT
# =========================================================

def logout_user():

    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.session_token = ""

    st.session_state.login_attempts = 0
    st.session_state.login_locked_until = 0


# =========================================================
# AUTH CHECK
# =========================================================

def is_authenticated() -> bool:

    init_auth_state()

    return bool(
        st.session_state.authenticated
        and st.session_state.session_token
        and st.session_state.username
    )


def is_admin() -> bool:

    return bool(
        is_authenticated()
        and st.session_state.get(
            "role",
            "",
        ).lower()
        == "admin"
    )


# =========================================================
# LOGIN SCREEN
# =========================================================

def require_login():

    init_auth_state()

    if is_authenticated():
        return True

    st.markdown(
        """
<style>

.login-wrap {
    min-height: 70vh;
    display:flex;
    align-items:center;
    justify-content:center;
}

.login-card {
    width:100%;
    max-width:500px;
    padding:42px;
    border-radius:30px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.11),
            rgba(255,255,255,.035)
        );

    border:
        1px solid rgba(255,255,255,.14);

    box-shadow:
        0 30px 100px rgba(0,0,0,.55),
        inset 0 1px 0 rgba(255,255,255,.08);

    backdrop-filter:blur(30px);
}

.login-lock {
    text-align:center;
    font-size:3rem;
    margin-bottom:10px;

    filter:
        drop-shadow(
            0 0 20px
            rgba(120,140,255,.7)
        );
}

.login-title {
    font-size:2.4rem;
    font-weight:800;
    text-align:center;
    color:white;
}

.login-subtitle {
    text-align:center;
    color:#9da6c0;
    margin-top:8px;
    margin-bottom:28px;
}

</style>

<div class="login-wrap">

<div class="login-card">

    <div class="login-lock">
        🔐
    </div>

    <div class="login-title">
        ✦ MC Search
    </div>

    <div class="login-subtitle">
        Secure administrator access
    </div>

</div>

</div>
""",
        unsafe_allow_html=True,
    )

    if is_locked():

        st.error(
            "Too many failed login attempts."
        )

        st.warning(
            f"Try again in "
            f"{seconds_remaining()} seconds."
        )

        st.stop()

    username = st.text_input(
        "Username",
        placeholder="Enter username",
        key="auth_username_input",
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter password",
        key="auth_password_input",
    )

    login_button = st.button(
        "🔐 Sign In",
        type="primary",
        use_container_width=True,
    )

    if login_button:

        success, status = login_user(
            username,
            password,
        )

        if success:

            st.success(
                "✓ Authentication successful."
            )

            st.rerun()

        elif status == "locked":

            st.error(
                "Too many failed attempts. "
                "Login temporarily locked."
            )

        else:

            remaining = (
                MAX_LOGIN_ATTEMPTS
                - st.session_state.login_attempts
            )

            st.error(
                "Invalid username or password."
            )

            if remaining > 0:

                st.caption(
                    f"{remaining} attempt(s) remaining."
                )

    st.stop()
