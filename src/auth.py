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
# STORED PASSWORD
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

    supplied_hash = hash_password(password)

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

    return max(0, int(remaining))


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

        # Fresh random session token
        st.session_state.session_token = (
            secrets.token_urlsafe(32)
        )

        return True

    # Failed attempt
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
# LOGIN PAGE
# =========================================================

def require_login():

    init_auth_state()

    # Already authenticated
    if is_authenticated():
        return True

    # -----------------------------------------------------
    # LOGIN CSS
    # -----------------------------------------------------

    st.markdown(
        """
        <style>

        /* =================================================
           LOGIN BACKGROUND
           ================================================= */

        .stApp {
            background:
                radial-gradient(
                    circle at 20% 20%,
                    rgba(82, 107, 255, 0.18),
                    transparent 32%
                ),
                radial-gradient(
                    circle at 80% 25%,
                    rgba(181, 70, 255, 0.16),
                    transparent 32%
                ),
                radial-gradient(
                    circle at 50% 90%,
                    rgba(0, 190, 255, 0.08),
                    transparent 35%
                ),
                linear-gradient(
                    135deg,
                    #05060a 0%,
                    #0b0d15 50%,
                    #05060a 100%
                );
        }


        /* =================================================
           LOGIN CARD
           ================================================= */

        .login-card {
            max-width: 480px;

            margin:
                10vh auto 0 auto;

            padding:
                42px 42px 36px 42px;

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
                rgba(255,255,255,0.14);

            box-shadow:
                0 30px 100px
                rgba(0,0,0,0.55),

                0 0 70px
                rgba(91,95,255,0.08),

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


        /* =================================================
           LOCK ICON
           ================================================= */

        .login-lock {
            width:
                76px;

            height:
                76px;

            margin:
                0 auto 22px auto;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            border-radius:
                24px;

            font-size:
                34px;

            background:
                linear-gradient(
                    135deg,
                    rgba(110,130,255,0.25),
                    rgba(180,80,255,0.20)
                );

            border:
                1px solid
                rgba(150,160,255,0.25);

            box-shadow:
                0 0 35px
                rgba(100,110,255,0.18),

                inset 0 1px 0
                rgba(255,255,255,0.12);

            animation:
                lockPulse 2.4s
                ease-in-out
                infinite;
        }


        @keyframes lockPulse {

            0%,
            100% {
                box-shadow:
                    0 0 25px
                    rgba(100,110,255,0.12),

                    inset 0 1px 0
                    rgba(255,255,255,0.12);
            }

            50% {
                box-shadow:
                    0 0 45px
                    rgba(100,110,255,0.28),

                    0 0 80px
                    rgba(160,70,255,0.10),

                    inset 0 1px 0
                    rgba(255,255,255,0.16);
            }
        }


        /* =================================================
           TITLE
           ================================================= */

        .login-title {
            font-size:
                2.35rem;

            font-weight:
                800;

            letter-spacing:
                -0.045em;

            background:
                linear-gradient(
                    90deg,
                    #ffffff,
                    #c1caff,
                    #ffffff
                );

            -webkit-background-clip:
                text;

            -webkit-text-fill-color:
                transparent;
        }


        /* =================================================
           SUBTITLE
           ================================================= */

        .login-subtitle {
            color:
                rgba(220,225,245,0.62);

            font-size:
                0.98rem;

            margin-top:
                8px;

            margin-bottom:
                28px;
        }


        /* =================================================
           LOGIN INPUT
           ================================================= */

        div[data-baseweb="input"] {

            background:
                rgba(255,255,255,0.055)
                !important;

            border:
                1px solid
                rgba(255,255,255,0.12)
                !important;

            border-radius:
                18px
                !important;

            transition:
                all 0.25s ease;
        }


        div[data-baseweb="input"]:focus-within {

            border-color:
                rgba(120,145,255,0.85)
                !important;

            box-shadow:
                0 0 0 3px
                rgba(100,125,255,0.10),

                0 0 35px
                rgba(80,100,255,0.14);
        }


        input {

            color:
                white
                !important;

            font-size:
                1rem
                !important;
        }


        /* =================================================
           SIGN IN BUTTON
           ================================================= */

        .stButton > button {

            min-height:
                52px;

            border-radius:
                18px
                !important;

            border:
                1px solid
                rgba(130,145,255,0.25)
                !important;

            background:
                linear-gradient(
                    135deg,
                    rgba(95,120,255,0.30),
                    rgba(150,75,255,0.25)
                )
                !important;

            color:
                white
                !important;

            font-weight:
                700
                !important;

            box-shadow:
                0 12px 35px
                rgba(70,80,220,0.18),

                inset 0 1px 0
                rgba(255,255,255,0.12);

            transition:
                all 0.22s ease;
        }


        .stButton > button:hover {

            transform:
                translateY(-2px)
                scale(1.01);

            box-shadow:
                0 16px 45px
                rgba(80,95,255,0.30),

                0 0 30px
                rgba(130,70,255,0.14),

                inset 0 1px 0
                rgba(255,255,255,0.15);
        }


        .stButton > button:active {

            transform:
                scale(0.97);
        }


        /* =================================================
           SECURITY FOOTER
           ================================================= */

        .login-security {

            margin-top:
                24px;

            color:
                rgba(180,188,215,0.45);

            font-size:
                0.78rem;
        }


        </style>
        """,
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------
    # LOGIN CARD
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # LOCKOUT
    # -----------------------------------------------------

    if is_locked():

        st.error(
            "🔒 Too many failed login attempts."
        )

        st.warning(
            f"Try again in "
            f"{seconds_remaining()} seconds."
        )

        st.stop()


    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="login_password",
    )


    # -----------------------------------------------------
    # SIGN IN
    # -----------------------------------------------------

    login_button = st.button(
        "🔐  Sign In",
        type="primary",
        use_container_width=True,
    )


    if login_button:

        if not password:

            st.warning(
                "Enter your password."
            )

        elif login_user(password):

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

                remaining_attempts = (
                    MAX_LOGIN_ATTEMPTS
                    - st.session_state.login_attempts
                )

                st.error(
                    "Incorrect password."
                )

                if remaining_attempts > 0:

                    st.caption(
                        f"{remaining_attempts} "
                        "attempt(s) remaining."
                    )


    st.markdown(
        """
        <div class="login-security">
            🔒 Protected session • Secure authentication
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()
