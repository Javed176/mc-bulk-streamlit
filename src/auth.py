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
# SECRETS
# =========================================================

def get_admin_username() -> str:

    try:
        value = st.secrets.get(
            "ADMIN_USERNAME",
            "",
        )
    except Exception:
        value = ""

    return str(value).strip()


def get_admin_password_hash() -> str:

    try:
        value = st.secrets.get(
            "ADMIN_PASSWORD_HASH",
            "",
        )
    except Exception:
        value = ""

    return str(value).strip()


# =========================================================
# PASSWORD HASH
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# VERIFY CREDENTIALS
# =========================================================

def check_credentials(
    username: str,
    password: str,
) -> bool:

    stored_username = get_admin_username()
    stored_password_hash = get_admin_password_hash()

    if not stored_username:
        return False

    if not stored_password_hash:
        return False

    username_ok = hmac.compare_digest(
        username.strip(),
        stored_username,
    )

    supplied_hash = hash_password(
        password
    )

    password_ok = hmac.compare_digest(
        supplied_hash,
        stored_password_hash,
    )

    return username_ok and password_ok


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

def login_user(
    username: str,
    password: str,
) -> bool:

    init_auth_state()

    if is_locked():
        return False

    if check_credentials(
        username,
        password,
    ):

        st.session_state.authenticated = True

        st.session_state.login_attempts = 0

        st.session_state.login_locked_until = 0.0

        # Fresh random session token
        st.session_state.session_token = (
            secrets.token_urlsafe(32)
        )

        return True

    # Failed login
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

    st.session_state.login_locked_until = 0.0


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

    # Already authenticated
    if is_authenticated():
        return True

    # -----------------------------------------------------
    # LOGIN PAGE CSS
    # -----------------------------------------------------

    st.markdown(
        """
        <style>

        .login-wrapper {
            max-width: 560px;
            margin: 7vh auto 0 auto;
        }

        .login-card {
            padding: 42px 42px 34px 42px;
            border-radius: 28px;

            background:
                linear-gradient(
                    145deg,
                    rgba(35,42,62,0.96),
                    rgba(18,23,36,0.96)
                );

            border:
                1px solid
                rgba(255,255,255,0.16);

            box-shadow:
                0 30px 90px
                rgba(0,0,0,0.55),

                inset 0 1px 0
                rgba(255,255,255,0.08);

            text-align: center;
        }

        .login-lock {
            font-size: 58px;
            line-height: 1;
            margin-bottom: 18px;

            filter:
                drop-shadow(
                    0 0 18px
                    rgba(110,140,255,0.65)
                );
        }

        .login-title {
            font-size: 2.2rem;
            font-weight: 800;

            color: #c9d4ff;

            letter-spacing: -0.5px;
        }

        .login-subtitle {
            margin-top: 10px;

            color: #9da6c0;

            font-size: 0.98rem;
        }

        .login-footer {
            text-align: center;

            margin-top: 25px;

            color: #69738e;

            font-size: 0.82rem;
        }

        </style>

        <div class="login-wrapper">

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

    # -----------------------------------------------------
    # LOCKOUT
    # -----------------------------------------------------

    if is_locked():

        st.error(
            "🔒 Too many failed login attempts."
        )

        st.warning(
            "Try again in "
            f"{seconds_remaining()} seconds."
        )

        st.stop()

    # -----------------------------------------------------
    # LOGIN FORM
    # -----------------------------------------------------

    with st.form(
        "admin_login_form",
        clear_on_submit=False,
    ):

        username = st.text_input(
            "Username",
            placeholder="Enter admin username",
            autocomplete="username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter admin password",
            autocomplete="current-password",
        )

        submitted = st.form_submit_button(
            "🔐  Sign In",
            type="primary",
            use_container_width=True,
        )

    # -----------------------------------------------------
    # LOGIN ATTEMPT
    # -----------------------------------------------------

    if submitted:

        username = username.strip()

        if not username or not password:

            st.error(
                "Please enter both username and password."
            )

            st.stop()

        if login_user(
            username,
            password,
        ):

            st.success(
                "✓ Authentication successful."
            )

            time.sleep(0.25)

            st.rerun()

        else:

            if is_locked():

                st.error(
                    "🔒 Too many failed attempts. "
                    "Login temporarily locked."
                )

            else:

                remaining = (
                    MAX_LOGIN_ATTEMPTS
                    - st.session_state.login_attempts
                )

                st.error(
                    "Incorrect username or password."
                )

                if remaining > 0:

                    st.caption(
                        f"{remaining} attempt(s) remaining."
                    )

    st.markdown(
        """
        <div class="login-footer">
            🔐 Protected MC Search system
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()
