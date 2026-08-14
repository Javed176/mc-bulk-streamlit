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

        # Admin sessions do not require a users-table row.
        "database_session": False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# PASSWORD HASH
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        str(password).encode("utf-8")
    ).hexdigest()


# =========================================================
# ADMIN SECRETS
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
# ADMIN LOGIN
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
        str(username).strip(),
        configured_username,
    ):

        return False

    stored_hash = (
        get_admin_password_hash()
    )

    # SHA-256 hash
    if stored_hash:

        supplied_hash = hash_password(
            password
        )

        if hmac.compare_digest(
            supplied_hash.lower(),
            stored_hash.lower(),
        ):

            return True

        # Compatibility with an old deployment
        # where ADMIN_PASSWORD_HASH contained
        # the actual password.
        if len(stored_hash) != 64:

            if hmac.compare_digest(
                password,
                stored_hash,
            ):

                return True

    # Plain password secret
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

    return (
        time.time()
        <
        float(
            st.session_state.get(
                "login_locked_until",
                0.0,
            )
        )
    )


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

        st.session_state.login_attempts = (
            attempts
        )


# =========================================================
# DATABASE HELPERS
#
# IMPORTANT:
# These imports are intentionally inside functions.
# This prevents an import-time crash from hiding
# the entire login page.
# =========================================================

def _database_get_user(username: str):

    from src.database import get_user

    return get_user(username)


def _database_create_session(
    username: str,
    token: str,
):

    from src.database import create_user_session

    return create_user_session(
        username,
        token,
    )


def _database_validate_session(
    username: str,
    token: str,
):

    from src.database import validate_user_session

    return validate_user_session(
        username,
        token,
    )


def _database_clear_session(
    username: str,
    token: str,
):

    from src.database import clear_user_session

    return clear_user_session(
        username,
        token,
    )


# =========================================================
# DATABASE USER LOGIN
# =========================================================

def _check_database_user(
    username: str,
    password: str,
):

    try:

        record = _database_get_user(
            username
        )

    except Exception as exc:

        return None, "database_error", exc

    if not record:

        return None, "invalid", None

    # -----------------------------------------------------
    # Active check
    # -----------------------------------------------------

    if not bool(
        record.get(
            "active",
            True,
        )
    ):

        return None, "inactive", None

    stored_hash = str(
        record.get(
            "password_hash",
            "",
        )
    ).strip()

    if not stored_hash:

        return None, "invalid", None

    supplied_hash = hash_password(
        password
    )

    if hmac.compare_digest(
        supplied_hash.lower(),
        stored_hash.lower(),
    ):

        return record, "ok", None

    return None, "invalid", None


# =========================================================
# LOGIN
# =========================================================

def login_user(
    username: str,
    password: str,
) -> tuple[bool, str]:

    init_auth_state()

    if is_locked():

        return False, "locked"

    username = str(username).strip()

    if not username or not password:

        failed_login()

        return False, "invalid"

    # =====================================================
    # ADMIN
    # =====================================================

    if check_admin_credentials(
        username,
        password,
    ):

        token = secrets.token_urlsafe(32)

        # Admin is a local Streamlit-secret account.
        # It does NOT depend on a users-table row.
        st.session_state.authenticated = True

        st.session_state.username = username

        st.session_state.role = "admin"

        st.session_state.session_token = token

        st.session_state.database_session = False

        st.session_state.login_attempts = 0

        st.session_state.login_locked_until = 0.0

        return True, "ok"

    # =====================================================
    # STANDARD USER
    # =====================================================

    record, status, error = (
        _check_database_user(
            username,
            password,
        )
    )

    if status == "database_error":

        return False, "database_error"

    if status == "inactive":

        failed_login()

        return False, "inactive"

    if status != "ok" or not record:

        failed_login()

        return False, "invalid"

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
    # Create a database session.
    #
    # The database stores only ONE token for the user.
    # Logging in from another browser/tab replaces it.
    # -----------------------------------------------------

    token = secrets.token_urlsafe(32)

    try:

        _database_create_session(
            username,
            token,
        )

    except Exception:

        return False, "database_error"

    st.session_state.authenticated = True

    st.session_state.username = username

    st.session_state.role = role

    st.session_state.session_token = token

    st.session_state.database_session = True

    st.session_state.login_attempts = 0

    st.session_state.login_locked_until = 0.0

    return True, "ok"


