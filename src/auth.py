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
# STORED PASSWORD HASH
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
# PASSWORD CHECK
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

def login_user(password: str) -> bool:

    init_auth_state()

    if is_locked():

        return False

    if check_password(password):

        st.session_state.authenticated = True

        st.session_state.login_attempts = 0

        st.session_state.login_locked_until = 0.0

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
# LOGIN UI
# =========================================================

def require_login():

    init_auth_state()

    # Already authenticated
    if is_authenticated():

        return True

    # =====================================================
    # LOGIN CSS
    # =====================================================

    st.markdown(
        """
        <style>

        .login-card {

            max-width: 520px;

            margin:
                10vh auto 25px auto;

            padding:
                45px 40px;

            border-radius:
                30px;

            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,0.12),
                    rgba(255,255,255,0.035)
                );

            border:
                1px solid
                rgba(255,255,255,0.15);

            box-shadow:
                0 30px 100px
                rgba(0,0,0,0.55),

                inset 0 1px 0
                rgba(255,255,255,0.10);

            backdrop-filter:
                blur(30px)
                saturate(160%);

            -webkit-backdrop-filter:
                blur(30px)
                saturate(160%);

            text-align:
                center;

        }


        .login-title {

            font-size:
                3rem;

            font-weight:
                800;

            letter-spacing:
                -0.05em;

            background:
                linear-gradient(
                    90deg,
                    #ffffff,
                    #aebcff,
                    #ffffff
                );

            -webkit-background-clip:
                text;

            -webkit-text-fill-color:
                transparent;

            margin-bottom:
                8px;

        }


        .login-subtitle {

            color:
                rgba(235,240,255,0.62);

            font-size:
                1rem;

            margin-bottom:
                5px;

        }


        .login-lock {

            width:
                70px;

            height:
                70px;

            margin:
                0 auto 22px auto;

            border-radius:
                22px;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            font-size:
                2rem;

            background:
                linear-gradient(
                    135deg,
                    rgba(100,130,255,0.25),
                    rgba(170,80,255,0.18)
                );

            border:
                1px solid
                rgba(140,160,255,0.25);

            box-shadow:
                0 0 35px
                rgba(100,120,255,0.18);

        }


        .stButton > button {

            transition:
                all 0.22s ease;

        }


        .stButton > button:hover {

            transform:
                translateY(-2px)
                scale(1.01);

            box-shadow:
                0 12px 35px
                rgba(80,110,255,0.28);

        }

        </style>
        """,
        unsafe_allow_html=True,
    )


    # =====================================================
    # LOGIN CARD
    # =====================================================

    st.markdown(
        """
        <div class="login-card">

            <div class="login-lock">
                🔐
            </div>

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


    # =====================================================
    # LOCKOUT
    # =====================================================

    if is_locked():

        st.error(
            "🔒 Too many failed login attempts."
        )

        st.warning(
            f"Try again in "
            f"{seconds_remaining()} seconds."
        )

        st.stop()


    # =====================================================
    # PASSWORD
    # =====================================================

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="auth_password",
    )


    # =====================================================
    # LOGIN BUTTON
    # =====================================================

    login_button = st.button(
        "🔐 Sign In",
        type="primary",
        use_container_width=True,
        key="login_button",
    )


    if login_button:

        if login_user(password):

            st.success(
                "✓ Authenticated."
            )

            # Remove password from session state
            st.session_state.pop(
                "auth_password",
                None,
            )

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
