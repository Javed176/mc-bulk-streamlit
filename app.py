from __future__ import annotations

import io
import time
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from src.search import search_one

from src.auth import (
    logout_user,
    is_admin,
    hash_password,
)

from src.database import (
    create_user_record,
    update_user,
    list_users,
    get_user,
    create_user_session,
    get_user_session,
    validate_user_session,
    clear_user_session,
    update_user_settings,
)

from src.audit import (
    log_action,
    audit_dataframe,
    cleanup_audit_logs,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="MC Search",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# LOGIN SECURITY
# =========================================================

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300


# =========================================================
# SESSION STATE
# =========================================================

def _init_auth_state():

    defaults = {
        "authenticated": False,
        "username": "",
        "role": "",
        "session_token": "",
        "login_attempts": 0,
        "login_locked_until": 0.0,

        "active_page": "Search",

        "running": False,
        "start_mc": "",
        "current_mc": None,
        "last_searched_mc": None,
        "results": [],
        "searched_count": 0,

        "search_delay_seconds": 1,
        "session_timeout_minutes": 60,

        "session_started_at": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


_init_auth_state()


# =========================================================
# HELPERS
# =========================================================

def _secret(
    name: str,
    default: str = "",
) -> str:

    try:
        value = st.secrets.get(
            name,
            default,
        )
    except Exception:
        value = default

    return str(value).strip()


def _parse_datetime(value):

    if not value:
        return None

    try:

        result = datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00",
            )
        )

        if result.tzinfo is None:
            result = result.replace(
                tzinfo=timezone.utc
            )

        return result

    except Exception:

        return None


# =========================================================
# ADMIN CREDENTIALS
# =========================================================

def _admin_login(
    username: str,
    password: str,
) -> bool:

    configured_username = _secret(
        "ADMIN_USERNAME"
    )

    if not configured_username:
        return False

    if not hmac.compare_digest(
        username.strip(),
        configured_username,
    ):
        return False

    stored_hash = _secret(
        "ADMIN_PASSWORD_HASH"
    )

    if len(stored_hash) == 64:

        supplied_hash = hash_password(
            password
        )

        if hmac.compare_digest(
            supplied_hash.lower(),
            stored_hash.lower(),
        ):
            return True

    stored_password = _secret(
        "ADMIN_PASSWORD"
    )

    if stored_password:

        if hmac.compare_digest(
            password,
            stored_password,
        ):
            return True

    # Compatibility with old deployment.
    if stored_hash and len(stored_hash) != 64:

        if hmac.compare_digest(
            password,
            stored_hash,
        ):
            return True

    return False


# =========================================================
# DATABASE USER LOGIN
# =========================================================

def _database_login(
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
        return False, "invalid"

    if not bool(
        record.get(
            "active",
            True,
        )
    ):

        return False, "inactive"

    stored_hash = str(
        record.get(
            "password_hash",
            "",
        )
    ).strip()

    if not stored_hash:
        return False, "invalid"

    supplied_hash = hash_password(
        password
    )

    if hmac.compare_digest(
        supplied_hash.lower(),
        stored_hash.lower(),
    ):

        return record, "ok"

    return False, "invalid"


# =========================================================
# LOGIN LOCKOUT
# =========================================================

def _auth_locked() -> bool:

    return time.time() < float(
        st.session_state.get(
            "login_locked_until",
            0.0,
        )
    )


def _lock_seconds() -> int:

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


def _failed_login():

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
            + LOGIN_LOCKOUT_SECONDS
        )

    else:

        st.session_state.login_attempts = attempts


# =========================================================
# GET CURRENT DATABASE SESSION
# =========================================================

def _get_current_session():

    username = str(
        st.session_state.get(
            "username",
            "",
        )
    ).strip()

    if not username:
        return None

    try:

        return get_user_session(
            username
        )

    except Exception:

        return None


# =========================================================
# CHECK IF ACCOUNT ALREADY HAS A LIVE SESSION
# =========================================================

def _account_has_live_session(
    username: str,
) -> bool:

    try:

        record = get_user_session(
            username
        )

    except Exception:

        return False

    if not record:
        return False

    token = str(
        record.get(
            "session_token",
            "",
        )
        or ""
    )

    if not token:
        return False

    valid, reason = validate_user_session(
        username,
        token,
    )

    return bool(
        valid and reason == "ok"
    )


# =========================================================
# CREATE SINGLE ACTIVE SESSION
# =========================================================

