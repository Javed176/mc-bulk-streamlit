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
# SECURITY
# =========================================================

require_login()


# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "running": False,
    "current_mc": None,
    "start_mc": "",
    "results": [],
    "searched_count": 0,
    "clear_animation": False,
}

for key, value in DEFAULTS.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# GLOBAL CSS
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
            rgba(80,110,255,0.20),
            transparent 30%
        ),

        radial-gradient(
            circle at 88% 12%,
            rgba(170,70,255,0.18),
            transparent 30%
        ),

        radial-gradient(
            circle at 50% 90%,
            rgba(30,120,255,0.08),
            transparent 35%
        ),

        linear-gradient(
            135deg,
            #05060a 0%,
            #0b0d14 45%,
            #05060a 100%
        );

    color: #f5f7ff;
}


/* =====================================================
   MAIN CONTAINER
   ===================================================== */

.block-container {

    max-width: 1450px;

    padding-top: 2.2rem;
    padding-bottom: 5rem;
}


/* =====================================================
   TEXT
   ===================================================== */

h1,
h2,
h3,
h4 {

    color: #f5f7ff !important;
}


/* =====================================================
   HERO
   ===================================================== */

.hero-card {

    padding: 32px;

    margin-bottom: 20px;

    border-radius: 28px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.115),
            rgba(255,255,255,0.035)
        );

    border:
        1px solid
        rgba(255,255,255,0.12);

    box-shadow:
        0 25px 75px
        rgba(0,0,0,0.45),

        inset 0 1px 0
        rgba(255,255,255,0.08);

    backdrop-filter:
        blur(25px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(25px)
        saturate(160%);
}


.hero-title {

    font-size: 3rem;

    font-weight: 800;

    letter-spacing: -0.055em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #aebcff,
            #ffffff
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;
}


.hero-subtitle {

    margin-top: 7px;

    color:
        rgba(235,240,255,0.62);

    font-size: 1rem;
}


/* =====================================================
   GLASS CARD
   ===================================================== */

.glass-card {

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.105),
            rgba(255,255,255,0.035)
        );

    border:
        1px solid
        rgba(255,255,255,0.12);

    box-shadow:
        0 20px 70px
        rgba(0,0,0,0.40),

        inset 0 1px 0
        rgba(255,255,255,0.07);

    backdrop-filter:
        blur(25px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(25px)
        saturate(160%);

    border-radius:
        28px;

    padding:
        26px;

    margin-bottom:
        20px;
}


/* =====================================================
   CURRENT MC
   ===================================================== */

.current-card {

    text-align: center;

    padding:
        26px 20px;

    border-radius:
        24px;

    background:
        linear-gradient(
            135deg,
            rgba(90,110,255,0.12),
            rgba(130,70,255,0.06)
        );

    border:
        1px solid
        rgba(110,130,255,0.20);

    box-shadow:
        0 15px 50px
        rgba(50,60,180,0.18),

        inset 0 1px 0
        rgba(255,255,255,0.06);

}


.current-label {

    color:
        #8f9ab7;

    font-size:
        0.85rem;

    text-transform:
        uppercase;

    letter-spacing:
        0.12em;

    font-weight:
        700;
}


.current-number {

    margin-top:
        8px;

    font-size:
        2.35rem;

    font-weight:
        800;

    letter-spacing:
        -0.04em;

    color:
        #ffffff;

    text-shadow:
        0 0 25px
        rgba(110,130,255,0.35);
}


.current-hint {

    margin-top:
        5px;

    color:
        #78839f;

    font-size:
        0.85rem;
}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {

    background:
        rgba(255,255,255,0.065) !important;

    border:
        1px solid
        rgba(255,255,255,0.12) !important;

    border-radius:
        18px !important;

    transition:
        all 0.25s ease;
}


