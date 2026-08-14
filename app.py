import io
import time
import hmac
import secrets

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
)
from src.audit import (
    log_action,
    audit_dataframe,
    cleanup_audit_logs,
)


# =========================================================
# APP-LEVEL AUTHENTICATION
# =========================================================
#
# This login layer intentionally lives in app.py so the UI and
# authentication state are controlled in one place. It supports:
#   1. Admin credentials from Streamlit Secrets
#   2. Standard users stored in Supabase
#   3. Active/inactive user status
#   4. SHA-256 password hashes for database users
#   5. A temporary lockout after repeated failures
#
# It also avoids writing to Streamlit widget keys after the
# widgets have been created, which was the source of the earlier
# StreamlitAPIException errors.

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300


def _init_auth_state():
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


def _secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return str(value).strip()


def _admin_login(username: str, password: str) -> bool:
    configured_username = _secret("ADMIN_USERNAME")

    if not configured_username:
        return False

    if username.strip() != configured_username:
        return False

    stored_hash = _secret("ADMIN_PASSWORD_HASH")

    # Preferred format: SHA-256 hex digest.
    if len(stored_hash) == 64:
        supplied_hash = hash_password(password)
        if hmac.compare_digest(
            supplied_hash.lower(),
            stored_hash.lower(),
        ):
            return True

    # Compatibility fallback: ADMIN_PASSWORD can be used while
    # migrating an existing deployment.
    stored_password = _secret("ADMIN_PASSWORD")
    if stored_password and hmac.compare_digest(
        password,
        stored_password,
    ):
        return True

    # Compatibility for the old deployment where a value was
    # mistakenly placed in ADMIN_PASSWORD_HASH as plain text.
    # Replace that secret with a real SHA-256 hash after login.
    if stored_hash and len(stored_hash) != 64:
        if hmac.compare_digest(password, stored_hash):
            return True

    return False


def _database_login(username: str, password: str):
    try:
        record = get_user(username.strip())
    except Exception:
        return None, "database_error"

    if not record:
        return False, "invalid"

    if not bool(record.get("active", True)):
        return False, "inactive"

    stored_hash = str(record.get("password_hash", "")).strip()
    if not stored_hash:
        return False, "invalid"

    supplied_hash = hash_password(password)

    if hmac.compare_digest(
        supplied_hash.lower(),
        stored_hash.lower(),
    ):
        return record, "ok"

    return False, "invalid"


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
            time.time() + LOGIN_LOCKOUT_SECONDS
        )
    else:
        st.session_state.login_attempts = attempts


def _set_authenticated(username: str, role: str):
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.role = role.lower()
    st.session_state.session_token = secrets.token_urlsafe(32)
    st.session_state.login_attempts = 0
    st.session_state.login_locked_until = 0.0


def _require_app_login() -> bool:
    _init_auth_state()

    if (
        st.session_state.get("authenticated", False)
        and st.session_state.get("username", "")
        and st.session_state.get("session_token", "")
    ):
        return True

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
            background: linear-gradient(135deg, rgba(255,255,255,.11), rgba(255,255,255,.035));
            border: 1px solid rgba(255,255,255,.14);
            box-shadow: 0 30px 100px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.08);
            backdrop-filter: blur(30px);
            text-align: center;
        }
        .login-lock {
            font-size: 3rem;
            line-height: 1;
            margin-bottom: 12px;
            filter: drop-shadow(0 0 18px rgba(120,140,255,.7));
        }
        .login-title {
            font-size: 2.4rem;
            font-weight: 850;
            color: #fff;
            letter-spacing: -.04em;
        }
        .login-subtitle {
            color: #9da6c0;
            margin-top: 7px;
        }
        </style>

        <div class="login-wrap">
            <div class="login-card">
                <div class="login-lock">🔐</div>
                <div class="login-title">✦ MC Search</div>
                <div class="login-subtitle">Secure administrator / user access</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if _auth_locked():
        st.error("🔒 Too many failed login attempts.")
        st.warning(
            f"Try again in {_lock_seconds()} seconds."
        )
        st.stop()

    with st.form("mc_login_form", clear_on_submit=False):
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

    if submitted:
        clean_username = username.strip()

        if not clean_username or not password:
            _failed_login()
            st.error("Username and password are required.")
            st.stop()

        # Admin is checked first.
        if _admin_login(clean_username, password):
            _set_authenticated(clean_username, "admin")
            log_action(
                "LOGIN",
                details="Administrator signed in",
            )
            st.rerun()

        # Then check normal Supabase users.
        record, status = _database_login(
            clean_username,
            password,
        )

        if status == "ok" and record:
            role = str(record.get("role", "user")).lower()
            if role not in {"user", "admin"}:
                role = "user"

            _set_authenticated(clean_username, role)
            log_action(
                "LOGIN",
                details=f"{role.title()} user signed in",
            )
            st.rerun()

        if status == "inactive":
            _failed_login()
            st.error("This account is inactive. Contact an administrator.")
        elif status == "database_error":
            _failed_login()
            st.error(
                "Unable to contact the user database. "
                "Check the Supabase configuration."
            )
        else:
            _failed_login()
            st.error("Invalid username or password.")

            if not _auth_locked():
                remaining = MAX_LOGIN_ATTEMPTS - int(
                    st.session_state.get("login_attempts", 0)
                )
                if remaining > 0:
                    st.caption(
                        f"{remaining} attempt(s) remaining."
                    )

    st.stop()


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
# AUTH
# =========================================================

