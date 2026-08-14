from __future__ import annotations

import io
import time

import pandas as pd
import streamlit as st

from src.search import search_one

from src.auth import (
    init_auth_state,
    login_user,
    logout_user,
    is_admin,
    is_authenticated,
    is_locked,
    seconds_remaining,
    MAX_LOGIN_ATTEMPTS,
    hash_password,
)

from src.database import (
    get_user_session,
    create_user_record,
    update_user,
    update_user_settings,
    list_users,
    set_user_active,
    create_access_request,
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
# AUTH STATE
# =========================================================

init_auth_state()


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

.login-title {
    text-align:center;
    font-size:2.8rem;
    font-weight:800;
    margin-top:5vh;
    color:white;
}

.login-subtitle {
    text-align:center;
    color:#9da6c0;
    margin-bottom:25px;
}

.request-note {
    text-align:center;
    color:#9da6c0;
    font-size:.9rem;
    margin-top:10px;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# LOGIN / REQUEST ACCESS
# =========================================================

if not is_authenticated():

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

        login_tab, request_tab = st.tabs(
            [
                "🔐 Sign In",
                "📱 Request Access",
            ]
        )

        # =================================================
        # LOGIN
        # =================================================

        with login_tab:

            if is_locked():

                st.error(
                    "🔒 Too many failed login attempts."
                )

                st.warning(
                    f"Try again in "
                    f"{seconds_remaining()} seconds."
                )

            else:

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

        # =================================================
        # REQUEST ACCESS
        # =================================================

        with request_tab:

            st.markdown(
                "### 📱 Request Access"
            )

            st.write(
                "Don't have a username and password?"
            )

            st.caption(
                "Enter your WhatsApp number below. "
                "The administrator will contact you "
                "on WhatsApp and provide your login details."
            )

            with st.form(
                "request_access_form",
                clear_on_submit=True,
            ):

                whatsapp_number = st.text_input(
                    "WhatsApp Number",
                    placeholder="+1 234 567 8900",
                )

                request_submitted = (
                    st.form_submit_button(
                        "📱 Request Access",
                        type="primary",
                        use_container_width=True,
                    )
                )

            if request_submitted:

                whatsapp_clean = str(
                    whatsapp_number
                ).strip()

                digits_only = "".join(
                    ch
                    for ch in whatsapp_clean
                    if ch.isdigit()
                )

                if not whatsapp_clean:

                    st.error(
                        "Please enter your WhatsApp number."
                    )

                elif len(digits_only) < 7:

                    st.error(
                        "Please enter a valid WhatsApp number."
                    )

                elif len(digits_only) > 15:

                    st.error(
                        "Please enter a valid WhatsApp number."
                    )

                else:

                    try:

                        request_result = (
                            create_access_request(
                                whatsapp_clean
                            )
                        )

                        status = str(
                            request_result.get(
                                "status",
                                "",
                            )
                        ).lower()

                        if (
                            request_result.get(
                                "success"
                            )
                        ):

                            st.success(
                                "✓ Access request submitted!"
                            )

                            st.info(
                                "The administrator will "
                                "contact you on WhatsApp."
                            )

                            log_action(
                                "ACCESS_REQUEST",
                                details=(
                                    "New access request "
                                    "submitted"
                                ),
                            )

                        elif status == "waiting":

                            st.warning(
                                "This WhatsApp number "
                                "already has a request "
                                "waiting for review."
                            )

                        elif status == "approved":

                            st.info(
                                "This WhatsApp number has "
                                "already been approved. "
                                "Please contact the administrator."
                            )

                        else:

                            st.warning(
                                request_result.get(
                                    "message",
                                    "Unable to submit request.",
                                )
                            )

                    except Exception as exc:

                        st.error(
                            "Unable to submit the "
                            "access request."
                        )

                        st.caption(
                            str(exc)
                        )

            st.markdown(
                '<div class="request-note">'
                'Only your WhatsApp number is required.'
                '</div>',
                unsafe_allow_html=True,
            )

    st.stop()


# =========================================================
# AUTHENTICATED SESSION VALIDATION
# =========================================================

if not is_authenticated():
    st.stop()


# =========================================================
# SEARCH SESSION STATE
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
        '<div class="hero-title">✦ MC Search</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-subtitle">'
        'FMCSA intelligence → DotSearch enrichment'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


with header_col2:

    st.write("")

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
        '<div class="admin-header">'
        '⚙️ Admin Panel'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="admin-small">'
        'Manage users, security, search delay and audit activity.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "</div>",
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

                hidden_columns = [
                    "session_token",
                    "session_started_at",
                ]

                visible_columns = [
                    c
                    for c in users_df.columns
                    if c not in hidden_columns
                ]

                st.dataframe(
                    users_df[
                        visible_columns
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
            "</div>",
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

                    existing_users = list_users()

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
                            "✓ User created with "
                            "0.5 second search delay."
                        )

                        st.rerun()

                except Exception as exc:

                    st.error(
                        f"Unable to create user: {exc}"
                    )

        st.markdown(
            "</div>",
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

                    current_delay = float(
                        selected_record.get(
                            "search_delay_seconds",
                            0.5,
                        )
                        or 0.0
                    )

                    current_timeout = int(
                        selected_record.get(
                            "session_timeout_minutes",
                            60,
                        )
                        or 60
                    )

                    status_text = (
                        "ACTIVE"
                        if current_active
                        else "INACTIVE"
                    )

                    if current_active:

                        st.success(
                            f"Current status: {status_text}"
                        )

                    else:

                        st.error(
                            f"Current status: {status_text}"
                        )

                    st.markdown(
                        "#### ⚡ Search & Session Settings"
                    )

                    settings_col1, settings_col2 = (
                        st.columns(2)
                    )

                    with settings_col1:

                        delay_value = st.number_input(
                            "Search delay (seconds)",
                            min_value=0.0,
                            max_value=60.0,
                            value=float(
                                current_delay
                            ),
                            step=0.1,
                            format="%.1f",
                            key=(
                                "delay_"
                                + selected_user
                            ),
                        )

                    with settings_col2:

                        timeout_value = st.number_input(
                            "Session timeout (minutes)",
                            min_value=1,
                            max_value=1440,
                            value=int(
                                current_timeout
                            ),
                            step=1,
                            key=(
                                "timeout_"
                                + selected_user
                            ),
                        )

                    st.caption(
                        f"Current delay: {current_delay:g}s • "
                        f"Current session timeout: "
                        f"{current_timeout} minute(s)"
                    )

                    if st.button(
                        "💾 Save User Settings",
                        use_container_width=True,
                        key=(
                            "save_settings_"
                            + selected_user
                        ),
                    ):

                        try:

                            update_user_settings(
                                selected_user,
                                search_delay_seconds=float(
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
                                    f"delay={float(delay_value):g}s, "
                                    f"timeout={int(timeout_value)}m"
                                ),
                            )

                            st.success(
                                "✓ User settings updated."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                f"Unable to save settings: {exc}"
                            )

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

                                set_user_active(
                                    selected_user,
                                    new_active,
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
                                    f"Unable to update user: {exc}"
                                )

                    with action_col2:

                        reset_password = st.text_input(
                            "New password",
                            type="password",
                            key="admin_reset_password",
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

                                except Exception as exc:

                                    st.error(
                                        f"Unable to reset password: {exc}"
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
            "</div>",
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
            "Passwords are stored as SHA-256 hashes. "
            "The application does not display stored passwords."
        )

        st.info(
            "Single-session protection is enabled. "
            "When the same username logs in from another "
            "browser or tab, the previous session is invalidated."
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
            "</div>",
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
            "</div>",
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
# CURRENT USER SETTINGS
# =========================================================

current_user_record = None

try:

    current_user_record = get_user_session(
        st.session_state.username
    )

except Exception:

    current_user_record = None


search_delay = 0.5

if current_user_record:

    try:

        search_delay = float(
            current_user_record.get(
                "search_delay_seconds",
                0.5,
            )
        )

        search_delay = max(
            0.0,
            search_delay,
        )

    except (
        TypeError,
        ValueError,
    ):

        search_delay = 0.5


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
    "one MC at a time. Press STOP whenever you want."
)

st.caption(
    f"⚡ Search delay: {search_delay:g} second(s)"
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

    if (
        st.session_state.current_mc
        is not None
    ):

        st.session_state.last_searched_mc = (
            int(
                st.session_state.current_mc
            )
            - 1
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

    st.session_state.last_searched_mc = None
    st.session_state.running = True

    log_action(
        "SEARCH_STARTED",
        mc_number=str(
            start_number
        ),
        details="Sequential MC search started",
    )

    st.rerun()


# =========================================================
# LIVE STATUS
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

    if search_delay > 0:

        time.sleep(
            search_delay
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

    for result in st.session_state.results:

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

        value = str(
            value
        ).upper()

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

        value = str(
            value
        ).upper()

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
        "</div>",
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