def _start_database_session(
    username: str,
):

    # -----------------------------------------------------
    # If another active browser/tab already owns this
    # username, do NOT allow another login.
    # -----------------------------------------------------

    if _account_has_live_session(
        username
    ):

        return False, "already_logged_in"

    token = secrets.token_urlsafe(
        32
    )

    try:

        response = create_user_session(
            username,
            token,
        )

    except Exception as exc:

        return False, str(exc)

    if not response:

        return False, "session_not_created"

    st.session_state.session_token = (
        token
    )

    now = datetime.now(
        timezone.utc
    )

    st.session_state.session_started_at = (
        now.isoformat()
    )

    # Load current user settings.
    try:

        record = get_user_session(
            username
        )

        if record:

            st.session_state.search_delay_seconds = max(
                0,
                int(
                    record.get(
                        "search_delay_seconds",
                        1,
                    )
                ),
            )

            st.session_state.session_timeout_minutes = max(
                1,
                int(
                    record.get(
                        "session_timeout_minutes",
                        60,
                    )
                ),
            )

            st.session_state.session_started_at = (
                record.get(
                    "session_started_at"
                )
                or st.session_state.session_started_at
            )

    except Exception:
        pass

    return True, "ok"


# =========================================================
# LOGOUT / CLEAR LOCAL AUTH
# =========================================================

def _logout_everywhere():

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
        or ""
    )

    if username:

        try:

            clear_user_session(
                username,
                token or None,
            )

        except Exception:
            pass

    try:

        log_action(
            "LOGOUT",
            details="User signed out",
        )

    except Exception:
        pass

    logout_user()

    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.session_token = ""
    st.session_state.session_started_at = None

    st.session_state.running = False


# =========================================================
# VALIDATE CURRENT SESSION
# =========================================================

def _validate_current_session():

    if not st.session_state.get(
        "authenticated",
        False,
    ):
        return False

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
        or ""
    )

    if not username or not token:
        return False

    try:

        valid, reason = (
            validate_user_session(
                username,
                token,
            )
        )

    except Exception:

        # Do not immediately log out on a temporary
        # database problem if the local session exists.
        return True

    if valid:
        return True

    # Another tab logged in, account disabled,
    # or session expired.
    if reason == "session_replaced":

        st.session_state.authenticated = False

        st.session_state.running = False

        st.error(
            "🔒 This session was signed out because "
            "the same account was opened in another tab "
            "or browser."
        )

    elif reason == "expired":

        st.session_state.authenticated = False

        st.session_state.running = False

        st.error(
            "⏰ Your session has expired. "
            "Please sign in again."
        )

    elif reason == "inactive":

        st.session_state.authenticated = False

        st.session_state.running = False

        st.error(
            "This account has been disabled."
        )

    else:

        st.session_state.authenticated = False

        st.session_state.running = False

    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.session_token = ""
    st.session_state.session_started_at = None

    return False


# =========================================================
# LOGIN PAGE
# =========================================================