_require_app_login()


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "running": False,
    "start_mc": "",
    "current_mc": None,
    "last_searched_mc": None,
    "results": [],
    "searched_count": 0,
    "active_page": "Search",
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# CSS
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
    padding-top:2rem;
    padding-bottom:4rem;
}

.glass-card {
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.105),
            rgba(255,255,255,.035)
        );

    border:1px solid rgba(255,255,255,.12);
    border-radius:28px;
    padding:28px;
    margin-bottom:20px;

    box-shadow:
        0 20px 70px rgba(0,0,0,.45),
        inset 0 1px 0 rgba(255,255,255,.08);

    backdrop-filter:blur(25px) saturate(160%);
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
    color:rgba(235,240,255,.62);
    font-size:1rem;
    margin-top:6px;
}

div[data-baseweb="input"] {
    background:rgba(255,255,255,.065)!important;
    border:1px solid rgba(255,255,255,.12)!important;
    border-radius:18px!important;
}

div[data-baseweb="input"]:focus-within {
    border-color:
        rgba(120,145,255,.85)!important;

    box-shadow:
        0 0 0 3px rgba(100,125,255,.12),
        0 0 30px rgba(80,100,255,.15);
}

input {
    color:white!important;
}

.stButton > button {
    min-height:50px;
    border-radius:18px!important;

    border:
        1px solid rgba(255,255,255,.14)!important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.12),
            rgba(255,255,255,.045)
        )!important;

    color:white!important;
    font-weight:700!important;

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

.current-mc-card {
    text-align:center;
    padding:25px 20px;
    margin-top:20px;
    border-radius:24px;

    background:
        linear-gradient(
            135deg,
            rgba(90,110,255,.13),
            rgba(160,70,255,.08)
        );

    border:
        1px solid rgba(130,150,255,.18);
}

.current-label {
    color:#9da6c0;
    font-size:.9rem;
    font-weight:600;
    text-transform:uppercase;
    letter-spacing:.08em;
}

.current-number {
    font-size:2.7rem;
    font-weight:800;
    color:white;
    margin-top:5px;
}

.current-hint {
    color:#8993ad;
    font-size:.85rem;
}

.live-dot {
    display:inline-block;
    width:10px;
    height:10px;
    border-radius:50%;
    background:#36ff8a;

    box-shadow:
        0 0 8px #36ff8a,
        0 0 20px #36ff8a;

    animation:pulse 1.4s infinite;
    margin-right:8px;
}

@keyframes pulse {

    0% {
        transform:scale(.85);
        opacity:.6;
    }

    50% {
        transform:scale(1.2);
        opacity:1;
    }

    100% {
        transform:scale(.85);
        opacity:.6;
    }
}

.badge {
    display:inline-block;
    padding:9px 15px;
    margin:4px 6px 10px 0;
    border-radius:999px;
    font-weight:700;
}

.badge-active {
    color:#58ff9a;
    background:rgba(40,255,130,.10);
    border:1px solid rgba(60,255,145,.25);
}

.badge-inactive {
    color:#ff667d;
    background:rgba(255,70,100,.10);
    border:1px solid rgba(255,80,105,.22);
}

.badge-carrier {
    color:#66aaff;
    background:rgba(70,130,255,.10);
    border:1px solid rgba(80,140,255,.22);
}

.badge-broker {
    color:#d18aff;
    background:rgba(180,80,255,.10);
    border:1px solid rgba(190,90,255,.22);
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
        """
<div class="glass-card">

<div class="hero-title">
    ✦ MC Search
</div>

<div class="hero-subtitle">
    FMCSA intelligence → DotSearch enrichment
</div>

</div>
""",
        unsafe_allow_html=True,
    )


with header_col2:

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    if st.button(
        "🚪 Sign Out",
        use_container_width=True,
    ):

        log_action(
            "LOGOUT",
            details="User signed out",
        )

        logout_user()
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
        st.session_state.active_page = "Search"

    if admin_page:
        st.session_state.active_page = "Admin"

else:

    st.session_state.active_page = "Search"


# =========================================================
# ADMIN PANEL
# =========================================================

if (
    st.session_state.active_page == "Admin"
    and is_admin()
):

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="admin-header">
    ⚙️ Admin Panel
</div>

