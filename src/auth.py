from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timezone

import streamlit as st

from src.database import (
    get_user,
    get_user_session,
    create_user_session,
    clear_user_session,
    validate_user_session,
)


# =========================================================
# SECURITY SETTINGS
# =========================================================

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300

DEFAULT_SESSION_TIMEOUT_MINUTES = 60
DEFAULT_SEARCH_DELAY_SECONDS = 1


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

        # User-specific settings
        "search_delay_seconds": DEFAULT_SEARCH_DELAY_SECONDS,
        "session_timeout_minutes": DEFAULT_SESSION_TIMEOUT_MINUTES,

        # Session timing
        "session_started_at": None,
        "session_expires_at": None,

        # Prevent repeated validation during same run
        "auth_checked": False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        str(password).encode("utf-8")
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


# =========================================================
# ADMIN AUTHENTICATION
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

    stored_hash = (
        get_admin_password_hash()
    )

    # -----------------------------------------------------
    # SHA256 HASH
    # -----------------------------------------------------

    if stored_hash:

        supplied_hash = hash_password(
            password
        )

        if hmac.compare_digest(
            supplied_hash.lower(),
            stored_hash.lower(),
        ):
            return True

    # -----------------------------------------------------
    # PLAIN PASSWORD FALLBACK
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
# LOGIN LOCKOUT
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
# CLEAR LOCAL AUTH STATE
# =========================================================

def _clear_local_auth():

    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.session_token = ""

    st.session_state.search_delay_seconds = (
        DEFAULT_SEARCH_DELAY_SECONDS
    )

    st.session_state.session_timeout_minutes = (
        DEFAULT_SESSION_TIMEOUT_MINUTES
    )

    st.session_state.session_started_at = None
    st.session_state.session_expires_at = None
    st.session_state.auth_checked = False


# =========================================================
# CALCULATE EXPIRATION
# =========================================================

def _calculate_expiration(
    started_at,
    timeout_minutes: int,
):

    if not started_at:
        return None

    try:

        started = datetime.fromisoformat(
            str(started_at).replace(
                "Z",
                "+00:00",
            )
        )

        if started.tzinfo is None:

            started = started.replace(
                tzinfo=timezone.utc,
            )

        return (
            started.timestamp()
            + (
                max(
                    1,
                    int(timeout_minutes),
                )
                * 60
            )
        )

    except Exception:

        return None


# =========================================================
# START DATABASE SESSION
# =========================================================

def _start_database_session(
    username: str,
    token: str,
):

    try:

        result = create_user_session(
            username,
            token,
        )

        return bool(result)

    except Exception:

        return False


# =========================================================
# STANDARD USER LOGIN
# =========================================================

