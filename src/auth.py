from __future__ import annotations

import hashlib
import hmac
import secrets
import time

import streamlit as st

from src.database import get_user


# =========================================================
# SECURITY 
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
# PASSWORD HASH
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# ADMIN FALLBACK
#
# This allows login using Streamlit Secrets even if the
# Supabase users table is not configured correctly yet.
#
# Add:
#
# ADMIN_USERNAME = "admin"
# ADMIN_PASSWORD_HASH = "your_sha256_hash"
#
# =========================================================

def get_admin_username() -> str:

    try:
        return str(
            st.secrets.get(
                "ADMIN_USERNAME",
                "admin",
            )
        ).strip()

    except Exception:
        return "admin"


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
# PASSWORD CHECK
# =========================================================

def verify_password(
    username: str,
    password: str,
) -> tuple[bool, str]:

    username = username.strip()
    password = password.strip()

    if not username or not password:
        return False, ""

    supplied_hash = hash_password(password)

    # -----------------------------------------------------
    # 1. Try Supabase user
    # -----------------------------------------------------

    try:

        user = get_user(username)

        if user:

            # Inactive users cannot log in.
            if not bool(
                user.get(
                    "active",
                    True,
                )
            ):
                return False, ""

            stored_hash = str(
                user.get(
                    "password_hash",
                    "",
                )
            ).strip()

            if stored_hash and hmac.compare_digest(
                supplied_hash,
                stored_hash,
            ):

                role = str(
                    user.get(
                        "role",
                        "user",
                    )
                ).strip().lower()

                return True, role

    except Exception:
        # Do not crash the login page if Supabase
        # is temporarily unavailable.
        pass

    # -----------------------------------------------------
    # 2. Streamlit Secrets administrator fallback
    # -----------------------------------------------------

    admin_username = get_admin_username()
    admin_hash = get_admin_password_hash()

    if (
        username == admin_username
        and admin_hash
        and hmac.compare_digest(
            supplied_hash,
            admin_hash,
        )
    ):

        return True, "admin"

    return False, ""


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

    valid, role = verify_password(
        username,
        password,
    )

    if valid:

        # IMPORTANT:
        # These are NOT widget keys, so it is safe to
        # update them here before rerunning.
        st.session_state["authenticated"] = True

        st.session_state["username"] = (
            username.strip()
        )

        st.session_state["role"] = role or "user"

        st.session_state["session_token"] = (
            secrets.token_urlsafe(32)
        )

        st.session_state["login_attempts"] = 0

        st.session_state["login_locked_until"] = 0.0

        return True

    # -----------------------------------------------------
    # Failed login
    # -----------------------------------------------------

    st.session_state["login_attempts"] += 1

    if (
        st.session_state["login_attempts"]
        >= MAX_LOGIN_ATTEMPTS
    ):

        st.session_state["login_locked_until"] = (
            time.time()
            + LOCKOUT_SECONDS
        )

        st.session_state["login_attempts"] = 0

    return False


# =========================================================
# LOGOUT
# =========================================================

def logout_user():

    st.session_state["authenticated"] = False

    st.session_state["username"] = ""

    st.session_state["role"] = ""

    st.session_state["session_token"] = ""

    st.session_state["login_attempts"] = 0

    st.session_state["login_locked_until"] = 0.0


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
            "session_token",
            "",
        )
    )


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin() -> bool:

    init_auth_state()

    return bool(
        is_authenticated()
        and str(
            st.session_state.get(
                "role",
                "",
            )
        ).lower()
        == "admin"
    )


# =========================================================
# LOGIN PAGE CSS
# =========================================================

def login_css():

    st.markdown(
        """
<style>

.login-page {
    max-width: 520px;
    margin: 9vh auto 0 auto;
}

.login-card {
    padding: 42px;
    border-radius: 30px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.11),
            rgba(255,255,255,0.035)
        );

    border:
        1px solid rgba(255,255,255,0.14);

    box-shadow:
        0 30px 100px rgba(0,0,0,0.55),
        inset 0 1px 0 rgba(255,255,255,0.08);

    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);

    text-align: center;
}

.login-lock {
    width: 72px;
    height: 72px;

    margin: 0 auto 20px auto;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 22px;

    font-size: 2rem;

    background:
        linear-gradient(
            135deg,
            rgba(100,120,255,0.20),
            rgba(180,70,255,0.15)
        );

    border:
        1px solid rgba(130,150,255,0.25);

    box-shadow:
        0 0 35px rgba(100,110,255,0.18),
        inset 0 1px 0 rgba(255,255,255,0.12);
}

.login-title {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.04em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #b9c5ff,
            #ffffff
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.login-subtitle {
    margin-top: 8px;
    margin-bottom: 30px;

    color: #9da6c0;
    font-size: 0.95rem;
}

</style>
""",
        unsafe_allow_html=True,
    )


# =========================================================
# LOGIN SCREEN
# =========================================================

def require_login() -> bool:

    init_auth_state()

    # Already authenticated.
    if is_authenticated():
        return True

    login_css()

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    st.markdown(
        """
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
""",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # Lockout
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
    #
    # Using a form prevents the username/password widgets
    # from being manipulated after they are created.
    # -----------------------------------------------------

    with st.form(
        "login_form",
        clear_on_submit=False,
    ):

        username = st.text_input(
            "Username",
            placeholder="Enter username",
            key="login_username_input",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password",
            key="login_password_input",
        )

        submitted = st.form_submit_button(
            "🔐 Sign In",
            type="primary",
            use_container_width=True,
        )

    # -----------------------------------------------------
    # LOGIN ATTEMPT
    # -----------------------------------------------------

    if submitted:

        username_clean = (
            str(username)
            .strip()
        )

        if not username_clean or not password:

            st.error(
                "Please enter both username and password."
            )

        elif login_user(
            username_clean,
            password,
        ):

            # DO NOT clear login_username_input or
            # login_password_input here.
            #
            # They are widget-owned keys. Changing them
            # after rendering can cause StreamlitAPIException.
            #
            # Authentication state uses separate keys.

            st.success(
                "✓ Authentication successful."
            )

            time.sleep(0.25)

            st.rerun()

        else:

            if is_locked():

                st.error(
                    "🔒 Too many failed attempts. "
                    f"Try again in {seconds_remaining()} seconds."
                )

            else:

                remaining = (
                    MAX_LOGIN_ATTEMPTS
                    - st.session_state.get(
                        "login_attempts",
                        0,
                    )
                )

                st.error(
                    "Invalid username or password."
                )

                if remaining > 0:

                    st.caption(
                        f"{remaining} attempt(s) remaining."
                    )

    # -----------------------------------------------------
    # STOP SCRIPT
    # -----------------------------------------------------

    st.stop()
