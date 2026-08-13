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
        "login_username": "",
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
        password_hash = st.secrets.get(
            "ADMIN_PASSWORD_HASH",
            "",
        )
    except Exception:
        password_hash = ""

    return str(password_hash).strip()


# =========================================================
# CHECK CREDENTIALS
# =========================================================

def check_credentials(
    username: str,
    password: str,
) -> bool:

    stored_username = get_admin_username()
    stored_hash = get_password_hash()

    if not stored_username or not stored_hash:
        return False

    username_ok = hmac.compare_digest(
        username.strip(),
        stored_username,
    )

    supplied_hash = hash_password(password)

    password_ok = hmac.compare_digest(
        supplied_hash,
        stored_hash,
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

    locked_until = float(
        st.session_state.get(
            "login_locked_until",
            0.0,
        )
    )

    remaining = locked_until - time.time()

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

        st.session_state.login_username = (
            username.strip()
        )

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

    st.session_state.login_username = ""

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
# LOGIN PAGE CSS
# =========================================================

def render_login_styles():

    st.markdown(
        """
<style>

.login-page {
    min-height: 70vh;

    display: flex;

    align-items: center;

    justify-content: center;

    padding-top: 6vh;
}


.login-card {
    width: min(480px, 92vw);

    margin: 0 auto;

    padding: 42px 40px;

    border-radius: 30px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,0.12),
            rgba(255,255,255,0.035)
        );

    border:
        1px solid rgba(255,255,255,0.14);

    box-shadow:
        0 30px 100px rgba(0,0,0,0.55),
        inset 0 1px 0 rgba(255,255,255,0.09);

    backdrop-filter:
        blur(30px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(30px)
        saturate(160%);

    text-align: center;

    animation:
        loginCardIn 0.55s ease-out;
}


@keyframes loginCardIn {

    from {
        opacity: 0;
        transform:
            translateY(18px)
            scale(0.97);
    }

    to {
        opacity: 1;
        transform:
            translateY(0)
            scale(1);
    }
}


.login-lock {
    width: 76px;

    height: 76px;

    margin: 0 auto 20px auto;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 24px;

    font-size: 2.1rem;

    background:
        radial-gradient(
            circle at 30% 20%,
            rgba(130,150,255,0.35),
            rgba(100,60,255,0.12)
        );

    border:
        1px solid rgba(130,150,255,0.28);

    box-shadow:
        0 0 35px rgba(100,110,255,0.20),
        inset 0 1px 0 rgba(255,255,255,0.10);

    animation:
        lockPulse 2.5s ease-in-out infinite;
}


@keyframes lockPulse {

    0%,
    100% {
        box-shadow:
            0 0 25px rgba(100,110,255,0.15),
            inset 0 1px 0 rgba(255,255,255,0.10);
    }

    50% {
        box-shadow:
            0 0 45px rgba(110,120,255,0.30),
            inset 0 1px 0 rgba(255,255,255,0.14);
    }
}


.login-title {

    font-size: 2.4rem;

    font-weight: 850;

    letter-spacing: -0.045em;

    color: #ffffff;

    text-shadow:
        0 0 30px rgba(150,160,255,0.15);
}


.login-subtitle {

    margin-top: 8px;

    margin-bottom: 28px;

    color: #9da6c0;

    font-size: 0.95rem;
}


/* Login inputs */

.login-input-label {

    text-align: left;

    margin:
        14px 0 7px 2px;

    color: #cbd3e8;

    font-size: 0.85rem;

    font-weight: 650;
}


/* Streamlit inputs */

div[data-baseweb="input"] {

    background:
        rgba(255,255,255,0.055) !important;

    border:
        1px solid rgba(255,255,255,0.12) !important;

    border-radius:
        16px !important;

    transition:
        all 0.2s ease !important;
}


div[data-baseweb="input"]:focus-within {

    border-color:
        rgba(115,135,255,0.85) !important;

    box-shadow:
        0 0 0 3px rgba(100,120,255,0.11),
        0 0 28px rgba(80,100,255,0.16) !important;
}


div[data-baseweb="input"] input {

    color: #ffffff !important;

    background: transparent !important;
}


/* Sign in button */

.login-button-space {

    margin-top: 18px;
}


.login-security {

    margin-top: 22px;

    padding-top: 18px;

    border-top:
        1px solid rgba(255,255,255,0.07);

    color: #727c96;

    font-size: 0.76rem;

    line-height: 1.5;
}


</style>
""",
        unsafe_allow_html=True,
    )


# =========================================================
# LOGIN CARD
# =========================================================

def render_login_card():

    # IMPORTANT:
    # Use st.html() instead of st.markdown()
    # so the HTML cannot accidentally appear as
    # literal text on the login screen.

    login_html = """
    <div class="login-page">

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
    """

    # st.html is available in modern Streamlit.
    # Fallback is included for compatibility.

    if hasattr(st, "html"):

        st.html(login_html)

    else:

        st.markdown(
            login_html,
            unsafe_allow_html=True,
        )


# =========================================================
# REQUIRE LOGIN
# =========================================================

def require_login() -> bool:

    init_auth_state()

    # Already authenticated
    if is_authenticated():
        return True

    # Login styling
    render_login_styles()

    # Login header
    render_login_card()

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
    # LOGIN FORM
    # -----------------------------------------------------

    with st.form(
        "administrator_login_form",
        clear_on_submit=False,
    ):

        username = st.text_input(
            "Username",
            placeholder="Enter administrator username",
            autocomplete="username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter administrator password",
            autocomplete="current-password",
        )

        submitted = st.form_submit_button(
            "🔐  Sign In",
            type="primary",
            use_container_width=True,
        )

    # -----------------------------------------------------
    # PROCESS LOGIN
    # -----------------------------------------------------

    if submitted:

        if not username.strip():

            st.error(
                "Please enter your username."
            )

            st.stop()

        if not password:

            st.error(
                "Please enter your password."
            )

            st.stop()

        if login_user(
            username,
            password,
        ):

            st.success(
                "✓ Authentication successful."
            )

            # Do NOT modify widget-bound session keys.
            # Just rerun after authentication.

            st.rerun()

        else:

            if is_locked():

                st.error(
                    "🔒 Too many failed attempts. "
                    "Login temporarily locked."
                )

                st.warning(
                    f"Try again in "
                    f"{seconds_remaining()} seconds."
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
                        f"attempt(s) remaining."
                    )

    # -----------------------------------------------------
    # SECURITY FOOTER
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="login-security">
            🔒 Administrator-only access<br>
            Authentication protected by session security
            and temporary lockout after repeated failures.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Prevent the rest of app.py from rendering
    st.stop()