def _check_standard_user(
    username: str,
    password: str,
):

    try:

        record = get_user(
            username.strip()
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

    if not hmac.compare_digest(
        supplied_hash.lower(),
        stored_hash.lower(),
    ):

        return None, "invalid"

    return record, "ok"


# =========================================================
# LOGIN USER
# =========================================================

def login_user(
    username: str,
    password: str,
) -> tuple[bool, str]:

    init_auth_state()

    if is_locked():

        return False, "locked"

    clean_username = str(
        username
    ).strip()

    clean_password = str(
        password
    )

    if not clean_username or not clean_password:

        failed_login()

        return False, "invalid"

    # =====================================================
    # ADMIN LOGIN
    # =====================================================

    if check_admin_credentials(
        clean_username,
        clean_password,
    ):

        token = secrets.token_urlsafe(
            48
        )

        # Admin does not require a users-table
        # session because the administrator credentials
        # come from Streamlit Secrets.
        st.session_state.authenticated = True
        st.session_state.username = (
            clean_username
        )
        st.session_state.role = "admin"
        st.session_state.session_token = token

        st.session_state.search_delay_seconds = (
            DEFAULT_SEARCH_DELAY_SECONDS
        )

        st.session_state.session_timeout_minutes = (
            DEFAULT_SESSION_TIMEOUT_MINUTES
        )

        started = datetime.now(
            timezone.utc
        )

        st.session_state.session_started_at = (
            started.isoformat()
        )

        st.session_state.session_expires_at = (
            started.timestamp()
            + (
                DEFAULT_SESSION_TIMEOUT_MINUTES
                * 60
            )
        )

        st.session_state.login_attempts = 0
        st.session_state.login_locked_until = 0.0

        return True, "admin"

    # =====================================================
    # STANDARD USER LOGIN
    # =====================================================

    record, status = _check_standard_user(
        clean_username,
        clean_password,
    )

    if status != "ok" or not record:

        if status in {
            "invalid",
            "inactive",
            "database_error",
        }:

            failed_login()

        return False, status

    role = str(
        record.get(
            "role",
            "standard_user",
        )
    ).lower()

    if role == "user":
        role = "standard_user"

    if role not in {
        "standard_user",
        "admin",
    }:

        role = "standard_user"

    token = secrets.token_urlsafe(
        48
    )

    # =====================================================
    # CRITICAL:
    # Store the token in Supabase.
    #
    # If this same username logs in from another
    # browser/tab/device, the old token gets replaced.
    # The old session will then fail validation.
    # =====================================================

    if not _start_database_session(
        clean_username,
        token,
    ):

        failed_login()

        return False, "database_error"

    timeout_minutes = max(
        1,
        int(
            record.get(
                "session_timeout_minutes",
                DEFAULT_SESSION_TIMEOUT_MINUTES,
            )
            or DEFAULT_SESSION_TIMEOUT_MINUTES
        ),
    )

    delay_seconds = max(
        0,
        int(
            record.get(
                "search_delay_seconds",
                DEFAULT_SEARCH_DELAY_SECONDS,
            )
            or DEFAULT_SEARCH_DELAY_SECONDS
        ),
    )

    started_at = (
        datetime.now(
            timezone.utc
        )
    )

    st.session_state.authenticated = True
    st.session_state.username = (
        clean_username
    )
    st.session_state.role = role
    st.session_state.session_token = token

    st.session_state.search_delay_seconds = (
        delay_seconds
    )

    st.session_state.session_timeout_minutes = (
        timeout_minutes
    )

    st.session_state.session_started_at = (
        started_at.isoformat()
    )

    st.session_state.session_expires_at = (
        started_at.timestamp()
        + (
            timeout_minutes
            * 60
        )
    )

    st.session_state.login_attempts = 0
    st.session_state.login_locked_until = 0.0

    return True, role


# =========================================================
# VALIDATE CURRENT SESSION
# =========================================================

def validate_current_session() -> tuple[bool, str]:

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
    ).strip()

    token = str(
        st.session_state.get(
            "session_token",
            "",
        )
    ).strip()

    role = str(
        st.session_state.get(
            "role",
            "",
        )
    ).lower()

    if not username or not token:

        _clear_local_auth()

        return False, "invalid_local_session"

    # =====================================================
    # ADMIN
    # =====================================================

    if role == "admin":

        expires_at = st.session_state.get(
            "session_expires_at"
        )

        if expires_at:

            try:

                if (
                    time.time()
                    >= float(expires_at)
                ):

                    _clear_local_auth()

                    return False, "expired"

            except Exception:

                pass

        return True, "ok"

    # =====================================================
    # STANDARD USER
    # =====================================================

    try:

        valid, reason = validate_user_session(
            username,
            token,
        )

    except Exception:

        # Do not immediately destroy a valid local
        # session just because Supabase temporarily
        # failed. The next validation can retry.
        return True, "database_unavailable"

    if not valid:

        _clear_local_auth()

        return False, reason

    # -----------------------------------------------------
    # Refresh user settings from database.
    #
    # This means an administrator changing:
    #
    # search_delay_seconds
    # session_timeout_minutes
    #
    # takes effect without requiring the user to log
    # out and back in.
    # -----------------------------------------------------

    try:

        record = get_user_session(
            username
        )

        if record:

            delay_seconds = max(
                0,
                int(
                    record.get(
                        "search_delay_seconds",
                        DEFAULT_SEARCH_DELAY_SECONDS,
                    )
                    or DEFAULT_SEARCH_DELAY_SECONDS
                ),
            )

            timeout_minutes = max(
                1,
                int(
                    record.get(
                        "session_timeout_minutes",
                        DEFAULT_SESSION_TIMEOUT_MINUTES,
                    )
                    or DEFAULT_SESSION_TIMEOUT_MINUTES
                ),
            )

            st.session_state.search_delay_seconds = (
                delay_seconds
            )

            st.session_state.session_timeout_minutes = (
                timeout_minutes
            )

            started_at = record.get(
                "session_started_at"
            )

            st.session_state.session_started_at = (
                started_at
            )

            st.session_state.session_expires_at = (
                _calculate_expiration(
                    started_at,
                    timeout_minutes,
                )
            )

    except Exception:

        pass

    return True, "ok"


# =========================================================
# AUTHENTICATION CHECK
# =========================================================

