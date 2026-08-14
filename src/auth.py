from __future__ import annotations

import hashlib
import hmac
import secrets
import time

import streamlit as st

from src.database import (
    clear_user_session,
    create_access_request,
    create_user_session,
    get_user,
    validate_user_session,
)


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
# PASSWORD
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# ADMIN CREDENTIALS
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

    stored_hash = (
        get_admin_password_hash()
    )

    if stored_hash:

        supplied_hash = hash_password(
            password
        )

        if hmac.compare_digest(
            supplied_hash.lower(),
            stored_hash.lower(),
        ):
            return True

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

    return time.time() < float(
        st.session_state.get(
            "login_locked_until",
            0.0,
        )
    )


def seconds_remaining() -> int:

    return max(
        0,
        int(
            float(
                st.session_state.get(
                    "login_locked_until",
                    0.0,
                )
            )
            - time.time()
        ),
    )


def failed_login():

    attempts = int(
        st.session_state.get(
            "login_attempts",
            0,
        )
    ) + 1

    if attempts >= MAX_LOGIN_ATTEMPTS:

        st.session_state.login_attempts = 0

        st.session_state.login_locked_until = (
            time.time()
            + LOCKOUT_SECONDS
        )

    else:

        st.session_state.login_attempts = attempts


# =========================================================
# DATABASE USER LOGIN
# =========================================================

def _check_database_user(
    username: str,
    password: str,
):

    try:

        record = get_user(
            username
        )

    except Exception:

        return None, "database_error"

    if not record:

        return None, "invalid"

    if not bool(
        record.get(
            "active",
            True,
        )
    ):

        return None, "inactive"

    stored_hash = str(
        record.get(
            "password_hash",
            "",
        )
    ).strip()

    if not stored_hash:

        return None, "invalid"

    supplied_hash = hash_password(
        password
    )

    if hmac.compare_digest(
        supplied_hash.lower(),
        stored_hash.lower(),
    ):

        return record, "ok"

    return None, "invalid"


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

    username = str(
        username
    ).strip()

    if not username or not password:

        failed_login()
        return False

    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    if check_admin_credentials(
        username,
        password,
    ):

        token = secrets.token_urlsafe(
            32
        )

        try:

            admin_record = get_user(
                username
            )

            if admin_record:

                create_user_session(
                    username,
                    token,
                )

        except Exception:

            pass

        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.role = "admin"
        st.session_state.session_token = token
        st.session_state.login_attempts = 0
        st.session_state.login_locked_until = 0.0

        return True

    # -----------------------------------------------------
    # STANDARD USER
    # -----------------------------------------------------

    record, status = (
        _check_database_user(
            username,
            password,
        )
    )

    if status != "ok" or not record:

        failed_login()
        return False

    role = str(
        record.get(
            "role",
            "standard_user",
        )
    ).lower()

    if role in {
        "admin",
        "administrator",
    }:

        role = "admin"

    else:

        role = "standard_user"

    # -----------------------------------------------------
    # NEW LOGIN REPLACES OLD LOGIN
    # -----------------------------------------------------

    token = secrets.token_urlsafe(
        32
    )

    try:

        create_user_session(
            username,
            token,
        )

    except Exception:

        return False

    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.role = role
    st.session_state.session_token = token
    st.session_state.login_attempts = 0
    st.session_state.login_locked_until = 0.0

    return True


# =========================================================
# SESSION VALIDATION
# =========================================================

def validate_current_session():

    init_auth_state()

    if not st.session_state.get(
        "authenticated",
        False,
    ):

        return False, "not_authenticated"

    username = st.session_state.get(
        "username",
        "",
    )

    token = st.session_state.get(
        "session_token",
        "",
    )

    if not username or not token:

        return False, "missing_session"

    try:

        return validate_user_session(
            username,
            token,
        )

    except Exception:

        return False, "database_error"


# =========================================================
# AUTHENTICATED?
# =========================================================

def is_authenticated() -> bool:

    init_auth_state()

    if not st.session_state.get(
        "authenticated",
        False,
    ):

        return False

    valid, _ = (
        validate_current_session()
    )

    if not valid:

        logout_user(
            clear_database=False
        )

        return False

    return True


# =========================================================
# ADMIN?
# =========================================================

def is_admin() -> bool:

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
# LOGOUT
# =========================================================

def logout_user(
    clear_database: bool = True,
):

    username = st.session_state.get(
        "username",
        "",
    )

    token = st.session_state.get(
        "session_token",
        "",
    )

    if (
        clear_database
        and username
        and token
    ):

        try:

            clear_user_session(
                username,
                token,
            )

        except Exception:

            pass

    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.session_token = ""
    st.session_state.login_attempts = 0
    st.session_state.login_locked_until = 0.0


# =========================================================
# ACCESS REQUEST
# =========================================================

def _request_access():

    st.markdown(
        "### 📱 Request Access"
    )

    st.caption(
        "Enter your WhatsApp number. "
        "An administrator will contact you."
    )

    with st.form(
        "request_access_form",
        clear_on_submit=True,
    ):

        whatsapp = st.text_input(
            "WhatsApp Number",
            placeholder="+1 555 123 4567",
        )

        submitted = (
            st.form_submit_button(
                "📲 Request Access",
                type="primary",
                use_container_width=True,
            )
        )

    if submitted:

        clean_number = (
            str(whatsapp)
            .strip()
        )

        if not clean_number:

            st.error(
                "Please enter your WhatsApp number."
            )

            return

        # Basic validation:
        # numbers plus common phone separators only.
        allowed = set(
            "0123456789+()- ."
        )

        if any(
            char not in allowed
            for char in clean_number
        ):

            st.error(
                "Please enter a valid WhatsApp number."
            )

            return

        digits = "".join(
            char
            for char in clean_number
            if char.isdigit()
        )

        if len(digits) < 7:

            st.error(
                "Please enter a valid WhatsApp number."
            )

            return

        try:

            create_access_request(
                clean_number
            )

            st.success(
                "✓ Request sent. "
                "An administrator will contact you on WhatsApp."
            )

        except Exception as exc:

            st.error(
                f"Unable to send request: {exc}"
            )


# =========================================================
# LOGIN SCREEN
# =========================================================

def require_login() -> bool:

    init_auth_state()

    if is_authenticated():
        return True

    st.markdown(
        """
        <style>

        .login-title {
            text-align:center;
            font-size:2.6rem;
            font-weight:800;
            margin-top:8vh;
            color:white;
        }

        .login-subtitle {
            text-align:center;
            color:#9da6c0;
            margin-bottom:25px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns(
        [1, 2, 1]
    )

    with center:

        st.markdown(
            '<div class="login-title">✦ MC Search</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="login-subtitle">'
            'Secure administrator / user access'
            '</div>',
            unsafe_allow_html=True,
        )

        if is_locked():

            st.error(
                "🔒 Too many failed login attempts."
            )

            st.warning(
                f"Try again in "
                f"{seconds_remaining()} seconds."
            )

            st.stop()

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        with st.form(
            "mc_login_form",
            clear_on_submit=False,
        ):

            username = st.text_input(
                "Username",
                placeholder="Enter username",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password",
            )

            submitted = (
                st.form_submit_button(
                    "🔐 Sign In",
                    type="primary",
                    use_container_width=True,
                )
            )

        if submitted:

            if login_user(
                username,
                password,
            ):

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

        # -------------------------------------------------
        # REQUEST ACCESS
        # -------------------------------------------------

        st.divider()

        _request_access()

    st.stop()