# =========================================================
# CURRENT SESSION VALIDATION
# =========================================================

def validate_current_session():

    init_auth_state()

    if not st.session_state.get(
        "authenticated",
        False,
    ):

        return False, "not_authenticated"

    username = str(
        st.session_state.get(
            "username",
            "",
        )
    )

    token = str(
        st.session_state.get(
            "session_token",
            "",
        )
    )

    if not username or not token:

        return False, "missing_session"

    # -----------------------------------------------------
    # Admin sessions are controlled by Streamlit session
    # state and secrets, not the users table.
    # -----------------------------------------------------

    if not bool(
        st.session_state.get(
            "database_session",
            False,
        )
    ):

        if (
            st.session_state.get(
                "role",
                "",
            )
            == "admin"
            and check_admin_credentials(
                username,
                # We cannot recover the password from
                # session state, so simply keep the admin
                # session alive for this browser session.
                "",
            )
        ):

            return True, "ok"

        # Configured admin is still considered valid
        # for this Streamlit session.
        if (
            st.session_state.get(
                "role",
                "",
            )
            == "admin"
        ):

            return True, "ok"

        return False, "missing_session"

    # -----------------------------------------------------
    # Database-backed standard user session
    # -----------------------------------------------------

    try:

        return _database_validate_session(
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

    valid, reason = (
        validate_current_session()
    )

    if valid:

        return True

    # A database error should not silently destroy
    # the user's local session.
    if reason == "database_error":

        return True

    logout_user(
        clear_database=False
    )

    return False


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

    username = str(
        st.session_state.get(
            "username",
            "",
        )
    )

    token = str(
        st.session_state.get(
            "session_token",
            "",
        )
    )

    database_session = bool(
        st.session_state.get(
            "database_session",
            False,
        )
    )

    if (
        clear_database
        and database_session
        and username
        and token
    ):

        try:

            _database_clear_session(
                username,
                token,
            )

        except Exception:

            pass

    st.session_state.authenticated = False

    st.session_state.username = ""

    st.session_state.role = ""

    st.session_state.session_token = ""

    st.session_state.database_session = False

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

.login-title {
    text-align: center;
    font-size: 2.6rem;
    font-weight: 850;
    margin-top: 8vh;
    color: white;
}

.login-subtitle {
    text-align: center;
    color: #9da6c0;
    margin-bottom: 25px;
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
            '<div class="login-title">'
            '✦ MC Search'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="login-subtitle">'
            'Secure administrator / user access'
            '</div>',
            unsafe_allow_html=True,
        )

        # -------------------------------------------------
        # LOCKOUT
        # -------------------------------------------------

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
        # LOGIN FORM
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

        # -------------------------------------------------
        # SUBMIT
        # -------------------------------------------------

        if submitted:

            success, status = login_user(
                username,
                password,
            )

            if success:

                st.success(
                    "✓ Authentication successful."
                )

                time.sleep(0.25)

                st.rerun()

            elif status == "locked":

                st.error(
                    "🔒 Too many failed attempts. "
                    "Login temporarily locked."
                )

            elif status == "inactive":

                st.error(
                    "This account is inactive. "
                    "Contact an administrator."
                )

            elif status == "database_error":

                st.error(
                    "Unable to access the user database. "
                    "Please check your Supabase configuration "
                    "and database.py."
                )

            else:

                st.error(
                    "Invalid username or password."
                )

                if not is_locked():

                    remaining = (
                        MAX_LOGIN_ATTEMPTS
                        - int(
                            st.session_state.get(
                                "login_attempts",
                                0,
                            )
                        )
                    )

                    if remaining > 0:

                        st.caption(
                            f"{remaining} "
                            f"attempt(s) remaining."
                        )

    st.stop()