def is_authenticated() -> bool:

    init_auth_state()

    if not st.session_state.get(
        "authenticated",
        False,
    ):

        return False

    valid, _ = validate_current_session()

    return valid


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin() -> bool:

    if not is_authenticated():
        return False

    return (
        str(
            st.session_state.get(
                "role",
                "",
            )
        ).lower()
        == "admin"
    )


# =========================================================
# GET CURRENT SEARCH DELAY
# =========================================================

def get_search_delay_seconds() -> int:

    init_auth_state()

    return max(
        0,
        int(
            st.session_state.get(
                "search_delay_seconds",
                DEFAULT_SEARCH_DELAY_SECONDS,
            )
            or DEFAULT_SEARCH_DELAY_SECONDS
        ),
    )


# =========================================================
# GET REMAINING SESSION SECONDS
# =========================================================

def get_session_seconds_remaining() -> int:

    init_auth_state()

    expires_at = st.session_state.get(
        "session_expires_at"
    )

    if not expires_at:

        return 0

    try:

        return max(
            0,
            int(
                float(expires_at)
                - time.time()
            ),
        )

    except Exception:

        return 0


# =========================================================
# LOGOUT
# =========================================================

def logout_user():

    username = str(
        st.session_state.get(
            "username",
            "",
        )
    ).strip()

    token = str(
        st.session_state.get(
            "session_token",
            "",
        )
    ).strip()

    # Standard users have their database session
    # removed. The token check prevents an old browser
    # from clearing a newer login.
    if username and token:

        try:

            role = str(
                st.session_state.get(
                    "role",
                    "",
                )
            ).lower()

            if role != "admin":

                clear_user_session(
                    username,
                    token,
                )

        except Exception:

            pass

    _clear_local_auth()


# =========================================================
# LOGIN SCREEN
# =========================================================

def require_login() -> bool:

    init_auth_state()

    # =====================================================
    # EXISTING SESSION
    # =====================================================

    if st.session_state.get(
        "authenticated",
        False,
    ):

        valid, reason = (
            validate_current_session()
        )

        if valid:

            return True

        # -------------------------------------------------
        # Session was replaced, disabled or expired.
        # -------------------------------------------------

        if reason == "session_replaced":

            st.warning(
                "🔐 This account was signed in "
                "from another browser or tab. "
                "This session has been signed out."
            )

        elif reason == "inactive":

            st.error(
                "🚫 This account has been disabled "
                "by an administrator."
            )

        elif reason == "expired":

            st.warning(
                "⏰ Your session has expired. "
                "Please sign in again."
            )

        else:

            st.warning(
                "Your session is no longer valid. "
                "Please sign in again."
            )

        st.stop()

    # =====================================================
    # LOGIN CSS
    # =====================================================

    st.markdown(
        """
<style>

.login-wrap {
    max-width: 520px;
    margin: 9vh auto 0 auto;
}

.login-card {
    padding: 42px;
    border-radius: 30px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.11),
            rgba(255,255,255,.035)
        );

    border:
        1px solid
        rgba(255,255,255,.14);

    box-shadow:
        0 30px 100px
        rgba(0,0,0,.55),

        inset 0 1px 0
        rgba(255,255,255,.08);

    backdrop-filter:
        blur(30px);

    text-align: center;
}

.login-lock {
    font-size: 3rem;
    line-height: 1;
    margin-bottom: 12px;

    filter:
        drop-shadow(
            0 0 18px
            rgba(120,140,255,.7)
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
}

</style>

<div class="login-wrap">

    <div class="login-card">

        <div class="login-lock">
            🔐
        </div>

        <div class="login-title">
            ✦ MC Search
        </div>

        <div class="login-subtitle">
            Secure administrator / user access
        </div>

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
        "mc_login_form",
        clear_on_submit=False,
    ):

        username = st.text_input(
            "Username",
            placeholder="Username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Password",
        )

        submitted = st.form_submit_button(
            "🔐 Sign In",
            type="primary",
            use_container_width=True,
        )

    # =====================================================
    # LOGIN SUBMITTED
    # =====================================================

    if submitted:

        success, result = login_user(
            username,
            password,
        )

        if success:

            if result == "admin":

                st.success(
                    "✓ Administrator authentication successful."
                )

            else:

                st.success(
                    "✓ Authentication successful."
                )

            time.sleep(0.25)

            st.rerun()

        else:

            if result == "inactive":

                st.error(
                    "🚫 This account is inactive. "
                    "Contact an administrator."
                )

            elif result == "database_error":

                st.error(
                    "⚠ Unable to contact the user database. "
                    "Please try again."
                )

            elif result == "locked":

                st.error(
                    "🔒 Login temporarily locked."
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
