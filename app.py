import io
import time

import pandas as pd
import streamlit as st

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
# SESSION STATE
# =========================================================

DEFAULTS = {
    "running": False,
    "start_mc": "",
    "current_mc": None,
    "results": [],
    "searched_count": 0,
    "clear_animation": False,
    "status_message": "",
    "filter_status": "All",
    "filter_type": "All",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# CSS
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
            circle at 10% 5%,
            rgba(76, 110, 255, 0.18),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(185, 70, 255, 0.15),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(30, 90, 255, 0.08),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #04050a 0%,
            #090b13 48%,
            #04050a 100%
        );

    color: #f5f7ff;
    min-height: 100vh;
}


.block-container {
    max-width: 1450px;
    padding-top: 2.2rem;
    padding-bottom: 5rem;
}


/* =====================================================
   HERO
   ===================================================== */

.hero-card {
    position: relative;
    overflow: hidden;

    padding: 32px 34px;
    margin-bottom: 22px;

    border-radius: 30px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.105),
            rgba(255,255,255,0.035)
        );

    border: 1px solid rgba(255,255,255,0.12);

    box-shadow:
        0 25px 80px rgba(0,0,0,0.45),
        inset 0 1px 0 rgba(255,255,255,0.10);

    backdrop-filter: blur(28px) saturate(160%);
    -webkit-backdrop-filter: blur(28px) saturate(160%);
}


.hero-card::before {
    content: "";

    position: absolute;

    width: 260px;
    height: 260px;

    right: -80px;
    top: -120px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(110,130,255,0.28),
            transparent 70%
        );

    pointer-events: none;
}


.hero-title {
    position: relative;

    font-size: 3rem;
    font-weight: 800;

    letter-spacing: -0.055em;

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
    position: relative;

    margin-top: 6px;

    color: rgba(235,240,255,0.60);

    font-size: 1rem;
}


/* =====================================================
   GLASS CARDS
   ===================================================== */

.glass-card {

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.095),
            rgba(255,255,255,0.032)
        );

    border:
        1px solid rgba(255,255,255,0.11);

    box-shadow:
        0 20px 65px rgba(0,0,0,0.36),
        inset 0 1px 0 rgba(255,255,255,0.07);

    backdrop-filter:
        blur(25px)
        saturate(150%);

    -webkit-backdrop-filter:
        blur(25px)
        saturate(150%);

    border-radius: 26px;

    padding: 26px;

    margin-bottom: 20px;
}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {

    background:
        rgba(255,255,255,0.055) !important;

    border:
        1px solid rgba(255,255,255,0.13) !important;

    border-radius:
        17px !important;

    transition:
        all 0.25s ease !important;
}


div[data-baseweb="input"]:focus-within {

    border-color:
        rgba(110,140,255,0.85) !important;

    box-shadow:
        0 0 0 3px rgba(90,120,255,0.12),
        0 0 30px rgba(80,110,255,0.18);
}


input {

    color: #ffffff !important;

    font-size: 1.08rem !important;
}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button {

    min-height: 52px;

    border-radius: 17px !important;

    border:
        1px solid rgba(255,255,255,0.14) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.12),
            rgba(255,255,255,0.045)
        ) !important;

    color: #ffffff !important;

    font-weight: 700 !important;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.25),
        inset 0 1px 0 rgba(255,255,255,0.10);

    transition:
        transform 0.20s ease,
        box-shadow 0.20s ease,
        background 0.20s ease !important;
}


.stButton > button:hover {

    transform:
        translateY(-2px)
        scale(1.012);

    background:
        linear-gradient(
            135deg,
            rgba(90,120,255,0.30),
            rgba(155,80,255,0.22)
        ) !important;

    box-shadow:
        0 14px 38px rgba(70,90,255,0.30),
        0 0 28px rgba(100,120,255,0.16);
}


.stButton > button:active {

    transform:
        scale(0.965);
}


/* =====================================================
   PRIMARY BUTTON
   ===================================================== */

button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            #546cff,
            #7a4cff
        ) !important;

    border-color:
        rgba(170,180,255,0.45) !important;

    box-shadow:
        0 12px 35px rgba(83,90,255,0.32),
        0 0 25px rgba(120,80,255,0.18);
}