<div class="admin-small">
    Manage users, security and audit activity.
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


    # =====================================================
    # ADMIN TABS
    # =====================================================

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

        st.subheader("👥 User Management")

        try:

            users = list_users()

            if users:

                users_df = pd.DataFrame(users)

                st.dataframe(
                    users_df,
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

        st.markdown("</div>", unsafe_allow_html=True)


        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.subheader("➕ Create User")

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
                    "user",
                    "admin",
                ],
            )

            create_button = st.form_submit_button(
                "Create User",
                use_container_width=True,
            )

        if create_button:

            username_clean = (
                new_username
                .strip()
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

        st.markdown("</div>", unsafe_allow_html=True)


        # -------------------------------------------------
        # USER ACTIONS
        # -------------------------------------------------

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.subheader("🔧 User Actions")

        try:

            users = list_users()

            usernames = [
                str(
                    u.get(
                        "username",
                        "",
                    )
                )
                for u in users
            ]

            editable_users = [
                u
                for u in usernames
                if u != st.session_state.username
            ]

            if editable_users:

                selected_user = st.selectbox(
                    "Select user",
                    editable_users,
                    key="admin_selected_user",
                )

                action_col1, action_col2 = st.columns(2)

                with action_col1:

                    if st.button(
                        "🔄 Toggle Active",
                        use_container_width=True,
                    ):

                        selected_record = next(
                            (
                                u
                                for u in users
                                if u.get(
                                    "username"
                                )
                                == selected_user
                            ),
                            None,
                        )

                        if selected_record:

                            new_active = not bool(
                                selected_record.get(
                                    "active",
                                    True,
                                )
                            )

                            update_user(
                                selected_user,
                                {
                                    "active": new_active
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

                with action_col2:

                    reset_password = st.text_input(
                        "New password",
                        type="password",
                        key="admin_reset_password",
                    )

                    if st.button(
                        "🔑 Reset Password",
                        use_container_width=True,
                    ):

                        if len(
                            reset_password
                        ) < 8:

                            st.error(
                                "Password must be at least "
                                "8 characters."
                            )

                        else:

                            update_user(
                                selected_user,
                                {
                                    "password_hash":
                                        hash_password(
                                            reset_password
                                        )
                                },
                            )

                            log_action(
                                "PASSWORD_RESET",
                                details=(
                                    f"Password reset "
                                    f"for {selected_user}"
                                ),
                            )

                            st.success(
                                "Password reset successfully."
                            )

            else:

                st.info(
                    "No other users available."
                )

        except Exception as exc:

            st.error(
                f"Unable to manage users: {exc}"
            )

        st.markdown("</div>", unsafe_allow_html=True)


    # =====================================================
    # SECURITY
    # =====================================================

    with tab_security:

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.subheader("🛡️ Security")

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
            "Passwords are stored as SHA-256 hashes. "
            "The application does not display stored passwords."
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

        st.markdown("</div>", unsafe_allow_html=True)


    # =====================================================
    # AUDIT
    # =====================================================

    with tab_audit:

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.subheader("📋 Audit Log")

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

        st.markdown("</div>", unsafe_allow_html=True)


    st.stop()


# =========================================================
# SEARCH PAGE
# =========================================================

# =========================================================
# CONTROL CARD
# =========================================================

st.markdown(
    '<div class="glass-card">',
    unsafe_allow_html=True,
)

st.markdown("### 🎯 Search Control")


# =========================================================
# START MC
# =========================================================

start_value = st.session_state.start_mc

start_input = st.text_input(
    "Start MC",
    value=start_value,
    placeholder="Example: 1800000",
    disabled=st.session_state.running,
    key="start_mc_input",
)

st.caption(
    "Enter the starting MC. The app searches sequentially "
    "one MC at a time. Press STOP whenever you want."
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

    display_hint = "Ready to search"

else:

    display_mc = "—"
    display_hint = "Enter a starting MC"


if display_mc != "—":

    try:

        formatted_mc = f"{int(display_mc):,}"

    except Exception:

        formatted_mc = str(
            display_mc
        )

else:

    formatted_mc = "—"


st.markdown(
    f"""
<div class="current-mc-card">

    <div class="current-label">
        Current MC Number
    </div>

    <div class="current-number">
        {formatted_mc}
    </div>

    <div class="current-hint">
        {display_hint}
    </div>

</div>
""",
    unsafe_allow_html=True,
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
    "</div>",
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

    if st.session_state.current_mc is not None:

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

    start_number = int(cleaned)

    st.session_state.start_mc = str(
        start_number
    )

    st.session_state.current_mc = (
        start_number
    )

    st.session_state.last_searched_mc = None

    st.session_state.running = True

    log_action(
        "SEARCH_STARTED",
        mc_number=str(start_number),
        details="Sequential MC search started",
    )

    st.rerun()


# =========================================================
# LIVE STATUS
# =========================================================

if st.session_state.running:

    current = (
        st.session_state.current_mc
    )

    st.markdown(
        f"""
<div class="glass-card">

    <span class="live-dot"></span>

    <b>
        Searching MC {int(current):,}
    </b>

    <br>

    <small style="color:#9da6c0;">
        Searching sequential MC numbers automatically...
    </small>

</div>
""",
        unsafe_allow_html=True,
    )


elif (
    st.session_state.searched_count > 0
):

    st.markdown(
        f"""
<div class="glass-card">

    <b style="color:#72ffae;">
        ✓ Search stopped
    </b>

    <br><br>

    <small style="color:#9da6c0;">
        {st.session_state.searched_count:,}
        MC number(s) processed.
        Results are preserved until Clear History.
    </small>

</div>
""",
        unsafe_allow_html=True,
    )


# =========================================================
# AUTOMATIC SEARCH
# =========================================================

if st.session_state.running:

    current_mc = int(
        st.session_state.current_mc
    )

    result = search_one(
        str(current_mc)
    )

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

    time.sleep(0.5)

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
        '<div class="filter-card">',
        unsafe_allow_html=True,
    )

    st.markdown("#### 🔎 Filters")

    filter_col1, filter_col2 = st.columns(2)

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
            ].astype(str).str.upper()
            == status_filter
        ]

    if type_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ].astype(str).str.upper()
            == type_filter
        ]

    st.caption(
        f"Showing {len(filtered_df):,} "
        f"of {len(df):,} result(s)"
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
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


    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Searched", len(df))
    c2.metric("Active", active_count)
    c3.metric("Carriers", carrier_count)
    c4.metric("Brokers", broker_count)


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
        "</div>",
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

    download_col1, download_col2 = st.columns(2)

    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

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
        "</div>",
        unsafe_allow_html=True,
    )


    # =====================================================
    # ERRORS
    # =====================================================

    if errors:

        with st.expander(
            "⚠ Search messages"
        ):

            for error in errors:
                st.write(error)
