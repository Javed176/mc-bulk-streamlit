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
# AUTHENTICATED?
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

    # -----------------------------------------------------
    # Already authenticated
    # -----------------------------------------------------

    if is_authenticated():

        return True


    # =====================================================
    # LOGIN PAGE CSS
    # =====================================================

    st.markdown(
        """
<style>

.stApp {

    background:
        radial-gradient(
            circle at 15% 15%,
            rgba(80,110,255,0.18),
            transparent 32%
        ),

        radial-gradient(
            circle at 85% 20%,
            rgba(170,70,255,0.16),
            transparent 32%
        ),

        linear-gradient(
            135deg,
            #05060a 0%,
            #0b0d16 50%,
            #05060a 100%
        );

}


/* ================================================
   LOGIN CARD
   ================================================ */

.login-card {

    max-width:
        480px;

    margin:
        9vh auto 25px auto;

    padding:
        42px;

    border-radius:
        30px;

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

        0 0 70px
        rgba(100,90,255,0.10),

        inset 0 1px 0
        rgba(255,255,255,0.08);

    backdrop-filter:
        blur(30px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(30px)
        saturate(160%);

    text-align:
        center;

}


/* ================================================
   LOCK
   ================================================ */

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
            rgba(90,120,255,0.25),
            rgba(180,70,255,0.20)
        );

    border:
        1px solid
        rgba(140,150,255,0.25);

    box-shadow:

        0 0 30px
        rgba(90,110,255,0.18),

        inset 0 1px 0
        rgba(255,255,255,0.12);

    animation:
        loginPulse 2.5s
        ease-in-out
        infinite;

}


@keyframes loginPulse {

    0%,
    100% {

        box-shadow:

            0 0 25px
            rgba(90,110,255,0.12),

            inset 0 1px 0
            rgba(255,255,255,0.10);

    }

    50% {

        box-shadow:

            0 0 45px
            rgba(90,110,255,0.30),

            0 0 80px
            rgba(170,70,255,0.12),

            inset 0 1px 0
            rgba(255,255,255,0.16);

    }

}


/* ================================================
   TITLE
   ================================================ */

.login-title {

    font-size:
        2.4rem;

    font-weight:
        800;

    letter-spacing:
        -0.05em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #bcc7ff,
            #ffffff
        );

    -webkit-background-clip:
        text;

    -webkit-text-fill-color:
        transparent;

}


/* ================================================
   SUBTITLE
   ================================================ */

.login-subtitle {

    color:
        rgba(220,225,245,0.62);

    font-size:
        1rem;

    margin-top:
        8px;

}


/* ================================================
   PASSWORD
   ================================================ */

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
        rgba(120,145,255,0.90)
        !important;

    box-shadow:

        0 0 0 3px
        rgba(100,125,255,0.10),

        0 0 35px
        rgba(80,100,255,0.16);

}


input {

    color:
        white
        !important;

}


/* ================================================
   SIGN IN BUTTON
   ================================================ */

.stButton > button {

    min-height:
        52px;

    border-radius:
        18px
        !important;

    border:
        1px solid
        rgba(130,145,255,0.28)
        !important;

    background:
        linear-gradient(
            135deg,
            rgba(90,115,255,0.32),
            rgba(145,70,255,0.26)
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
        rgba(70,80,220,0.20),

        inset 0 1px 0
        rgba(255,255,255,0.12);

    transition:
        all 0.22s ease;

}


.stButton > button:hover {

    transform:
        translateY(-2px)
        scale(1.015);

    box-shadow:

        0 16px 45px
        rgba(80,95,255,0.32),

        0 0 30px
        rgba(130,70,255,0.16),

        inset 0 1px 0
        rgba(255,255,255,0.15);

}


.stButton > button:active {

    transform:
        scale(0.97);

}


/* ================================================
   FOOTER
   ================================================ */

.login-security {

    text-align:
        center;

    color:
        rgba(180,188,215,0.45);

    font-size:
        0.78rem;

    margin-top:
        18px;

}

</style>
""",
        unsafe_allow_html=True,
    )


    # =====================================================
    # LOGIN CARD
    #
    # IMPORTANT:
    # This is deliberately a SEPARATE st.markdown call.
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
        key="login_password",
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

                remaining = (
                    MAX_LOGIN_ATTEMPTS
                    - st.session_state.login_attempts
                )

                st.error(
                    "Incorrect password."
                )

                st.caption(
                    f"{remaining} attempt(s) remaining."
                )


    # =====================================================
    # SECURITY FOOTER
    # =====================================================

    st.markdown(
        """
<div class="login-security">
    🔒 Protected session • Secure authentication
</div>
""",
        unsafe_allow_html=True,
    )


    # Stop app until authenticated
    st.stop()
