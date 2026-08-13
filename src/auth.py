from __future__ import annotations

import hashlib
import hmac
import secrets
import time

import streamlit as st


# =========================================================
# SECURITY SETTINGS
# =========================================================

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


# =========================================================
# SESSION STATE
# =========================================================

def init_auth_state():

    defaults = {
        "authenticated": False,
        "login_attempts": 0,
        "login_locked_until": 0.0,
        "session_token": "",
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
# GET STORED PASSWORD HASH
# =========================================================

def get_password_hash() -> str:

    try:

        value = st.secrets.get(
            "ADMIN_PASSWORD_HASH",
            "",
        )

    except Exception:

        value = ""

    return str(value).strip()


# =========================================================
# CHECK PASSWORD
# =========================================================

def check_password(password: str) -> bool:

    stored_hash = get_password_hash()

    if not stored_hash:

        return False

    supplied_hash = hash_password(
        password
    )

    return hmac.compare_digest(
        supplied_hash,
        stored_hash,
    )


# =========================================================
# LOCKOUT
# =========================================================

def is_locked() -> bool:

    locked_until = float(
        st.session_state.get(
            "login_locked_until",
            0,
        )
    )

    return time.time() < locked_until


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

def login_user(password: str) -> bool:

    init_auth_state()

    if is_locked():

        return False

    if check_password(password):

        st.session_state.authenticated = True

        st.session_state.login_attempts = 0

        st.session_state.login_locked_until = 0

        st.session_state.session_token = (
            secrets.token_urlsafe(32)
        )

        return True

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

    return False


# =========================================================
# LOGOUT
# =========================================================

def logout_user():

    st.session_state.authenticated = False

    st.session_state.session_token = ""

    st.session_state.login_attempts = 0


# =========================================================
# AUTH CHECK
# =========================================================

def is_authenticated() -> bool:

    init_auth_state()

    return bool(
        st.session_state.authenticated
        and st.session_state.session_token
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

        .login-card {
            max-width: 480px;
            margin: 10vh auto 0 auto;
            padding: 42px;
            border-radius: 30px;

            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,0.11),
                    rgba(255,255,255,0.035)
                );

            border:
                1px solid
                rgba(255,255,255,0.14);

            box-shadow:
                0 30px 100px
                rgba(0,0,0,0.55),

                inset 0 1px 0
                rgba(255,255,255,0.08);

            backdrop-filter:
                blur(30px);

        }

        .login-title {
            font-size: 2.3rem;
            font-weight: 800;
            color: white;
            text-align: center;
        }

        .login-subtitle {
            text-align: center;
            color: #9da6c0;
            margin-bottom: 30px;
        }

        </style>

        <div class="login-card">

            <div class="login-title">
                ✦ MC Search
            </div>

            <div class="login-subtitle">
                Secure access required
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

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
    )

    login_button = st.button(
        "🔐 Sign In",
        type="primary",
        use_container_width=True,
    )

    if login_button:

        if login_user(password):

            st.success(
                "Authenticated."
            )

            time.sleep_short = 0

            st.rerun()

        else:

            remaining_attempts = (
                MAX_LOGIN_ATTEMPTS
                - st.session_state.login_attempts
            )

            if remaining_attempts > 0:

                st.error(
                    "Incorrect password."
                )

                st.caption(
                    f"{remaining_attempts} "
                    "attempt(s) remaining."
                )

            else:

                st.error(
                    "Too many failed attempts. "
                    "Login temporarily locked."
                )

    st.stop()
