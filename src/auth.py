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
# STREAMLIT SECRETS
# =========================================================

def get_admin_username() -> str:

    try:
        return str(
            st.secrets.get(
                "ADMIN_USERNAME",
                "",
            )
        ).strip()

    except Exception:
        return ""


def get_admin_password_hash() -> str:

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
# PASSWORD HASH
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# VERIFY LOGIN
# =========================================================

def check_credentials(
    username: str,
    password: str,
) -> bool:

    stored_username = get_admin_username()
    stored_hash = get_admin_password_hash()

    if not stored_username:
        return False

    if not stored_hash:
        return False

    username_ok = hmac.compare_digest(
        username.strip(),
        stored_username,
    )

    password_hash = hash_password(
        password
    )

    password_ok = hmac.compare_digest(
        password_hash,
        stored_hash,
    )

    return (
        username_ok
        and password_ok
    )


# =========================================================
# LOCKOUT
# =========================================================

def is_locked() -> bool:

    locked_until = float(
        st.session_state.get(
            "login_locked_until",
            0.0,
        )
    )

    return time.time() < locked_until


def seconds_remaining() -> int:

    remaining = (
        float(
            st.session_state.get(
                "login_locked_until",
                0.0,
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

    # Already logged in
    if is_authenticated():
        return True

    # =====================================================
    # LOGIN PAGE CSS
    #
    # IMPORTANT:
    # There is NO HTML login content here.
    # This prevents <div>...</div> from appearing as text.
    # =====================================================

    st.markdown(
        """
        <style>

        /* Remove unnecessary top spacing */
        .block-container {
            padding-top: 5vh !important;
        }

        /* Login header area */
        .login-header {
            max-width: 560px;
            margin: 0 auto 25px auto;
            padding: 38px 30px 30px 30px;

            text-align: center;

            border-radius: 28px;

            background:
                linear-gradient(
                    145deg,
                    rgba(39,48,72,0.96),
                    rgba(18,23,36,0.96)
                );

            border:
                1px solid
                rgba(255,255,255,0.15);

            box-shadow:
                0 25px 80px
                rgba(0,0,0,0.50),

                inset 0 1px 0
                rgba(255,255,255,0.08);
        }

        .login-lock {
            font-size: 54px;
            line-height: 1;

            margin-bottom: 15px;

            filter:
                drop-shadow(
                    0 0 18px
                    rgba(100,140,255,0.75)
                );
        }

        .login-title {
            font-size: 2.2rem;
            font-weight: 800;

            color: #cbd5ff;

            letter-spacing: -0.5px;
        }

        .login-subtitle {
            margin-top: 8px;

            color: #9da6c0;

            font-size: 0.95rem;
        }

        .login-footer {
            text-align: center;

            margin-top: 24px;

            color: #69738e;

            font-size: 0.82rem;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # LOGIN HEADER
    #
    # NATIVE STREAMLIT ONLY
    # =====================================================

    st.markdown(
        '<div class="login-header">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="login-lock">🔐</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="login-title">✦ MC Search</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="login-subtitle">'
        'Secure administrator access'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '</div>',
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
    # LOGIN FORM
    # =====================================================

    with st.form(
        "admin_login_form",
        clear_on_submit=False,
    ):

        username = st.text_input(
            "Username",
            placeholder="Enter admin username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter admin password",
        )

        submitted = st.form_submit_button(
            "🔐  Sign In",
            type="primary",
            use_container_width=True,
        )

    # =====================================================
    # LOGIN PROCESSING
    # =====================================================

    if submitted:

        username = username.strip()

        if not username:

            st.error(
                "Please enter your username."
            )

        elif not password:

            st.error(
                "Please enter your password."
            )

        elif login_user(
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

    st.stop()