/* =====================================================
   CURRENT MC
   ===================================================== */

.current-mc-card {

    text-align: center;

    padding: 25px;

    border-radius: 24px;

    background:
        linear-gradient(
            135deg,
            rgba(80,105,255,0.13),
            rgba(150,70,255,0.08)
        );

    border:
        1px solid rgba(120,140,255,0.20);

    box-shadow:
        0 15px 50px rgba(40,50,160,0.18),
        inset 0 1px 0 rgba(255,255,255,0.07);
}


.current-mc-label {

    color:
        rgba(220,225,255,0.58);

    font-size:
        0.82rem;

    text-transform:
        uppercase;

    letter-spacing:
        0.12em;

    font-weight:
        700;
}


.current-mc-number {

    margin-top:
        5px;

    font-size:
        2.35rem;

    font-weight:
        800;

    letter-spacing:
        -0.04em;

    color:
        #ffffff;

    text-shadow:
        0 0 25px rgba(105,130,255,0.30);
}


.current-mc-hint {

    margin-top:
        4px;

    color:
        #8e99b5;

    font-size:
        0.82rem;
}


/* =====================================================
   LIVE DOT
   ===================================================== */

.live-dot {

    display: inline-block;

    width: 10px;
    height: 10px;

    margin-right: 8px;

    border-radius: 50%;

    background:
        #35ff88;

    box-shadow:
        0 0 8px #35ff88,
        0 0 22px #35ff88;

    animation:
        pulse 1.35s infinite;
}


@keyframes pulse {

    0% {
        transform: scale(0.8);
        opacity: 0.60;
    }

    50% {
        transform: scale(1.25);
        opacity: 1;
    }

    100% {
        transform: scale(0.8);
        opacity: 0.60;
    }
}


/* =====================================================
   FILTERS
   ===================================================== */

.filter-label {

    color:
        rgba(225,230,250,0.62);

    font-size:
        0.78rem;

    text-transform:
        uppercase;

    letter-spacing:
        0.08em;

    font-weight:
        700;

    margin-bottom:
        4px;
}


/* =====================================================
   BADGES
   ===================================================== */

.badges {

    display: flex;

    flex-wrap: wrap;

    gap: 10px;

    margin:
        15px 0 20px 0;
}


.badge {

    display: inline-flex;

    align-items: center;

    padding:
        8px 13px;

    border-radius:
        999px;

    font-size:
        0.82rem;

    font-weight:
        750;

    border:
        1px solid rgba(255,255,255,0.10);

    backdrop-filter:
        blur(10px);
}


.badge-active {

    color: #52ff9a;

    background:
        rgba(45,255,135,0.09);

    border-color:
        rgba(50,255,140,0.20);
}


.badge-inactive {

    color: #ff667b;

    background:
        rgba(255,70,95,0.09);

    border-color:
        rgba(255,70,95,0.20);
}


.badge-carrier {

    color: #67a9ff;

    background:
        rgba(70,130,255,0.09);

    border-color:
        rgba(70,130,255,0.20);
}


.badge-broker {

    color: #ca8cff;

    background:
        rgba(180,80,255,0.09);

    border-color:
        rgba(180,80,255,0.20);
}


/* =====================================================
   METRICS
   ===================================================== */

div[data-testid="stMetric"] {

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.08),
            rgba(255,255,255,0.025)
        );

    border:
        1px solid rgba(255,255,255,0.09);

    border-radius:
        20px;

    padding:
        17px;

    box-shadow:
        0 12px 35px rgba(0,0,0,0.22);
}


div[data-testid="stMetricValue"] {

    color:
        #ffffff !important;
}


/* =====================================================
   DATAFRAME
   ===================================================== */

div[data-testid="stDataFrame"] {

    border-radius:
        20px;

    overflow:
        hidden;

    border:
        1px solid rgba(255,255,255,0.10);

    box-shadow:
        0 18px 55px rgba(0,0,0,0.30);
}


/* =====================================================
   BLACK HOLE
   ===================================================== */