def _require_app_login() -> bool:

    _init_auth_state()

    # -----------------------------------------------------
    # Existing session
    # -----------------------------------------------------

    if st.session_state.get(
        "authenticated",
        False,
    ):

        if _validate_current_session():
            return True

        st.rerun()

    # -----------------------------------------------------
    # Login CSS
    # -----------------------------------------------------

    st.markdown(
        """
        <style>

        .login-title {
            text-align:center;
            font-size:2.7rem;
            font-weight:850;
            margin-top:8vh;
            color:#ffffff;
            letter-spacing:-0.04em;
        }

        .login-subtitle {
            text-align:center;
            color:#9da6c0;
            margin-bottom:28px;
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
            "## 🔐",
        )

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

        if _auth_locked():

            st.error(
                "🔒 Too many failed login attempts."
            )

            st.warning(
                f"Try again in {_lock_seconds()} seconds."
            )

            st.stop()

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

            submitted = st.form_submit_button(
                "🔐 Sign In",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            clean_username = (
                username.strip()
            )

            if (
                not clean_username
                or not password
            ):

                _failed_login()

                st.error(
                    "Username and password are required."
                )

                st.stop()

            # -------------------------------------------------
            # ADMIN LOGIN
            # -------------------------------------------------

            if _admin_login(
                clean_username,
                password,
            ):

                # Ensure the secret-based admin also has
                # a database session record so the same
                # single-session protection applies.
                try:

                    admin_record = get_user(
                        clean_username
                    )

                    if not admin_record:

                        admin_hash = (
                            _secret(
                                "ADMIN_PASSWORD_HASH"
                            )
                        )

                        if len(admin_hash) != 64:

                            admin_hash = hash_password(
                                _secret(
                                    "ADMIN_PASSWORD"
                                )
                                or password
                            )

                        create_user_record(
                            clean_username,
                            admin_hash,
                            "admin",
                        )

                except Exception as exc:

                    st.error(
                        "Unable to initialize administrator "
                        f"session: {exc}"
                    )

                    st.stop()

                ok, reason = (
                    _start_database_session(
                        clean_username
                    )
                )

                if not ok:

                    if reason == "already_logged_in":

                        st.error(
                            "🔒 This account is already "
                            "logged in on another tab or browser."
                        )

                        st.caption(
                            "Sign out from the other session "
                            "before signing in here."
                        )

                    else:

                        st.error(
                            "Unable to create the secure "
                            f"session: {reason}"
                        )

                    st.stop()

                st.session_state.authenticated = True
                st.session_state.username = (
                    clean_username
                )
                st.session_state.role = "admin"

                st.session_state.login_attempts = 0
                st.session_state.login_locked_until = 0.0

                try:

                    log_action(
                        "LOGIN",
                        details=(
                            "Administrator signed in"
                        ),
                    )

                except Exception:
                    pass

                st.rerun()

            # -------------------------------------------------
            # STANDARD USER
            # -------------------------------------------------

            record, status = (
                _database_login(
                    clean_username,
                    password,
                )
            )

            if (
                status == "ok"
                and record
            ):

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

                ok, reason = (
                    _start_database_session(
                        clean_username
                    )
                )

                if not ok:

                    if reason == "already_logged_in":

                        st.error(
                            "🔒 This account is already "
                            "logged in on another tab or browser."
                        )

                        st.caption(
                            "Only one active session is "
                            "allowed for each username."
                        )

                    else:

                        st.error(
                            "Unable to create secure session: "
                            f"{reason}"
                        )

                    st.stop()

                st.session_state.authenticated = True
                st.session_state.username = (
                    clean_username
                )
                st.session_state.role = role

                st.session_state.login_attempts = 0
                st.session_state.login_locked_until = 0.0

                try:

                    log_action(
                        "LOGIN",
                        details=(
                            f"{role} signed in"
                        ),
                    )

                except Exception:
                    pass

                st.rerun()

            # -------------------------------------------------
            # LOGIN FAILURE
            # -------------------------------------------------

            if status == "inactive":

                _failed_login()

                st.error(
                    "This account is inactive. "
                    "Contact an administrator."
                )

            elif status == "database_error":

                _failed_login()

                st.error(
                    "Unable to contact the user database. "
                    "Check the Supabase configuration."
                )

            else:

                _failed_login()

                st.error(
                    "Invalid username or password."
                )

                if not _auth_locked():

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


# =========================================================
# REQUIRE LOGIN
# =========================================================

_require_app_login()


# =========================================================
# LOAD CURRENT USER SETTINGS
# =========================================================

current_session = _get_current_session()

if current_session:

    st.session_state.search_delay_seconds = max(
        0,
        int(
            current_session.get(
                "search_delay_seconds",
                1,
            )
        ),
    )

    st.session_state.session_timeout_minutes = max(
        1,
        int(
            current_session.get(
                "session_timeout_minutes",
                60,
            )
        ),
    )

    if current_session.get(
        "session_started_at"
    ):

        st.session_state.session_started_at = (
            current_session.get(
                "session_started_at"
            )
        )


# =========================================================
# LIVE SESSION TIMER
# =========================================================

def _format_remaining(seconds: int) -> str:

    seconds = max(
        0,
        int(seconds),
    )

    minutes, secs = divmod(
        seconds,
        60,
    )

    hours, minutes = divmod(
        minutes,
        60,
    )

    if hours:

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{secs:02d}"
    )


def _seconds_until_expiry() -> int:

    started_at = _parse_datetime(
        st.session_state.get(
            "session_started_at"
        )
    )

    if not started_at:

        return 0

    timeout_minutes = max(
        1,
        int(
            st.session_state.get(
                "session_timeout_minutes",
                60,
            )
        ),
    )

    expires_at = (
        started_at
        + timedelta(
            minutes=timeout_minutes
        )
    )

    return max(
        0,
        int(
            (
                expires_at
                - datetime.now(timezone.utc)
            ).total_seconds()
        ),
    )


# =========================================================
# TIMER FRAGMENT
# =========================================================

@st.fragment(run_every=1)
def _session_timer():

    remaining = _seconds_until_expiry()

    timer_col, logout_col = st.columns(
        [5, 1]
    )

    with timer_col:

        if remaining <= 0:

            st.error(
                "⏰ Session expired"
            )

            st.session_state.running = False

        elif remaining <= 60:

            st.error(
                f"⏳ Session time left: "
                f"**{_format_remaining(remaining)}**"
            )

        else:

            st.markdown(
                f"""
                <div style="
                    color:#ff5268;
                    font-size:0.86rem;
                    font-weight:750;
                    text-align:right;
                    padding:7px 8px;
                ">
                    ⏳ { _format_remaining(remaining) }
                </div>
                """,
                unsafe_allow_html=True,
            )

    with logout_col:

        if st.button(
            "Logout",
            key="live_logout_button",
            use_container_width=True,
        ):

            _logout_everywhere()

            st.rerun()

    if remaining <= 0:

        _logout_everywhere()

        st.rerun()


_session_timer()


# =========================================================
# SEARCH STATE
# =========================================================

search_defaults = {

    "running": False,

    "start_mc": "",

    "current_mc": None,

    "last_searched_mc": None,

    "results": [],

    "searched_count": 0,

    "active_page": "Search",
}

for key, value in search_defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {

    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(80,110,255,.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(180,70,255,.16),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(40,120,255,.10),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #05060a,
            #0b0d14 45%,
            #05060a
        );

    color:#f5f7ff;
}

.block-container {

    max-width:1450px;

    padding-top:1.3rem;

    padding-bottom:4rem;
}

.glass-card {

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.105),
            rgba(255,255,255,.035)
        );

    border:
        1px solid
        rgba(255,255,255,.12);

    border-radius:28px;

    padding:28px;

    margin-bottom:20px;

    box-shadow:
        0 20px 70px
        rgba(0,0,0,.45),

        inset 0 1px 0
        rgba(255,255,255,.08);

    backdrop-filter:
        blur(25px)
        saturate(160%);
}

.hero-title {

    font-size:3rem;

    font-weight:800;

    letter-spacing:-.05em;

    background:
        linear-gradient(
            90deg,
            #fff,
            #b9c5ff,
            #fff
        );

    -webkit-background-clip:text;

    -webkit-text-fill-color:transparent;
}

.hero-subtitle {

    color:
        rgba(235,240,255,.62);

    font-size:1rem;

    margin-top:6px;
}

div[data-baseweb="input"] {

    background:
        rgba(255,255,255,.065)
        !important;

    border:
        1px solid
        rgba(255,255,255,.12)
        !important;

    border-radius:
        18px !important;
}

div[data-baseweb="input"]:focus-within {

    border-color:
        rgba(120,145,255,.85)
        !important;

    box-shadow:
        0 0 0 3px
        rgba(100,125,255,.12),

        0 0 30px
        rgba(80,100,255,.15);
}

input {

    color:white !important;
}

.stButton > button {

    min-height:50px;

    border-radius:
        18px !important;

    border:
        1px solid
        rgba(255,255,255,.14)
        !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.12),
            rgba(255,255,255,.045)
        ) !important;

    color:white !important;

    font-weight:700 !important;

    transition:
        transform .2s ease,
        box-shadow .2s ease;
}

.stButton > button:hover {

    transform:
        translateY(-2px)
        scale(1.015);

    box-shadow:
        0 12px 35px
        rgba(75,95,255,.28);
}

.admin-header {

    font-size:2rem;

    font-weight:800;
}

.admin-small {

    color:#9da6c0;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# TOP HEADER
# =========================================================

header_col1, header_col2 = st.columns(
    [5, 1]
)

with header_col1:

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-title">'
        '✦ MC Search'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-subtitle">'
        'FMCSA intelligence → DotSearch enrichment'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

with header_col2:

    st.write("")

    if st.button(
        "🚪 Sign Out",
        use_container_width=True,
    ):

        _logout_everywhere()

        st.rerun()


# =========================================================
# NAVIGATION
# =========================================================

if is_admin():

    nav1, nav2 = st.columns(2)

    with nav1:

        search_page = st.button(
            "🔎 MC Search",
            use_container_width=True,
        )

    with nav2:

        admin_page = st.button(
            "⚙️ Admin Panel",
            use_container_width=True,
        )

    if search_page:

        st.session_state.active_page = (
            "Search"
        )

    if admin_page:

        st.session_state.active_page = (
            "Admin"
        )

else:

    st.session_state.active_page = (
        "Search"
    )


# =========================================================
# ADMIN PANEL
# =========================================================

if (
    st.session_state.active_page
    == "Admin"
    and is_admin()
):

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="admin-header">'
        '⚙️ Admin Panel'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="admin-small">'
        'Manage users, security and audit activity.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

    tab_users, tab_security, tab_audit = st.tabs(
        [
            "👥 Users",
            "🛡️ Security",
            "📋 Audit Log",
        ]
    )

    # =====================================================
    # USERS
    # =====================================================

    with tab_users:

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "👥 User Management"
        )

        try:

            users = list_users()

            if users:

                users_df = pd.DataFrame(
                    users
                )

                display_columns = [
                    "username",
                    "role",
                    "active",
                    "search_delay_seconds",
                    "session_timeout_minutes",
                    "created_at",
                ]

                display_columns = [
                    column
                    for column in display_columns
                    if column in users_df.columns
                ]

                st.dataframe(
                    users_df[
                        display_columns
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No Supabase users found."
                )

        except Exception as exc:

            st.error(
                f"Unable to load users: {exc}"
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

        # =================================================
        # CREATE USER
        # =================================================

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "➕ Create User"
        )

        with st.form(
            "create_user_form"
        ):

            new_username = st.text_input(
                "Username",
                placeholder="username",
            )

            new_password = st.text_input(
                "Password",
                type="password",
                placeholder="Password",
            )

            new_role = st.selectbox(
                "Role",
                [
                    "standard_user",
                    "admin",
                ],
            )

            create_button = (
                st.form_submit_button(
                    "Create User",
                    use_container_width=True,
                )
            )

        if create_button:

            username_clean = (
                new_username.strip()
            )

            if not username_clean:

                st.error(
                    "Username is required."
                )

            elif len(new_password) < 8:

                st.error(
                    "Password must contain at least "
                    "8 characters."
                )

            else:

                try:

                    existing_users = (
                        list_users()
                    )

                    exists = any(
                        str(
                            u.get(
                                "username",
                                "",
                            )
                        ).lower()
                        == username_clean.lower()
                        for u in existing_users
                    )

                    if exists:

                        st.error(
                            "That username already exists."
                        )

                    else:

                        create_user_record(
                            username_clean,
                            hash_password(
                                new_password
                            ),
                            new_role,
                        )

                        log_action(
                            "CREATE_USER",
                            details=(
                                f"Created user "
                                f"{username_clean} "
                                f"with role {new_role}"
                            ),
                        )

                        st.success(
                            "✓ User created."
                        )

                        st.rerun()

                except Exception as exc:

                    st.error(
                        f"Unable to create user: {exc}"
                    )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

        # =================================================
        # USER ACTIONS
        # =================================================

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "🔧 User Actions"
        )

        try:

            users = list_users()

            editable_users = [
                str(
                    u.get(
                        "username",
                        "",
                    )
                )
                for u in users
                if str(
                    u.get(
                        "username",
                        "",
                    )
                )
                != st.session_state.username
            ]

            if editable_users:

                selected_user = st.selectbox(
                    "Select user",
                    editable_users,
                    key="admin_selected_user",
                )

                selected_record = next(
                    (
                        u
                        for u in users
                        if str(
                            u.get(
                                "username",
                                "",
                            )
                        )
                        == selected_user
                    ),
                    None,
                )

                if selected_record:

                    current_active = bool(
                        selected_record.get(
                            "active",
                            True,
                        )
                    )

                    current_delay = max(
                        0,
                        int(
                            selected_record.get(
                                "search_delay_seconds",
                                1,
                            )
                        ),
                    )

                    current_timeout = max(
                        1,
                        int(
                            selected_record.get(
                                "session_timeout_minutes",
                                60,
                            )
                        ),
                    )

                    if current_active:

                        st.success(
                            "Current status: ACTIVE"
                        )

                    else:

                        st.error(
                            "Current status: INACTIVE"
                        )

                    # -------------------------------------
                    # SETTINGS
                    # -------------------------------------

                    st.markdown(
                        "#### ⚙ Search & Session Settings"
                    )

                    setting_col1, setting_col2 = (
                        st.columns(2)
                    )

                    with setting_col1:

                        delay_value = st.number_input(
                            "Search delay (seconds)",
                            min_value=0,
                            max_value=3600,
                            value=current_delay,
                            step=1,
                            key=(
                                f"delay_"
                                f"{selected_user}"
                            ),
                            help=(
                                "Delay between sequential "
                                "MC searches."
                            ),
                        )

                    with setting_col2:

                        timeout_value = st.number_input(
                            "Session timeout (minutes)",
                            min_value=1,
                            max_value=10080,
                            value=current_timeout,
                            step=1,
                            key=(
                                f"timeout_"
                                f"{selected_user}"
                            ),
                            help=(
                                "Maximum login session "
                                "duration."
                            ),
                        )

                    if st.button(
                        "💾 Save Search & Session Settings",
                        use_container_width=True,
                        key=(
                            f"save_settings_"
                            f"{selected_user}"
                        ),
                    ):

                        try:

                            update_user_settings(
                                selected_user,
                                search_delay_seconds=int(
                                    delay_value
                                ),
                                session_timeout_minutes=int(
                                    timeout_value
                                ),
                            )

                            log_action(
                                "USER_SETTINGS_CHANGE",
                                details=(
                                    f"{selected_user}: "
                                    f"delay={delay_value}s, "
                                    f"timeout={timeout_value}m"
                                ),
                            )

                            st.success(
                                "✓ Settings saved."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                "Unable to save settings: "
                                f"{exc}"
                            )

                    st.divider()

                    # -------------------------------------
                    # STATUS / PASSWORD
                    # -------------------------------------

                    action_col1, action_col2 = (
                        st.columns(2)
                    )

                    with action_col1:

                        if st.button(
                            (
                                "🔴 Disable User"
                                if current_active
                                else "🟢 Enable User"
                            ),
                            use_container_width=True,
                            key="toggle_user_status",
                        ):

                            new_active = (
                                not current_active
                            )

                            try:

                                update_user(
                                    selected_user,
                                    {
                                        "active":
                                            new_active
                                    },
                                )

                                log_action(
                                    "USER_STATUS_CHANGE",
                                    details=(
                                        f"{selected_user} "
                                        f"active={new_active}"
                                    ),
                                )

                                st.success(
                                    "User status updated."
                                )

                                st.rerun()

                            except Exception as exc:

                                st.error(
                                    "Unable to update user: "
                                    f"{exc}"
                                )

                    with action_col2:

                        reset_password = (
                            st.text_input(
                                "New password",
                                type="password",
                                key="admin_reset_password",
                            )
                        )

                        if st.button(
                            "🔑 Reset Password",
                            use_container_width=True,
                            key="reset_user_password",
                        ):

                            if len(
                                reset_password
                            ) < 8:

                                st.error(
                                    "Password must be at least "
                                    "8 characters."
                                )

                            else:

                                try:

                                    update_user(
                                        selected_user,
                                        {
                                            "password_hash":
                                                hash_password(
                                                    reset_password
                                                )
                                        },
                                    )

                                    # Reset password should also
                                    # destroy any existing session.
                                    clear_user_session(
                                        selected_user
                                    )

                                    log_action(
                                        "PASSWORD_RESET",
                                        details=(
                                            f"Password reset "
                                            f"for {selected_user}"
                                        ),
                                    )

                                    st.success(
                                        "Password reset successfully. "
                                        "Existing session was signed out."
                                    )

                                except Exception as exc:

                                    st.error(
                                        "Unable to reset password: "
                                        f"{exc}"
                                    )

            else:

                st.info(
                    "No other users available."
                )

        except Exception as exc:

            st.error(
                f"Unable to manage users: {exc}"
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

    # =====================================================
    # SECURITY
    # =====================================================

    with tab_security:

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "🛡️ Security"
        )

        st.metric(
            "Current User",
            st.session_state.username,
        )

        st.metric(
            "Role",
            st.session_state.role.upper(),
        )

        st.success(
            "✓ Authenticated administrator session"
        )

        st.caption(
            "Each username has one active database session. "
            "A replacement login invalidates the previous session."
        )

        st.caption(
            "Passwords are stored as SHA-256 hashes. "
            "The application does not display stored passwords."
        )

        st.markdown(
            "#### Current Session"
        )

        st.write(
            f"Search delay: "
            f"{st.session_state.search_delay_seconds} second(s)"
        )

        st.write(
            f"Session timeout: "
            f"{st.session_state.session_timeout_minutes} minute(s)"
        )

        if st.button(
            "🧹 Clean Audit Logs Older Than 90 Days",
            use_container_width=True,
        ):

            cleanup_audit_logs()

            log_action(
                "AUDIT_CLEANUP",
                details=(
                    "Removed audit records older than 90 days"
                ),
            )

            st.success(
                "Audit cleanup completed."
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

    # =====================================================
    # AUDIT
    # =====================================================

    with tab_audit:

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "📋 Audit Log"
        )

        try:

            audit_df = audit_dataframe()

            if audit_df.empty:

                st.info(
                    "No audit events found."
                )

            else:

                st.dataframe(
                    audit_df,
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as exc:

            st.error(
                f"Unable to load audit log: {exc}"
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

    st.stop()


# =========================================================
# SEARCH PAGE
# =========================================================

st.markdown(
    '<div class="glass-card">',
    unsafe_allow_html=True,
)

st.markdown(
    "### 🎯 Search Control"
)


# =========================================================
# START MC
# =========================================================

start_value = (
    st.session_state.start_mc
)

start_input = st.text_input(
    "Start MC",
    value=start_value,
    placeholder="Example: 1800000",
    disabled=st.session_state.running,
    key="start_mc_input",
)

st.caption(
    "Enter the starting MC. The app searches sequentially "
    "one MC at a time."
)

st.caption(
    f"Current search delay: "
    f"{st.session_state.search_delay_seconds} second(s)"
)


# =========================================================
# CURRENT MC
# =========================================================

if st.session_state.running:

    display_mc = (
        st.session_state.current_mc
    )

    display_hint = (
        "Search running • next MC will update automatically"
    )

elif (
    st.session_state.last_searched_mc
    is not None
):

    display_mc = (
        st.session_state.last_searched_mc
    )

    display_hint = (
        "Search stopped • press START to continue"
    )

elif st.session_state.start_mc:

    display_mc = (
        st.session_state.start_mc
    )

    display_hint = (
        "Ready to search"
    )

else:

    display_mc = "—"

    display_hint = (
        "Enter a starting MC"
    )


# =========================================================
# CURRENT MC DISPLAY
# =========================================================

st.markdown(
    "#### Current MC Number"
)

if display_mc != "—":

    try:

        formatted_mc = (
            f"{int(display_mc):,}"
        )

    except Exception:

        formatted_mc = str(
            display_mc
        )

else:

    formatted_mc = "—"


st.markdown(
    f"# {formatted_mc}"
)

st.caption(
    display_hint
)


# =========================================================
# BUTTONS
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:

    start_button = st.button(
        "▶ Start Search",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running,
    )

with col2:

    stop_button = st.button(
        "■ Stop",
        use_container_width=True,
        disabled=not st.session_state.running,
    )

with col3:

    clear_button = st.button(
        "◉ Clear History",
        use_container_width=True,
    )


st.markdown(
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# CLEAR HISTORY
# =========================================================

if clear_button:

    st.session_state.running = False

    st.session_state.start_mc = ""

    st.session_state.current_mc = None

    st.session_state.last_searched_mc = None

    st.session_state.results = []

    st.session_state.searched_count = 0

    log_action(
        "CLEAR_HISTORY",
        details="MC search history cleared",
    )

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    if (
        st.session_state.current_mc
        is not None
    ):

        st.session_state.last_searched_mc = (
            int(
                st.session_state.current_mc
            ) - 1
        )

    st.session_state.running = False

    st.session_state.current_mc = None

    log_action(
        "SEARCH_STOPPED",
        mc_number=str(
            st.session_state.last_searched_mc
            or ""
        ),
        details="Sequential MC search stopped",
    )

    st.rerun()


# =========================================================
# START
# =========================================================

if start_button:

    cleaned = (
        str(start_input)
        .strip()
        .replace("MC", "")
        .replace("mc", "")
        .strip()
    )

    if not cleaned.isdigit():

        st.error(
            "Enter a valid numeric MC number."
        )

        st.stop()

    start_number = int(
        cleaned
    )

    st.session_state.start_mc = (
        str(start_number)
    )

    st.session_state.current_mc = (
        start_number
    )

    st.session_state.last_searched_mc = (
        None
    )

    st.session_state.running = True

    log_action(
        "SEARCH_STARTED",
        mc_number=str(
            start_number
        ),
        details=(
            "Sequential MC search started"
        ),
    )

    st.rerun()


# =========================================================
# LIVE SEARCH STATUS
# =========================================================

if st.session_state.running:

    current = int(
        st.session_state.current_mc
    )

    st.info(
        f"🟢 Searching MC {current:,}\n\n"
        "Searching sequential MC numbers automatically..."
    )

elif (
    st.session_state.searched_count > 0
):

    st.success(
        "✓ Search stopped"
    )

    st.caption(
        f"{st.session_state.searched_count:,} "
        "MC number(s) processed. "
        "Results are preserved until Clear History."
    )


# =========================================================
# AUTOMATIC SEARCH
# =========================================================

if st.session_state.running:

    current_mc = int(
        st.session_state.current_mc
    )

    try:

        result = search_one(
            str(current_mc)
        )

    except Exception as exc:

        result = {
            "MC Number": str(current_mc),
            "Owner": "Not available",
            "Carrier/Broker Name": "",
            "Broker/Carrier": "",
            "Operating Status": "",
            "Number": "Not available",
            "Email Address": "Not available",
            "Location": "Not available",
            "_error": str(exc),
        }

    st.session_state.results.append(
        result
    )

    st.session_state.searched_count += 1

    st.session_state.last_searched_mc = (
        current_mc
    )

    st.session_state.current_mc = (
        current_mc + 1
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # This is now the user's saved database delay.
    # -----------------------------------------------------

    delay_seconds = max(
        0,
        int(
            st.session_state.get(
                "search_delay_seconds",
                1,
            )
        ),
    )

    if delay_seconds > 0:

        time.sleep(
            delay_seconds
        )

    st.rerun()


# =========================================================
# RESULTS
# =========================================================

if st.session_state.results:

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 📊 Search Results"
    )

    rows = []

    errors = []

    for result in (
        st.session_state.results
    ):

        rows.append(
            {
                "MC Number": result.get(
                    "MC Number",
                    "",
                ),

                "Owner": result.get(
                    "Owner",
                    "Not available",
                ),

                "Carrier/Broker Name": result.get(
                    "Carrier/Broker Name",
                    "",
                ),

                "Broker/Carrier": result.get(
                    "Broker/Carrier",
                    "",
                ),

                "Operating Status": result.get(
                    "Operating Status",
                    "",
                ),

                "Number": result.get(
                    "Number",
                    "Not available",
                ),

                "Email Address": result.get(
                    "Email Address",
                    "Not available",
                ),

                "Location": result.get(
                    "Location",
                    "Not available",
                ),
            }
        )

        if result.get("_error"):

            errors.append(
                result["_error"]
            )

    df = pd.DataFrame(
        rows,
        columns=[
            "MC Number",
            "Owner",
            "Carrier/Broker Name",
            "Broker/Carrier",
            "Operating Status",
            "Number",
            "Email Address",
            "Location",
        ],
    )

    # =====================================================
    # FILTERS
    # =====================================================

    st.markdown(
        "#### 🔎 Filters"
    )

    filter_col1, filter_col2 = (
        st.columns(2)
    )

    with filter_col1:

        status_filter = st.selectbox(
            "Operating Status",
            [
                "ALL",
                "ACTIVE",
                "INACTIVE",
            ],
            key="status_filter",
        )

    with filter_col2:

        type_filter = st.selectbox(
            "Broker / Carrier",
            [
                "ALL",
                "CARRIER",
                "BROKER",
            ],
            key="type_filter",
        )

    filtered_df = df.copy()

    if status_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df[
                "Operating Status"
            ]
            .astype(str)
            .str.upper()
            == status_filter
        ]

    if type_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ]
            .astype(str)
            .str.upper()
            == type_filter
        ]

    st.caption(
        f"Showing {len(filtered_df):,} "
        f"of {len(df):,} result(s)"
    )

    # =====================================================
    # METRICS
    # =====================================================

    active_count = int(
        (
            df["Operating Status"]
            .astype(str)
            .str.upper()
            == "ACTIVE"
        ).sum()
    )

    inactive_count = int(
        (
            df["Operating Status"]
            .astype(str)
            .str.upper()
            == "INACTIVE"
        ).sum()
    )

    carrier_count = int(
        (
            df["Broker/Carrier"]
            .astype(str)
            .str.upper()
            == "CARRIER"
        ).sum()
    )

    broker_count = int(
        (
            df["Broker/Carrier"]
            .astype(str)
            .str.upper()
            == "BROKER"
        ).sum()
    )

    c1, c2, c3, c4 = (
        st.columns(4)
    )

    c1.metric(
        "Searched",
        len(df),
    )

    c2.metric(
        "Active",
        active_count,
    )

    c3.metric(
        "Carriers",
        carrier_count,
    )

    c4.metric(
        "Brokers",
        broker_count,
    )

    # =====================================================
    # COLORS
    # =====================================================

    def color_status(value):

        value = str(value).upper()

        if value == "ACTIVE":

            return (
                "color:#39ff88;"
                "font-weight:700;"
            )

        if value == "INACTIVE":

            return (
                "color:#ff4d67;"
                "font-weight:700;"
            )

        return ""

    def color_type(value):

        value = str(value).upper()

        if value == "BROKER":

            return (
                "color:#c084fc;"
                "font-weight:700;"
            )

        if value == "CARRIER":

            return (
                "color:#60a5fa;"
                "font-weight:700;"
            )

        return ""

    styled_df = (
        filtered_df.style
        .map(
            color_status,
            subset=[
                "Operating Status"
            ],
        )
        .map(
            color_type,
            subset=[
                "Broker/Carrier"
            ],
        )
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

    # =====================================================
    # EXPORT
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### ⬇ Export Filtered Results"
    )

    download_col1, download_col2 = (
        st.columns(2)
    )

    csv_data = (
        filtered_df
        .to_csv(index=False)
        .encode("utf-8")
    )

    with download_col1:

        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name="mc_filtered_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl",
    ) as writer:

        filtered_df.to_excel(
            writer,
            index=False,
            sheet_name="MC Results",
        )

    with download_col2:

        st.download_button(
            "Download Excel",
            data=excel_buffer.getvalue(),
            file_name="mc_filtered_results.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

    # =====================================================
    # SEARCH ERRORS
    # =====================================================

    if errors:

        with st.expander(
            "⚠ Search messages"
        ):

            for error in errors:

                st.write(error)
