from __future__ import annotations

import io
import time

import pandas as pd
import streamlit as st

from src.auth import (
    ensure_bootstrap_admin,
    initialize_auth,
    is_admin,
    is_authenticated,
    is_super_admin,
    login,
    logout,
)

from src.audit import (
    audit_dataframe,
    cleanup_audit_logs,
    log_action,
)

from src.search import search_one


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
# AUTH INITIALIZATION
# =========================================================

initialize_auth()

ensure_bootstrap_admin()


# =========================================================
# CLEAN OLD AUDIT LOGS
# =========================================================

cleanup_audit_logs()


# =========================================================
# LOGIN PAGE
# =========================================================

if not is_authenticated():

    st.markdown(
        """
        <style>

        .stApp {
            background:
                radial-gradient(
                    circle at 15% 10%,
                    rgba(80,110,255,.20),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 85% 15%,
                    rgba(170,80,255,.18),
                    transparent 30%
                ),
                linear-gradient(
                    135deg,
                    #05060a,
                    #0b0d14,
                    #05060a
                );

            color: white;
        }

        .login-card {
            max-width: 520px;
            margin: 8vh auto;
            padding: 40px;
            border-radius: 30px;
            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,.11),
                    rgba(255,255,255,.035)
                );
            border: 1px solid rgba(255,255,255,.13);
            box-shadow:
                0 25px 80px rgba(0,0,0,.50);
            backdrop-filter: blur(25px);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-card">

        <h1>✦ MC Search</h1>

        <p style="color:#aab2c8;">
        Secure access portal
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):

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
            "🔐 Login",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        if login(
            username,
            password,
        ):

            log_action(
                "LOGIN",
                details="Successful login",
            )

            st.rerun()

        else:

            st.error(
                "Incorrect username or password."
            )

            st.caption(
                "Please try again."
            )

    st.stop()


# =========================================================
# GLOBAL UI
# =========================================================

st.markdown(
    """
    <style>

    .stApp {

        background:
            radial-gradient(
                circle at 15% 10%,
                rgba(80,110,255,.18),
                transparent 30%
            ),
            radial-gradient(
                circle at 85% 15%,
                rgba(170,80,255,.16),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #05060a 0%,
                #0b0d14 45%,
                #05060a 100%
            );

        color:#f5f7ff;
    }

    .block-container {
        max-width:1450px;
        padding-top:2rem;
        padding-bottom:4rem;
    }

    h1 {
        font-size:3rem !important;
        font-weight:750 !important;
        letter-spacing:-.05em;
        background:
            linear-gradient(
                90deg,
                #ffffff,
                #b9c5ff,
                #ffffff
            );
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
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

        box-shadow:
            0 20px 70px rgba(0,0,0,.45),
            inset 0 1px 0 rgba(255,255,255,.08);

        backdrop-filter:
            blur(25px)
            saturate(160%);

        border-radius:28px;
        padding:26px;
        margin-bottom:20px;
    }

    .subtitle {
        color:rgba(235,240,255,.62);
        font-size:1rem;
        margin-top:-20px;
        margin-bottom:20px;
    }

    div[data-baseweb="input"] {

        background:
            rgba(255,255,255,.065) !important;

        border:
            1px solid
            rgba(255,255,255,.12) !important;

        border-radius:
            18px !important;
    }

    input {
        color:#fff !important;
    }

    .stButton > button {

        border-radius:18px !important;

        border:
            1px solid
            rgba(255,255,255,.14) !important;

        background:
            linear-gradient(
                135deg,
                rgba(255,255,255,.12),
                rgba(255,255,255,.045)
            ) !important;

        color:#fff !important;

        font-weight:650 !important;

        min-height:50px;

        box-shadow:
            0 10px 30px rgba(0,0,0,.25);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

header_col1, header_col2 = st.columns(
    [4, 1]
)

with header_col1:

    st.markdown(
        """
        <div class="glass-card">

        <h1>✦ MC Search</h1>

        <div class="subtitle">
        FMCSA intelligence → DotSearch enrichment
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with header_col2:

    st.write("")

    st.caption(
        f"👤 {st.session_state.username}"
    )

    st.caption(
        st.session_state.role
    )

    if st.button(
        "Logout",
        use_container_width=True,
    ):

        log_action(
            "LOGOUT",
            details="User logged out",
        )

        logout()

        st.rerun()


# =========================================================
# ADMIN NAVIGATION
# =========================================================

if is_admin():

    admin_tab, search_tab = st.tabs(
        [
            "🔎 MC Search",
            "🛡️ Admin",
        ]
    )

else:

    search_tab = st.container()
    admin_tab = None


# =========================================================
# SEARCH APPLICATION
# =========================================================

with search_tab:

    # =====================================================
    # SESSION STATE
    # =====================================================

    if "running" not in st.session_state:
        st.session_state.running = False

    if "current_mc" not in st.session_state:
        st.session_state.current_mc = None

    if "results" not in st.session_state:
        st.session_state.results = []

    if "start_mc" not in st.session_state:
        st.session_state.start_mc = ""

    if "searched_count" not in st.session_state:
        st.session_state.searched_count = 0


    # =====================================================
    # SEARCH CONTROL
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 🎯 Search Control"
    )

    if st.session_state.running:

        display_mc = str(
            st.session_state.current_mc
        )

    elif st.session_state.start_mc:

        display_mc = str(
            st.session_state.start_mc
        )

    else:

        display_mc = ""


    start_input = st.text_input(
        "Current MC Number",
        value=display_mc,
        placeholder="Example: 1066434",
        disabled=st.session_state.running,
    )

    st.caption(
        "Enter the starting MC. The app searches "
        "sequentially until STOP is pressed."
    )


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


    # =====================================================
    # CLEAR
    # =====================================================

    if clear_button:

        st.session_state.results = []
        st.session_state.searched_count = 0
        st.session_state.running = False
        st.session_state.current_mc = None
        st.session_state.start_mc = ""

        st.rerun()


    # =====================================================
    # STOP
    # =====================================================

    if stop_button:

        st.session_state.running = False
        st.session_state.current_mc = None

        log_action(
            "SEARCH_STOP",
            details=(
                f"{st.session_state.searched_count} "
                "MC number(s) processed"
            ),
        )

        st.rerun()


    # =====================================================
    # START
    # =====================================================

    if start_button:

        cleaned = (
            start_input
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

        st.session_state.start_mc = cleaned

        st.session_state.current_mc = int(
            cleaned
        )

        st.session_state.results = []

        st.session_state.searched_count = 0

        st.session_state.running = True

        log_action(
            "SEARCH_START",
            mc_number=cleaned,
            details="Sequential MC search started",
        )

        st.rerun()


    # =====================================================
    # LIVE STATUS
    # =====================================================

    if st.session_state.running:

        st.info(
            f"🔎 Searching MC "
            f"{st.session_state.current_mc:,}..."
        )


    # =====================================================
    # AUTOMATIC SEARCH
    # =====================================================

    if st.session_state.running:

        current_mc = (
            st.session_state.current_mc
        )

        result = search_one(
            str(current_mc)
        )

        st.session_state.results.append(
            result
        )

        st.session_state.searched_count += 1

        # Audit each individual MC.
        log_action(
            "MC_SEARCH",
            mc_number=str(current_mc),
            details="MC processed",
        )

        st.session_state.current_mc = (
            current_mc + 1
        )

        time.sleep(0.5)

        st.rerun()


    # =====================================================
    # RESULTS
    # =====================================================

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


        df = pd.DataFrame(rows)


        # =================================================
        # FILTERS
        # =================================================

        st.markdown(
            "### 🔎 Filters"
        )

        filter1, filter2 = st.columns(2)


        with filter1:

            status_filter = st.selectbox(
                "Operating Status",
                [
                    "All",
                    "ACTIVE",
                    "INACTIVE",
                ],
            )


        with filter2:

            type_filter = st.selectbox(
                "Broker / Carrier",
                [
                    "All",
                    "CARRIER",
                    "BROKER",
                ],
            )


        filtered_df = df.copy()


        if status_filter != "All":

            filtered_df = filtered_df[
                filtered_df[
                    "Operating Status"
                ]
                == status_filter
            ]


        if type_filter != "All":

            filtered_df = filtered_df[
                filtered_df[
                    "Broker/Carrier"
                ]
                == type_filter
            ]


        # =================================================
        # METRICS
        # =================================================

        active_count = int(
            (
                filtered_df[
                    "Operating Status"
                ]
                == "ACTIVE"
            ).sum()
        )

        carrier_count = int(
            (
                filtered_df[
                    "Broker/Carrier"
                ]
                == "CARRIER"
            ).sum()
        )

        broker_count = int(
            (
                filtered_df[
                    "Broker/Carrier"
                ]
                == "BROKER"
            ).sum()
        )


        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Shown",
            len(filtered_df),
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


        # =================================================
        # TABLE
        # =================================================

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
        )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


        # =================================================
        # DOWNLOAD
        # =================================================

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            "### ⬇ Export Filtered Data"
        )

        csv_data = (
            filtered_df
            .to_csv(index=False)
            .encode("utf-8")
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


        d1, d2 = st.columns(2)


        with d1:

            if st.download_button(
                "Download Filtered CSV",
                data=csv_data,
                file_name="mc_filtered.csv",
                mime="text/csv",
                use_container_width=True,
            ):

                log_action(
                    "DOWNLOAD_CSV",
                    details=(
                        f"{len(filtered_df)} "
                        "filtered rows"
                    ),
                )


        with d2:

            if st.download_button(
                "Download Filtered Excel",
                data=excel_buffer.getvalue(),
                file_name="mc_filtered.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            ):

                log_action(
                    "DOWNLOAD_EXCEL",
                    details=(
                        f"{len(filtered_df)} "
                        "filtered rows"
                    ),
                )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


        # =================================================
        # ERRORS
        # =================================================

        if errors:

            with st.expander(
                "⚠ Search messages"
            ):

                for error in errors:

                    st.write(error)


# =========================================================
# ADMIN PANEL
# =========================================================

if is_admin():

    with admin_tab:

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            "### 🛡️ Administration"
        )

        st.write(
            f"Signed in as "
            f"**{st.session_state.username}** "
            f"({st.session_state.role})"
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


        # =================================================
        # AUDIT LOG
        # =================================================

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            "### 📋 Activity Log"
        )

        users = audit_dataframe()[
            "Username"
        ].dropna().unique().tolist()

        actions = audit_dataframe()[
            "Action"
        ].dropna().unique().tolist()


        f1, f2 = st.columns(2)


        with f1:

            selected_user = st.selectbox(
                "Username",
                ["All"] + sorted(users),
            )


        with f2:

            selected_action = st.selectbox(
                "Action",
                ["All"] + sorted(actions),
            )


        start_date = st.date_input(
            "Start date",
            value=None,
        )

        end_date = st.date_input(
            "End date",
            value=None,
        )


        audit_df = audit_dataframe(
            username=(
                None
                if selected_user == "All"
                else selected_user
            ),
            action=(
                None
                if selected_action == "All"
                else selected_action
            ),
            start_date=start_date,
            end_date=end_date,
        )


        st.dataframe(
            audit_df,
            use_container_width=True,
            hide_index=True,
        )


        audit_csv = (
            audit_df
            .to_csv(index=False)
            .encode("utf-8")
        )


        audit_excel = io.BytesIO()

        with pd.ExcelWriter(
            audit_excel,
            engine="openpyxl",
        ) as writer:

            audit_df.to_excel(
                writer,
                index=False,
                sheet_name="Audit Log",
            )


        a1, a2 = st.columns(2)


        with a1:

            st.download_button(
                "Download Audit CSV",
                data=audit_csv,
                file_name="audit_log.csv",
                mime="text/csv",
                use_container_width=True,
            )


        with a2:

            st.download_button(
                "Download Audit Excel",
                data=audit_excel.getvalue(),
                file_name="audit_log.xlsx",
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


        # =================================================
        # USER MANAGEMENT
        # =================================================

        if is_super_admin():

            st.markdown(
                '<div class="glass-card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                "### 👥 User Management"
            )

            st.info(
                "User creation can be added here after "
                "the initial Super Admin login is confirmed."
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )
