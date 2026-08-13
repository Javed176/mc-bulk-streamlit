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
# GET ADMIN USERNAME
# =========================================================

def get_admin_username() -> str:

    try:
        username = st.secrets.get(
            "ADMIN_USERNAME",
            "",
        )
    except Exception:
        username = ""

    return str(username).strip()


# =========================================================
# GET PASSWORD HASH
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
# CHECK CREDENTIALS
# =========================================================

def check_credentials(
    username: str,
    password: str,
) -> bool:

    stored_username = get_admin_username()
    stored_password_hash = get_password_hash()

    if not stored_username:
        return False

    if not stored_password_hash:
        return False

    username_ok = hmac.compare_digest(
        str(username).strip(),
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

        # Generate a fresh random session token.
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

    # =====================================================
    # LOGIN CSS
    # =====================================================

    st.markdown(
        """
        <style>

        .login-wrapper {
            max-width: 560px;
            margin: 8vh auto 0 auto;
        }

        .login-card {
            padding: 42px 42px 34px 42px;

            border-radius: 30px;

            background:
                linear-gradient(
                    135deg,
                    rgba(35,42,61,0.96),
                    rgba(18,23,35,0.96)
                );

            border:
                1px solid
                rgba(255,255,255,0.16);

            box-shadow:
                0 30px 100px
                rgba(0,0,0,0.55),

                inset 0 1px 0
                rgba(255,255,255,0.08);

            backdrop-filter:
                blur(30px);

            text-align: center;
        }

        .login-lock {
            font-size: 4.5rem;
            line-height: 1;
            margin-bottom: 18px;

            filter:
                drop-shadow(
                    0 0 22px
                    rgba(100,130,255,0.65)
                );

            animation:
                loginGlow 2.5s
                ease-in-out
                infinite alternate;
        }

        @keyframes loginGlow {

            from {
                transform: scale(1);
                filter:
                    drop-shadow(
                        0 0 12px
                        rgba(100,130,255,0.45)
                    );
            }

            to {
                transform: scale(1.06);
                filter:
                    drop-shadow(
                        0 0 30px
                        rgba(130,100,255,0.8)
                    );
            }
        }

        .login-title {
            font-size: 2.4rem;
            font-weight: 850;

            color: #c5d0ff;

            letter-spacing: -0.8px;

            margin-bottom: 8px;
        }

        .login-subtitle {
            color: #9da6c0;
            font-size: 1rem;
            margin-bottom: 4px;
        }

        .login-security {
            margin-top: 18px;

            color: #68728f;

            font-size: 0.82rem;
        }

        div[data-testid="stTextInput"] {
            margin-top: 18px;
        }

        div[data-testid="stTextInput"] input {
            border-radius: 12px !important;
            background: #242732 !important;
            border: 1px solid #3b4050 !important;
        }

        div[data-testid="stButton"] > button {
            border-radius: 13px !important;

            min-height: 48px;

            font-weight: 750;

            background:
                linear-gradient(
                    135deg,
                    #273b9f,
                    #452071
                ) !important;

            border:
                1px solid
                rgba(130,140,255,0.45) !important;

            box-shadow:
                0 8px 30px
                rgba(70,80,220,0.25);

            transition:
                all 0.2s ease;
        }

        div[data-testid="stButton"] > button:hover {

            transform:
                translateY(-2px);

            box-shadow:
                0 12px 40px
                rgba(90,100,255,0.4);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # LOCKOUT CHECK
    # =====================================================

    if is_locked():

        st.markdown(
            """
            <div class="login-wrapper">
                <div class="login-card">
                    <div class="login-lock">🔒</div>

                    <div class="login-title">
                        MC Search
                    </div>

                    <div class="login-subtitle">
                        Access temporarily locked
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.error(
            "Too many failed login attempts."
        )

        st.warning(
            f"Try again in "
            f"{seconds_remaining()} seconds."
        )

        st.stop()

    # =====================================================
    # LOGIN HEADER
    # =====================================================

    st.markdown(
        """
        <div class="login-wrapper">

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

        </div>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # USERNAME
    # =====================================================

    username = st.text_input(
        "Username",
        placeholder="Enter your username",
        autocomplete="username",
    )

    # =====================================================
    # PASSWORD
    # =====================================================

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        autocomplete="current-password",
    )

    # =====================================================
    # SIGN IN
    # =====================================================

    login_button = st.button(
        "🔐  Sign In",
        type="primary",
        use_container_width=True,
    )

    if login_button:

        if login_user(
            username,
            password,
        ):

            st.success(
                "Authenticated successfully."
            )

            st.rerun()

        else:

            if is_locked():

                st.error(
                    "Too many failed attempts. "
                    "Login temporarily locked."
                )

            else:

                remaining_attempts = (
                    MAX_LOGIN_ATTEMPTS
                    - st.session_state.login_attempts
                )

                st.error(
                    "Incorrect username or password."
                )

                if remaining_attempts > 0:

                    st.caption(
                        f"{remaining_attempts} "
                        "attempt(s) remaining."
                    )

    # =====================================================
    # FOOTER
    # =====================================================

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:38px;
            color:#68728f;
            font-size:0.82rem;
        ">
            🔐 Protected MC Search system
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()
