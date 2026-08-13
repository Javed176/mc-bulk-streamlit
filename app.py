from __future__ import annotations

import io
import time

import pandas as pd
import streamlit as st

from src.auth import require_login, logout_user
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
# AUTHENTICATION
# =========================================================
#
# IMPORTANT:
# auth.py handles the complete login screen.
# Do NOT put the login HTML in this file.
#

require_login()


# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "running": False,
    "current_mc": None,
    "results": [],
    "start_mc": "",
    "searched_count": 0,
    "last_searched_mc": None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# GLOBAL UI
# =========================================================

st.markdown(
    """
<style>

/* =====================================================
   GLOBAL
   ===================================================== */

.stApp {
    background:
        radial-gradient(
            circle at 12% 8%,
            rgba(80, 110, 255, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 88% 10%,
            rgba(180, 70, 255, 0.16),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #05060a 0%,
            #0b0d16 48%,
            #05060a 100%
        );

    color: #f5f7ff;
}


/* =====================================================
   CONTAINER
   ===================================================== */

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 5rem;
}


/* =====================================================
   GLASS
   ===================================================== */

.glass-card {
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.105),
            rgba(255,255,255,0.035)
        );

    border: 1px solid rgba(255,255,255,0.12);

    box-shadow:
        0 20px 70px rgba(0,0,0,0.45),
        inset 0 1px 0 rgba(255,255,255,0.08);

    backdrop-filter:
        blur(25px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(25px)
        saturate(160%);

    border-radius: 28px;
    padding: 26px;
    margin-bottom: 20px;
}


/* =====================================================
   HERO
   ===================================================== */

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -0.05em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #b8c5ff,
            #ffffff
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: rgba(235,240,255,0.62);
    font-size: 1rem;
    margin-top: 4px;
}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {
    background: rgba(255,255,255,0.065) !important;

    border:
        1px solid
        rgba(255,255,255,0.12) !important;

    border-radius: 18px !important;

    transition:
        all 0.25s ease;
}

div[data-baseweb="input"]:focus-within {
    border-color:
        rgba(120,145,255,0.85) !important;

    box-shadow:
        0 0 0 3px rgba(100,125,255,0.12),
        0 0 30px rgba(80,100,255,0.15);
}

input {
    color: white !important;
}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button {
    border-radius: 18px !important;

    border:
        1px solid
        rgba(255,255,255,0.14) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.12),
            rgba(255,255,255,0.045)
        ) !important;

    color: white !important;

    font-weight: 700 !important;

    min-height: 50px;

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease,
        background 0.2s ease;
}

.stButton > button:hover {
    transform:
        translateY(-2px)
        scale(1.015);

    background:
        linear-gradient(
            135deg,
            rgba(105,130,255,0.32),
            rgba(130,80,255,0.22)
        ) !important;

    box-shadow:
        0 12px 35px rgba(75,95,255,0.28),
        0 0 25px rgba(90,110,255,0.18);
}

.stButton > button:active {
    transform: scale(0.97);
}


/* =====================================================
   CURRENT MC
   ===================================================== */

.current-label {
    color: #8f9ab7;
    font-size: 0.9rem;
    margin-top: 20px;
}

.current-number {
    font-size: 2.5rem;
    font-weight: 800;

    color: #ffffff;

    text-shadow:
        0 0 25px rgba(100,130,255,0.35);
}

.current-hint {
    color: #8d98b4;
    font-size: 0.85rem;
    margin-top: 4px;
}


/* =====================================================
   LIVE DOT
   ===================================================== */

.live-dot {
    display: inline-block;

    width: 10px;
    height: 10px;

    border-radius: 50%;

    background: #36ff8a;

    box-shadow:
        0 0 8px #36ff8a,
        0 0 20px #36ff8a;

    animation: pulse 1.4s infinite;

    margin-right: 8px;
}

@keyframes pulse {
    0% {
        transform: scale(0.85);
        opacity: 0.6;
    }

    50% {
        transform: scale(1.2);
        opacity: 1;
    }

    100% {
        transform: scale(0.85);
        opacity: 0.6;
    }
}


/* =====================================================
   BADGES
   ===================================================== */

.badge {
    display: inline-block;

    padding: 8px 15px;

    margin-right: 8px;
    margin-bottom: 8px;

    border-radius: 999px;

    font-weight: 700;
    font-size: 0.9rem;

    border: 1px solid rgba(255,255,255,0.10);

    background: rgba(255,255,255,0.045);
}

.badge-active {
    color: #5cff9b;
    box-shadow: 0 0 18px rgba(50,255,130,0.08);
}

.badge-inactive {
    color: #ff647a;
}

.badge-carrier {
    color: #65a9ff;
}

.badge-broker {
    color: #d18aff;
}


/* =====================================================
   METRICS
   ===================================================== */

div[data-testid="stMetric"] {
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.09),
            rgba(255,255,255,0.035)
        );

    border:
        1px solid
        rgba(255,255,255,0.10);

    border-radius: 22px;

    padding: 18px;

    box-shadow:
        0 15px 40px
        rgba(0,0,0,0.25);
}

div[data-testid="stMetricValue"] {
    color: white !important;
}


/* =====================================================
   DATAFRAME
   ===================================================== */

div[data-testid="stDataFrame"] {
    border-radius: 22px;
    overflow: hidden;

    border:
        1px solid
        rgba(255,255,255,0.10);

    box-shadow:
        0 20px 60px
        rgba(0,0,0,0.30);
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 768px) {

    .hero-title {
        font-size: 2.2rem;
    }

    .current-number {
        font-size: 2rem;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

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


# =========================================================
# CONTROL CARD
# =========================================================

st.markdown(
    '<div class="glass-card">',
    unsafe_allow_html=True,
)

st.markdown("### 🎯 Search Control")


# =========================================================
# START MC INPUT
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
# CURRENT MC DISPLAY
# =========================================================

if st.session_state.current_mc is not None:

    current_display = (
        f"{int(st.session_state.current_mc):,}"
    )

else:

    current_display = "—"


if st.session_state.running:

    current_hint = (
        "Search running • next MC will update automatically"
    )

elif st.session_state.searched_count > 0:

    current_hint = (
        "Search stopped • press START to continue"
    )

else:

    current_hint = "Waiting for search"


st.markdown(
    f"""
<div class="current-label">
    Current MC Number
</div>

<div class="current-number">
    {current_display}
</div>

<div class="current-hint">
    {current_hint}
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
# LOGOUT
# =========================================================

logout_col1, logout_col2 = st.columns([5, 1])

with logout_col2:

    if st.button(
        "🔒 Logout",
        use_container_width=True,
    ):

        logout_user()

        st.rerun()


# =========================================================
# CLEAR HISTORY
# =========================================================

if clear_button:

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = False

    st.session_state.current_mc = None

    st.session_state.last_searched_mc = None

    st.session_state.start_mc = ""

    # Clear the widget safely BEFORE it is recreated
    if "start_mc_input" in st.session_state:
        del st.session_state["start_mc_input"]

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    # IMPORTANT:
    # Do NOT reset current_mc.
    #
    # This preserves the next MC so the user can see
    # exactly where the search stopped.

    st.session_state.running = False

    st.rerun()


# =========================================================
# START
# =========================================================

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


    cleaned = str(
        int(cleaned)
    )


    # -----------------------------------------------------
    # Save starting MC
    # -----------------------------------------------------

    st.session_state.start_mc = cleaned


    # -----------------------------------------------------
    # IMPORTANT:
    # Results are NOT cleared here.
    #
    # Old results remain until Clear History.
    # -----------------------------------------------------

    st.session_state.current_mc = int(
        cleaned
    )

    st.session_state.running = True

    st.rerun()


# =========================================================
# RUNNING STATUS
# =========================================================

if st.session_state.running:

    st.markdown(
        """
<div class="glass-card">

    <span class="live-dot"></span>

    <b>Searching sequential MC numbers...</b>

    <br>

    <small style="color:#9da6c0;">
        The current MC updates automatically after every search.
    </small>

</div>
""",
        unsafe_allow_html=True,
    )


# =========================================================
# STOPPED STATUS
# =========================================================

elif st.session_state.searched_count > 0:

    st.markdown(
        f"""
<div class="glass-card">

    <b style="color:#72ffae;">
        ✓ Search stopped
    </b>

    <br>

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


    # -----------------------------------------------------
    # Search exactly ONE MC
    # -----------------------------------------------------

    result = search_one(
        str(current_mc)
    )


    # -----------------------------------------------------
    # Store result
    # -----------------------------------------------------

    st.session_state.results.append(
        result
    )

    st.session_state.searched_count += 1

    st.session_state.last_searched_mc = (
        current_mc
    )


    # -----------------------------------------------------
    # MOVE TO NEXT MC
    #
    # Example:
    #
    # 1800000 searched
    # current_mc becomes 1800001
    #
    # 1800001 searched
    # current_mc becomes 1800002
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )


    # -----------------------------------------------------
    # Small delay
    # -----------------------------------------------------

    time.sleep(0.35)


    # -----------------------------------------------------
    # Rerun
    # -----------------------------------------------------

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


    # =====================================================
    # BUILD DATAFRAME
    # =====================================================

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
    # COUNTS
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


    # =====================================================
    # BADGES
    # =====================================================

    st.markdown(
        f"""
<span class="badge badge-active">
    ● Active {active_count}
</span>

<span class="badge badge-inactive">
    ● Inactive {inactive_count}
</span>

<span class="badge badge-carrier">
    ◆ Carriers {carrier_count}
</span>

<span class="badge badge-broker">
    ◆ Brokers {broker_count}
</span>
""",
        unsafe_allow_html=True,
    )


    # =====================================================
    # METRICS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

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
    # FILTERS
    # =====================================================

    st.markdown(
        "#### 🔎 Filters"
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
            key="status_filter",
        )


    with filter2:

        type_filter = st.selectbox(
            "Broker / Carrier",
            [
                "All",
                "CARRIER",
                "BROKER",
            ],
            key="type_filter",
        )


    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered_df = df.copy()


    if status_filter != "All":

        filtered_df = filtered_df[
            filtered_df[
                "Operating Status"
            ]
            .astype(str)
            .str.upper()
            == status_filter
        ]


    if type_filter != "All":

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ]
            .astype(str)
            .str.upper()
            == type_filter
        ]


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
            subset=["Operating Status"],
        )
        .map(
            color_type,
            subset=["Broker/Carrier"],
        )
    )


    # =====================================================
    # FILTER RESULT COUNT
    # =====================================================

    st.caption(
        f"Showing {len(filtered_df):,} "
        f"of {len(df):,} result(s)"
    )


    # =====================================================
    # TABLE
    # =====================================================

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
        "### ⬇ Export Filtered Data"
    )

    st.caption(
        f"Downloads contain the currently filtered "
        f"{len(filtered_df):,} row(s)."
    )


    download_col1, download_col2 = st.columns(2)


    # =====================================================
    # CSV
    # =====================================================

    csv_data = (
        filtered_df
        .to_csv(index=False)
        .encode("utf-8")
    )


    with download_col1:

        st.download_button(
            "⬇ Download CSV",
            data=csv_data,
            file_name="mc_filtered_results.csv",
            mime="text/csv",
            use_container_width=True,
        )


    # =====================================================
    # EXCEL
    # =====================================================

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
            "⬇ Download Excel",
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