div[data-baseweb="input"]:focus-within {

    border-color:
        rgba(120,145,255,0.85) !important;

    box-shadow:
        0 0 0 3px
        rgba(100,125,255,0.12),

        0 0 30px
        rgba(80,100,255,0.15);
}


input {

    color:
        #ffffff !important;

    font-size:
        1.05rem !important;
}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button {

    min-height:
        50px;

    border-radius:
        18px !important;

    border:
        1px solid
        rgba(255,255,255,0.14) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.12),
            rgba(255,255,255,0.045)
        ) !important;

    color:
        #ffffff !important;

    font-weight:
        700 !important;

    box-shadow:
        0 10px 30px
        rgba(0,0,0,0.25),

        inset 0 1px 0
        rgba(255,255,255,0.10);

    transition:
        transform 0.20s ease,
        box-shadow 0.20s ease,
        background 0.20s ease;
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
        0 14px 38px
        rgba(75,95,255,0.28),

        0 0 28px
        rgba(90,110,255,0.18);
}


.stButton > button:active {

    transform:
        scale(0.97);
}


/* =====================================================
   PRIMARY BUTTON
   ===================================================== */

button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            #536dff,
            #7b45e8
        ) !important;

    border:
        1px solid
        rgba(160,170,255,0.45) !important;

    box-shadow:
        0 10px 35px
        rgba(83,109,255,0.35),

        0 0 25px
        rgba(120,70,255,0.18);
}


button[kind="primary"]:hover {

    background:
        linear-gradient(
            135deg,
            #6680ff,
            #914fff
        ) !important;

    box-shadow:
        0 15px 45px
        rgba(83,109,255,0.45),

        0 0 35px
        rgba(120,70,255,0.25);
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

    border-radius:
        22px;

    padding:
        18px;

    box-shadow:
        0 15px 40px
        rgba(0,0,0,0.25);

    backdrop-filter:
        blur(20px);
}


div[data-testid="stMetricValue"] {

    color:
        #ffffff !important;
}


/* =====================================================
   FILTERS
   ===================================================== */

.filter-card {

    padding:
        20px 22px;

    border-radius:
        22px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.075),
            rgba(255,255,255,0.025)
        );

    border:
        1px solid
        rgba(255,255,255,0.10);

    margin:
        18px 0;
}


/* =====================================================
   STATUS CARD
   ===================================================== */

.status-card {

    padding:
        22px 26px;

    margin-bottom:
        20px;

    border-radius:
        22px;

    background:
        linear-gradient(
            135deg,
            rgba(54,255,138,0.08),
            rgba(255,255,255,0.035)
        );

    border:
        1px solid
        rgba(54,255,138,0.18);

    box-shadow:
        0 15px 45px
        rgba(0,0,0,0.28),

        inset 0 1px 0
        rgba(255,255,255,0.06);

    backdrop-filter:
        blur(20px);
}


/* =====================================================
   LIVE DOT
   ===================================================== */

.live-dot {

    display:
        inline-block;

    width:
        10px;

    height:
        10px;

    border-radius:
        50%;

    background:
        #36ff8a;

    box-shadow:
        0 0 8px #36ff8a,
        0 0 20px #36ff8a;

    animation:
        pulse 1.4s infinite;

    margin-right:
        8px;
}


@keyframes pulse {

    0% {
        transform:
            scale(0.85);

        opacity:
            0.6;
    }

    50% {
        transform:
            scale(1.2);

        opacity:
            1;
    }

    100% {
        transform:
            scale(0.85);

        opacity:
            0.6;
    }
}


/* =====================================================
   BADGES
   ===================================================== */

.badge {

    display:
        inline-block;

    padding:
        9px 14px;

    margin:
        4px 5px 4px 0;

    border-radius:
        999px;

    font-size:
        0.88rem;

    font-weight:
        750;

    border:
        1px solid;
}


.badge-active {

    color:
        #72ffae;

    background:
        rgba(54,255,138,0.09);

    border-color:
        rgba(54,255,138,0.22);

    box-shadow:
        0 0 18px
        rgba(54,255,138,0.08);
}


.badge-inactive {

    color:
        #ff7285;

    background:
        rgba(255,70,100,0.08);

    border-color:
        rgba(255,70,100,0.20);
}


.badge-carrier {

    color:
        #70a8ff;

    background:
        rgba(70,130,255,0.08);

    border-color:
        rgba(70,130,255,0.20);
}


.badge-broker {

    color:
        #ce8cff;

    background:
        rgba(160,80,255,0.08);

    border-color:
        rgba(160,80,255,0.20);
}


/* =====================================================
   DATAFRAME
   ===================================================== */

div[data-testid="stDataFrame"] {

    border-radius:
        22px;

    overflow:
        hidden;

    border:
        1px solid
        rgba(255,255,255,0.10);

    box-shadow:
        0 20px 60px
        rgba(0,0,0,0.30);
}


/* =====================================================
   BLACK HOLE
   ===================================================== */

.black-hole {

    position:
        fixed;

    left:
        50%;

    top:
        50%;

    transform:
        translate(-50%, -50%);

    width:
        220px;

    height:
        220px;

    border-radius:
        50%;

    z-index:
        999999;

    background:

        radial-gradient(
            circle,
            #000 0%,
            #000 27%,
            #17002c 30%,
            #6d1cff 43%,
            #ff4fd8 48%,
            #151020 58%,
            transparent 70%
        );

    box-shadow:

        0 0 35px
        #7a2cff,

        0 0 100px
        #5a1cff,

        0 0 180px
        rgba(255,40,210,0.35);

    animation:
        blackHole 1.35s
        cubic-bezier(.6,0,.1,1)
        forwards;
}


@keyframes blackHole {

    0% {

        width:
            20px;

        height:
            20px;

        opacity:
            0;

        transform:
            translate(-50%, -50%)
            rotate(0deg);
    }

    25% {

        width:
            260px;

        height:
            260px;

        opacity:
            1;
    }

    65% {

        width:
            330px;

        height:
            330px;

        opacity:
            1;

        filter:
            brightness(1.4);
    }

    100% {

        width:
            0;

        height:
            0;

        opacity:
            0;

        transform:
            translate(-50%, -50%)
            rotate(540deg);
    }
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 768px) {

    .hero-title {

        font-size:
            2.2rem !important;
    }

    .block-container {

        padding-left:
            1rem;

        padding-right:
            1rem;
    }

    .current-number {

        font-size:
            1.9rem;
    }

}

</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero-card">

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
# TOP RIGHT LOGOUT
# =========================================================

logout_col1, logout_col2 = st.columns(
    [8, 1]
)

with logout_col2:

    if st.button(
        "Logout",
        use_container_width=True,
    ):

        logout_user()

        st.rerun()


# =========================================================
# SEARCH CONTROL CARD
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

    if st.session_state.running:

        current_hint = (
            "Search running • next MC will update automatically"
        )

    else:

        current_hint = (
            "Search stopped • press START to continue"
        )

else:

    current_display = "—"

    current_hint = (
        "Waiting for search"
    )


