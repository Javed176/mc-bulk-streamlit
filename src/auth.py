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
# SECRET READER
# =========================================================

def get_secret(
    name: str,
    nested_name: str = "",
) -> str:

    try:

        # ---------------------------------------------
        # Top-level secret
        # ---------------------------------------------

        value = st.secrets.get(
            name,
            "",
        )

        if value:

            return str(value).strip()

        # ---------------------------------------------
        # Optional [auth] section
        # ---------------------------------------------

        if "auth" in st.secrets:

            auth_section = st.secrets["auth"]

            if nested_name:

                value = auth_section.get(
                    nested_name,
                    "",
                )

                if value:

                    return str(value).strip()

    except Exception:

        pass

    return ""


# =========================================================
# ADMIN USERNAME
# =========================================================

def get_admin_username() -> str:

    return get_secret(
        "ADMIN_USERNAME",
        "username",
    )


# =========================================================
# PASSWORD HASH
# =========================================================

def hash_password(
    password: str,
) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# PASSWORD HASH FROM SECRETS
# =========================================================

def get_password_hash() -> str:

    return get_secret(
        "ADMIN_PASSWORD_HASH",
        "password_hash",
    )


# =========================================================
# OPTIONAL PLAIN PASSWORD
#
# Useful for initial setup.
# Hash is preferred for production.
# =========================================================

def get_plain_password() -> str:

    return get_secret(
        "ADMIN_PASSWORD",
        "password",
    )


# =========================================================
# CHECK USERNAME
# =========================================================

def check_username(
    username: str,
) -> bool:

    expected = get_admin_username()

    if not expected:

        return False

    return hmac.compare_digest(
        username.strip(),
        expected,
    )


# =========================================================
# CHECK PASSWORD
# =========================================================

def check_password(
    password: str,
) -> bool:

    stored_hash = get_password_hash()

    # ---------------------------------------------
    # Preferred method
    # ---------------------------------------------

    if stored_hash:

        supplied_hash = hash_password(
            password
        )

        return hmac.compare_digest(
            supplied_hash,
            stored_hash,
        )

    # ---------------------------------------------
    # Temporary plain password compatibility
    # ---------------------------------------------

    plain_password = get_plain_password()

    if plain_password:

        return hmac.compare_digest(
            password,
            plain_password,
        )

    return False


# =========================================================
# CHECK BOTH CREDENTIALS
# =========================================================

def check_credentials(
    username: str,
    password: str,
) -> bool:

    username_valid = check_username(
        username
    )

    password_valid = check_password(
        password
    )

    return (
        username_valid
        and password_valid
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

    locked_until = float(
        st.session_state.get(
            "login_locked_until",
            0,
        )
    )

    remaining = (
        locked_until
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

    # ---------------------------------------------
    # Already locked
    # ---------------------------------------------

    if is_locked():

        return False

    # ---------------------------------------------
    # Correct credentials
    # ---------------------------------------------

    if check_credentials(
        username,
        password,
    ):

        st.session_state.authenticated = True

        st.session_state.login_attempts = 0

        st.session_state.login_locked_until = 0.0

        # Random session token
        st.session_state.session_token = (
            secrets.token_urlsafe(32)
        )

        return True

    # ---------------------------------------------
    # Failed login
    # ---------------------------------------------

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
# AUTHENTICATION CHECK
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

    # =====================================================
    # ALREADY LOGGED IN
    # =====================================================

    if is_authenticated():

        return True

    # =====================================================
    # PAGE CSS
    # =====================================================

    st.markdown(
        """
<style>

.login-wrapper {
    width: 100%;
    max-width: 520px;
    margin: 7vh auto 0 auto;
}

.login-card {
    padding: 38px 35px 34px 35px;
    border-radius: 28px;

    background:
        linear-gradient(
            135deg,
            rgba(38,45,65,0.98),
            rgba(23,28,42,0.98)
        );

    border:
        1px solid
        rgba(255,255,255,0.15);

    box-shadow:
        0 30px 90px
        rgba(0,0,0,0.55),

        inset 0 1px 0
        rgba(255,255,255,0.08);

    text-align: center;
}

.login-lock {
    font-size: 3.6rem;
    line-height: 1;
    margin-bottom: 15px;

    filter:
        drop-shadow(
            0 0 20px
            rgba(100,130,255,0.55)
        );
}

.login-title {
    font-size: 2.15rem;
    font-weight: 800;

    color: #cbd5ff;

    letter-spacing: -0.5px;
}

.login-subtitle {
    margin-top: 9px;

    color: #9da6c0;

    font-size: 0.95rem;
}

.login-footer {
    text-align: center;

    margin-top: 22px;

    color: #68718a;

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

    # =====================================================
    # LOCKOUT
    # =====================================================

    if is_locked():

        st.error(
            "🔒 Too many failed login attempts."
        )

        st.warning(
            "Try again in "
            f"{seconds_remaining()} seconds."
        )

        st.stop()

    # =====================================================
    # USERNAME
    # =====================================================

    username = st.text_input(
        "Username",
        placeholder="Enter administrator username",
        key="login_username",
    )

    # =====================================================
    # PASSWORD
    # =====================================================

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter administrator password",
        key="login_password",
    )

    # =====================================================
    # SIGN IN
    # =====================================================

    login_button = st.button(
        "🔐 Sign In",
        type="primary",
        use_container_width=True,
    )

    if login_button:

        # ---------------------------------------------
        # Authenticate
        # ---------------------------------------------

        if login_user(
            username,
            password,
        ):

            # IMPORTANT:
            #
            # DO NOT modify:
            #
            # st.session_state.login_username
            # st.session_state.login_password
            #
            # after their widgets have been created.
            #
            # That causes the StreamlitAPIException
            # you were getting.

            st.rerun()

        # ---------------------------------------------
        # Failed login
        # ---------------------------------------------

        else:

            if is_locked():

                st.error(
                    "🔒 Too many failed attempts."
                )

                st.warning(
                    "Login locked for "
                    f"{LOCKOUT_SECONDS // 60} minutes."
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
                        f"{remaining} "
                        "attempt(s) remaining."
                    )

    # =====================================================
    # FOOTER
    # =====================================================

    st.markdown(
        """
<div class="login-footer">
    🔐 Protected MC Search system
</div>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # STOP APP HERE
    # =====================================================

    st.stop()