.black-hole {

    position: fixed;

    left: 50%;
    top: 50%;

    transform:
        translate(-50%, -50%);

    width: 20px;
    height: 20px;

    border-radius: 50%;

    z-index: 999999;

    background:
        radial-gradient(
            circle,
            #000000 0%,
            #000000 25%,
            #28004a 31%,
            #7b21ff 43%,
            #ff43d0 49%,
            #160f25 59%,
            transparent 72%
        );

    box-shadow:
        0 0 35px #7925ff,
        0 0 100px #5d1dff,
        0 0 180px rgba(255,40,210,0.38);

    animation:
        blackHole 1.35s
        cubic-bezier(.6,0,.1,1)
        forwards;
}


@keyframes blackHole {

    0% {

        width: 20px;
        height: 20px;

        opacity: 0;

        transform:
            translate(-50%, -50%)
            rotate(0deg);
    }

    20% {

        width: 220px;
        height: 220px;

        opacity: 1;
    }

    55% {

        width: 340px;
        height: 340px;

        opacity: 1;

        filter:
            brightness(1.45);
    }

    100% {

        width: 0;
        height: 0;

        opacity: 0;

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
        font-size: 2.25rem;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .current-mc-number {
        font-size: 2rem;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# CLEAR ANIMATION
# =========================================================

if st.session_state.clear_animation:

    st.markdown(
        '<div class="black-hole"></div>',
        unsafe_allow_html=True,
    )

    time.sleep(1.1)

    st.session_state.clear_animation = False


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
# SEARCH CONTROL
# =========================================================

st.markdown(
    '<div class="glass-card">',
    unsafe_allow_html=True,
)

st.markdown(
    "### 🎯 Search Control"
)


# =========================================================
# START MC INPUT
#
# IMPORTANT:
# This widget is NEVER modified programmatically.
# Therefore Streamlit will not throw the widget-state error.
# =========================================================

start_input = st.text_input(
    "Start MC",
    value=st.session_state.start_mc,
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
#
# This is NOT a text_input.
# It is only a display.
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
            "Search stopped"
        )

else:

    current_display = "—"

    current_hint = (
        "Waiting for search"
    )


st.markdown(
    f"""
    <div class="current-mc-card">

        <div class="current-mc-label">
            Current MC Number
        </div>

        <div class="current-mc-number">
            {current_display}
        </div>

        <div class="current-mc-hint">
            {current_hint}
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# BUTTONS
# =========================================================

button_col1, button_col2, button_col3 = st.columns(
    [1, 1, 1]
)


with button_col1:

    start_button = st.button(
        "▶ Start Search",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running,
    )


with button_col2:

    stop_button = st.button(
        "■ Stop",
        use_container_width=True,
        disabled=not st.session_state.running,
    )


with button_col3:

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

    # Start animation on this run.
    st.session_state.clear_animation = True

    # Clear actual search data.
    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = False

    st.session_state.current_mc = None

    st.session_state.start_mc = ""

    st.session_state.filter_status = "All"

    st.session_state.filter_type = "All"

    st.rerun()


# =========================================================
# START SEARCH
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


    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Start MC is saved ONCE.
    # Current MC is initialized from it.
    #
    # We NEVER modify start_mc_input after this.
    # -----------------------------------------------------

    st.session_state.start_mc = cleaned

    st.session_state.current_mc = int(
        cleaned
    )

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = True

    st.session_state.filter_status = "All"

    st.session_state.filter_type = "All"

    st.rerun()


# =========================================================
# STOP SEARCH
# =========================================================

if stop_button:

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Do NOT reset current_mc.
    # Do NOT reset start_mc.
    #
    # This means if the search is currently at 1800003,
    # pressing STOP leaves Current MC = 1800003.
    # -----------------------------------------------------

    st.session_state.running = False

    st.rerun()


# =========================================================
# LIVE STATUS
# =========================================================

if st.session_state.running:

    current_mc = int(
        st.session_state.current_mc
    )

    st.markdown(
        f"""
        <div class="glass-card">

            <span class="live-dot"></span>

            <b>
                Searching MC
                {current_mc:,}
            </b>

            <br>

            <small style="color:#9da6c0;">
                Searching sequential MC numbers automatically...
            </small>

        </div>
        """,
        unsafe_allow_html=True,
    )


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
    # Search current MC
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


    # -----------------------------------------------------
    # ADVANCE CURRENT MC
    #
    # Example:
    #
    # 1800000 searched
    # current_mc becomes 1800001
    #
    # next rerun searches 1800001.
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
    # NORMALIZE FILTER VALUES
    # =====================================================

    df["Operating Status"] = (
        df["Operating Status"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["Broker/Carrier"] = (
        df["Broker/Carrier"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )


    # =====================================================
    # COUNTS
    # =====================================================

    active_count = int(
        (
            df["Operating Status"]
            == "ACTIVE"
        ).sum()
    )


    inactive_count = int(
        (
            df["Operating Status"]
            == "INACTIVE"
        ).sum()
    )


    carrier_count = int(
        (
            df["Broker/Carrier"]
            == "CARRIER"
        ).sum()
    )


    broker_count = int(
        (
            df["Broker/Carrier"]
            == "BROKER"
        ).sum()
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
    # BADGES
    # =====================================================

    st.markdown(
        f"""
        <div class="badges">

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

        </div>
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


    filter_col1, filter_col2 = st.columns(2)


    with filter_col1:

        st.markdown(
            '<div class="filter-label">Operating Status</div>',
            unsafe_allow_html=True,
        )

        status_filter = st.selectbox(
            "Operating Status",
            [
                "All",
                "ACTIVE",
                "INACTIVE",
            ],
            index=[
                "All",
                "ACTIVE",
                "INACTIVE",
            ].index(
                st.session_state.filter_status
                if st.session_state.filter_status
                in [
                    "All",
                    "ACTIVE",
                    "INACTIVE",
                ]
                else "All"
            ),
            label_visibility="collapsed",
            key="status_filter_widget",
        )

        st.session_state.filter_status = (
            status_filter
        )


    with filter_col2:

        st.markdown(
            '<div class="filter-label">Business Type</div>',
            unsafe_allow_html=True,
        )

        type_filter = st.selectbox(
            "Business Type",
            [
                "All",
                "CARRIER",
                "BROKER",
            ],
            index=[
                "All",
                "CARRIER",
                "BROKER",
            ].index(
                st.session_state.filter_type
                if st.session_state.filter_type
                in [
                    "All",
                    "CARRIER",
                    "BROKER",
                ]
                else "All"
            ),
            label_visibility="collapsed",
            key="type_filter_widget",
        )

        st.session_state.filter_type = (
            type_filter
        )


    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered_df = df.copy()


    if status_filter != "All":

        filtered_df = filtered_df[
            filtered_df["Operating Status"]
            == status_filter
        ]


    if type_filter != "All":

        filtered_df = filtered_df[
            filtered_df["Broker/Carrier"]
            == type_filter
        ]


    # =====================================================
    # COLOR FUNCTIONS
    # =====================================================

    def color_status(value):

        if value == "ACTIVE":

            return (
                "color:#39ff88;"
                "font-weight:800;"
                "background-color:rgba(40,255,130,0.06);"
            )

        if value == "INACTIVE":

            return (
                "color:#ff526b;"
                "font-weight:800;"
                "background-color:rgba(255,50,80,0.06);"
            )

        return ""


    def color_type(value):

        if value == "BROKER":

            return (
                "color:#c084fc;"
                "font-weight:800;"
                "background-color:rgba(190,90,255,0.06);"
            )

        if value == "CARRIER":

            return (
                "color:#60a5fa;"
                "font-weight:800;"
                "background-color:rgba(70,130,255,0.06);"
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


    st.caption(
        f"Showing {len(filtered_df):,} of "
        f"{len(df):,} searched MC records."
    )


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # =====================================================
    # DOWNLOAD
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )


    st.markdown(
        "### ⬇ Export"
    )


    st.caption(
        "Downloads contain the currently filtered data."
    )


    download_col1, download_col2 = st.columns(2)


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
            "⬇ Download Filtered CSV",
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
            "⬇ Download Filtered Excel",
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

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        with st.expander(
            f"⚠ Search messages ({len(errors)})"
        ):

            for error in errors:

                st.write(error)

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )
