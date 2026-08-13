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
# SHA256
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# GET ADMIN CREDENTIALS
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


def get_admin_password() -> str:

    try:

        return str(
            st.secrets.get(
                "ADMIN_PASSWORD",
                "",
            )
        )

    except Exception:

        return ""


# =========================================================
# CHECK ADMIN LOGIN
# =========================================================

def check_admin_credentials(
    username: str,
    password: str,
) -> bool:

    configured_username = (
        get_admin_username()
    )

    if not configured_username:
        return False

    if not hmac.compare_digest(
        username.strip(),
        configured_username,
    ):
        return False

    # -----------------------------------------------------
    # OPTION 1
    # Proper SHA256 hash
    # -----------------------------------------------------

    stored_hash = (
        get_admin_password_hash()
    )

    if stored_hash:

        supplied_hash = hash_password(
            password
        )

        if hmac.compare_digest(
            supplied_hash,
            stored_hash,
        ):
            return True

    # -----------------------------------------------------
    # OPTION 2
    # Plain secret fallback
    #
    # This allows the current setup to work if you have:
    #
    # ADMIN_PASSWORD = "your-password"
    #
    # in Streamlit Secrets.
    # -----------------------------------------------------

    stored_password = (
        get_admin_password()
    )

    if stored_password:

        if hmac.compare_digest(
            password,
            stored_password,
        ):
            return True

    return False


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
# FAILED LOGIN
# =========================================================

def failed_login():

    attempts = int(
        st.session_state.get(
            "login_attempts",
            0,
        )
    )

    attempts += 1

    if attempts >= MAX_LOGIN_ATTEMPTS:

        st.session_state.login_attempts = 0

        st.session_state.login_locked_until = (
            time.time()
            + LOCKOUT_SECONDS
        )

    else:

        st.session_state.login_attempts = attempts


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

    username = str(username).strip()

    if not username or not password:
        failed_login()
        return False

    if check_admin_credentials(
        username,
        password,
    ):

        st.session_state.authenticated = True

        st.session_state.username = (
            username
        )

        st.session_state.role = "admin"

        st.session_state.session_token = (
            secrets.token_urlsafe(32)
        )

        st.session_state.login_attempts = 0

        st.session_state.login_locked_until = 0.0

        return True

    failed_login()

    return False


# =========================================================
# AUTH CHECK
# =========================================================

def is_authenticated() -> bool:

    init_auth_state()

    return bool(
        st.session_state.get(
            "authenticated",
            False,
        )
        and st.session_state.get(
            "username",
            "",
        )
        and st.session_state.get(
            "session_token",
            "",
        )
    )


# =========================================================
# ADMIN CHECK
# =========================================================

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
# LOGOUT
# =========================================================

def logout_user():

    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.session_token = ""

    st.session_state.login_attempts = 0
    st.session_state.login_locked_until = 0.0


# =========================================================
# LOGIN SCREEN
# =========================================================

def require_login() -> bool:

    init_auth_state()

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

    margin: 9vh auto 25px auto;

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

    text-align: center;
}

.login-lock {
    font-size: 3rem;

    margin-bottom: 10px;

    filter:
        drop-shadow(
            0 0 18px
            rgba(120,140,255,0.7)
        );
}

.login-title {
    font-size: 2.4rem;

    font-weight: 850;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #b8c4ff,
            #ffffff
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.login-subtitle {
    color: #9da6c0;

    margin-top: 7px;

    margin-bottom: 5px;
}

div[data-baseweb="input"] {

    border-radius:
        16px !important;

    background:
        rgba(255,255,255,0.055)
        !important;

    border:
        1px solid
        rgba(255,255,255,0.13)
        !important;
}

div[data-baseweb="input"]:focus-within {

    border-color:
        rgba(110,135,255,0.9)
        !important;

    box-shadow:
        0 0 0 3px
        rgba(100,125,255,0.12),

        0 0 30px
        rgba(80,100,255,0.18);
}

input {
    color: white !important;
}

.stButton > button {

    min-height: 52px;

    border-radius:
        17px !important;

    font-weight:
        750 !important;

    transition:
        transform .2s ease,
        box-shadow .2s ease;
}

.stButton > button:hover {

    transform:
        translateY(-2px)
        scale(1.01);

    box-shadow:
        0 12px 35px
        rgba(90,110,255,0.3);
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
        Secure administrator access
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
    # LOGIN FORM
    # =====================================================

    with st.form(
        "mc_admin_login",
        clear_on_submit=False,
    ):

        username = st.text_input(
            "Username",
            placeholder="Administrator username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Administrator password",
        )

        submitted = st.form_submit_button(
            "🔐 Sign In",
            type="primary",
            use_container_width=True,
        )

    # =====================================================
    # SUBMIT
    # =====================================================

    if submitted:

        if login_user(
            username,
            password,
        ):

            st.success(
                "✓ Authentication successful."
            )

            time.sleep(0.3)

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
                    - int(
                        st.session_state.get(
                            "login_attempts",
                            0,
                        )
                    )
                )

                st.error(
                    "Invalid username or password."
                )

                if remaining > 0:

                    st.caption(
                        f"{remaining} "
                        f"attempt(s) remaining."
                    )

    st.stop()