st.markdown(
    f"""
    <div class="current-card">

        <div class="current-label">
            Current MC Number
        </div>

        <div class="current-number">
            {current_display}
        </div>

        <div class="current-hint">
            {current_hint}
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# BUTTONS
# =========================================================

col1, col2, col3 = st.columns(
    3
)


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

    st.session_state.clear_animation = True

    st.markdown(
        """
        <div class="black-hole"></div>
        """,
        unsafe_allow_html=True,
    )

    time.sleep(1.0)

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = False

    st.session_state.current_mc = None

    st.session_state.start_mc = ""

    st.session_state.clear_animation = False

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    st.session_state.running = False

    # IMPORTANT:
    #
    # Do NOT clear:
    #
    # results
    # searched_count
    # start_mc
    #
    # Results must survive STOP.

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


    # ---------------------------------------------
    # New search starts from the entered MC.
    #
    # Existing results are intentionally preserved.
    # ---------------------------------------------

    st.session_state.start_mc = cleaned

    st.session_state.current_mc = int(
        cleaned
    )

    st.session_state.running = True

    st.rerun()


# =========================================================
# LIVE STATUS
# =========================================================

if st.session_state.running:

    st.markdown(
        """
        <div class="status-card">

            <span class="live-dot"></span>

            <b>
                Searching sequential MC numbers...
            </b>

            <br>

            <small style="color:#9da6c0;">
                Searching one MC at a time.
                Press STOP to pause the search.
            </small>

        </div>
        """,
        unsafe_allow_html=True,
    )


elif st.session_state.searched_count > 0:

    st.markdown(
        f"""
        <div class="status-card">

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


    # -----------------------------------------------------
    # SEARCH CURRENT MC
    # -----------------------------------------------------

    result = search_one(
        str(current_mc)
    )


    # -----------------------------------------------------
    # STORE RESULT
    # -----------------------------------------------------

    st.session_state.results.append(
        result
    )

    st.session_state.searched_count += 1


    # -----------------------------------------------------
    # NEXT MC
    #
    # Example:
    #
    # 1800000 searched
    # current becomes 1800001
    #
    # 1800001 searched
    # current becomes 1800002
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )


    # -----------------------------------------------------
    # SMALL DELAY
    # -----------------------------------------------------

    time.sleep(
        0.5
    )


    # -----------------------------------------------------
    # RERUN
    # -----------------------------------------------------

    st.rerun()


# =========================================================
# RESULTS
# =========================================================

if st.session_state.results:

    # =====================================================
    # CONVERT RESULTS
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
    # RESULTS CARD
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 📊 Search Results"
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


    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )


    # =====================================================
    # TOTAL METRICS
    # =====================================================

    m1, m2, m3, m4 = st.columns(
        4
    )


    m1.metric(
        "Searched",
        len(df),
    )

    m2.metric(
        "Active",
        active_count,
    )

    m3.metric(
        "Carriers",
        carrier_count,
    )

    m4.metric(
        "Brokers",
        broker_count,
    )


    # =====================================================
    # FILTER CARD
    # =====================================================

    st.markdown(
        """
        <div class="filter-card">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 🔎 Filters"
    )


    filter_col1, filter_col2 = st.columns(
        2
    )


    with filter_col1:

        status_filter = st.selectbox(
            "Operating Status",
            options=[
                "ALL",
                "ACTIVE",
                "INACTIVE",
            ],
            index=0,
            key="status_filter",
        )


    with filter_col2:

        type_filter = st.selectbox(
            "Broker / Carrier",
            options=[
                "ALL",
                "CARRIER",
                "BROKER",
            ],
            index=0,
            key="type_filter",
        )


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # =====================================================
    # APPLY FILTERS
    # =====================================================

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


    # =====================================================
    # FILTER RESULT COUNT
    # =====================================================

    st.caption(
        f"Showing "
        f"{len(filtered_df):,} "
        f"of "
        f"{len(df):,} "
        f"searched records."
    )


    # =====================================================
    # TABLE COLORS
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


    # =====================================================
    # STYLE FILTERED DATA
    # =====================================================

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
    # EXPORT CARD
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### ⬇ Export Filtered Data"
    )

    st.caption(
        "Downloads contain only the records currently "
        "selected by the filters."
    )


    download_col1, download_col2 = st.columns(
        2
    )


    # =====================================================
    # CSV
    # =====================================================

    csv_data = filtered_df.to_csv(
        index=False
    ).encode(
        "utf-8"
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
            f"⚠ Search messages ({len(errors)})"
        ):

            for error in errors:

                st.write(error)
