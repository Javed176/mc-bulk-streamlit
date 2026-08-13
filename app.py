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
    "current_mc": None,
    "start_mc": "",
    "results": [],
    "searched_count": 0,
    "just_stopped": False,
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
            circle at 10% 5%,
            rgba(72, 96, 255, 0.20),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(175, 65, 255, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(40, 120, 255, 0.10),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #05060a 0%,
            #0a0d16 45%,
            #05060a 100%
        );

    color: #f5f7ff;
}


/* =====================================================
   MAIN
   ===================================================== */

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}


/* =====================================================
   GLASS CARDS
   ===================================================== */

.glass-card {
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.105),
            rgba(255,255,255,0.035)
        );

    border:
        1px solid rgba(255,255,255,0.12);

    border-radius: 28px;

    padding: 26px;

    margin-bottom: 20px;

    box-shadow:
        0 20px 70px rgba(0,0,0,0.42),
        inset 0 1px 0 rgba(255,255,255,0.08);

    backdrop-filter:
        blur(25px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(25px)
        saturate(160%);
}


/* =====================================================
   HERO
   ===================================================== */

.hero-title {
    font-size: 3.1rem;
    font-weight: 800;
    letter-spacing: -0.055em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #aebcff,
            #d9c8ff,
            #ffffff
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    margin-top: 5px;
    color: rgba(235,240,255,0.60);
    font-size: 1rem;
}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {
    background:
        rgba(255,255,255,0.065) !important;

    border:
        1px solid rgba(255,255,255,0.12) !important;

    border-radius:
        18px !important;

    transition:
        all 0.25s ease !important;
}

div[data-baseweb="input"]:focus-within {
    border-color:
        rgba(110,140,255,0.9) !important;

    box-shadow:
        0 0 0 3px rgba(90,120,255,0.12),
        0 0 30px rgba(80,100,255,0.16);
}

input {
    color: #ffffff !important;
}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button {
    min-height: 52px;

    border-radius: 18px !important;

    border:
        1px solid rgba(255,255,255,0.14) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.13),
            rgba(255,255,255,0.045)
        ) !important;

    color: #ffffff !important;

    font-weight: 700 !important;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.25),
        inset 0 1px 0 rgba(255,255,255,0.10);

    transition:
        all 0.20s ease !important;
}

.stButton > button:hover {
    transform:
        translateY(-3px)
        scale(1.015);

    border-color:
        rgba(125,145,255,0.50) !important;

    background:
        linear-gradient(
            135deg,
            rgba(95,125,255,0.32),
            rgba(145,80,255,0.22)
        ) !important;

    box-shadow:
        0 15px 40px rgba(70,90,255,0.28),
        0 0 28px rgba(90,110,255,0.18);
}

.stButton > button:active {
    transform:
        translateY(0)
        scale(0.97);
}


/* =====================================================
   CURRENT MC
   ===================================================== */

.current-mc-box {
    margin-top: 22px;

    padding: 24px;

    text-align: center;

    border-radius: 24px;

    background:
        linear-gradient(
            135deg,
            rgba(85,110,255,0.15),
            rgba(170,80,255,0.10)
        );

    border:
        1px solid rgba(120,140,255,0.22);

    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.08),
        0 15px 45px rgba(0,0,0,0.25);
}

.current-mc-label {
    color: rgba(220,225,245,0.58);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

.current-mc-number {
    margin-top: 7px;

    font-size: 2.7rem;

    font-weight: 800;

    letter-spacing: -0.04em;

    color: #ffffff;

    text-shadow:
        0 0 25px rgba(100,130,255,0.35);
}

.current-mc-hint {
    margin-top: 5px;
    color: #8993ad;
}


/* =====================================================
   LIVE DOT
   ===================================================== */

.live-dot {
    display: inline-block;

    width: 10px;
    height: 10px;

    border-radius: 50%;

    background: #39ff88;

    box-shadow:
        0 0 8px #39ff88,
        0 0 20px #39ff88;

    animation:
        pulse 1.25s infinite;

    margin-right: 8px;
}

@keyframes pulse {

    0% {
        transform: scale(0.8);
        opacity: 0.55;
    }

    50% {
        transform: scale(1.25);
        opacity: 1;
    }

    100% {
        transform: scale(0.8);
        opacity: 0.55;
    }
}


/* =====================================================
   BADGES
   ===================================================== */

.badge {
    display: inline-block;

    padding: 8px 14px;

    margin-right: 8px;
    margin-bottom: 8px;

    border-radius: 999px;

    font-size: 0.88rem;

    font-weight: 700;

    border: 1px solid rgba(255,255,255,0.10);
}

.badge-active {
    color: #58ff9a;
    background: rgba(40,255,130,0.08);
}

.badge-inactive {
    color: #ff667c;
    background: rgba(255,60,90,0.08);
}

.badge-carrier {
    color: #66a9ff;
    background: rgba(70,130,255,0.08);
}

.badge-broker {
    color: #c58cff;
    background: rgba(175,80,255,0.08);
}


/* =====================================================
   METRICS
   ===================================================== */

div[data-testid="stMetric"] {
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.085),
            rgba(255,255,255,0.025)
        );

    border:
        1px solid rgba(255,255,255,0.09);

    border-radius: 22px;

    padding: 17px;

    box-shadow:
        0 15px 40px rgba(0,0,0,0.25);
}

div[data-testid="stMetricValue"] {
    color: #ffffff !important;
}


/* =====================================================
   DATAFRAME
   ===================================================== */

div[data-testid="stDataFrame"] {
    border-radius: 22px;

    overflow: hidden;

    border:
        1px solid rgba(255,255,255,0.10);

    box-shadow:
        0 20px 60px rgba(0,0,0,0.30);
}


/* =====================================================
   DOWNLOAD BUTTON
   ===================================================== */

.stDownloadButton > button {
    width: 100%;

    min-height: 50px;

    border-radius: 18px !important;

    border:
        1px solid rgba(255,255,255,0.13) !important;

    background:
        linear-gradient(
            135deg,
            rgba(70,100,255,0.20),
            rgba(145,70,255,0.14)
        ) !important;

    color: white !important;

    font-weight: 700 !important;

    transition: all 0.2s ease !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px);

    box-shadow:
        0 12px 30px rgba(75,95,255,0.25);
}


/* =====================================================
   SELECTBOX
   ===================================================== */

div[data-baseweb="select"] > div {
    background:
        rgba(255,255,255,0.065) !important;

    border:
        1px solid rgba(255,255,255,0.12) !important;

    border-radius:
        16px !important;

    color: white !important;
}


/* =====================================================
   BLACK HOLE
   ===================================================== */

.black-hole {
    position: fixed;

    left: 50%;
    top: 50%;

    transform: translate(-50%, -50%);

    width: 30px;
    height: 30px;

    border-radius: 50%;

    z-index: 999999;

    background:
        radial-gradient(
            circle,
            #000000 0%,
            #000000 28%,
            #26003d 32%,
            #7025ff 43%,
            #ff4fd8 49%,
            #171021 59%,
            transparent 72%
        );

    box-shadow:
        0 0 35px #792cff,
        0 0 100px #591cff,
        0 0 180px rgba(255,40,210,0.45);

    animation:
        blackHole 1.2s
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
        width: 270px;
        height: 270px;
        opacity: 1;
    }

    55% {
        width: 350px;
        height: 350px;
        opacity: 1;
        filter: brightness(1.5);
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

    .current-mc-number {
        font-size: 2.1rem;
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
# SEARCH CONTROL
# =========================================================

st.markdown(
    '<div class="glass-card">',
    unsafe_allow_html=True,
)

st.markdown("### 🎯 Search Control")


# =========================================================
# START MC INPUT
# IMPORTANT:
# DO NOT MODIFY THIS WIDGET THROUGH SESSION STATE.
# =========================================================

start_input = st.text_input(
    "Start MC",
    value=(
        str(st.session_state.start_mc)
        if st.session_state.start_mc
        else ""
    ),
    placeholder="Example: 1800000",
    disabled=st.session_state.running,
)


st.caption(
    "Enter the starting MC. The app searches sequentially "
    "one MC at a time. Press STOP whenever you want."
)


# =========================================================
# CURRENT MC DISPLAY
# THIS IS SEPARATE FROM THE INPUT
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
        current_hint = "Search stopped"

else:

    current_display = "—"
    current_hint = "Waiting for search"


st.markdown(
    f"""
<div class="current-mc-box">

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
    st.session_state.results = []
    st.session_state.searched_count = 0
    st.session_state.current_mc = None
    st.session_state.start_mc = ""
    st.session_state.just_stopped = False

    # Clear filters if they exist
    if "status_filter" in st.session_state:
        st.session_state.status_filter = "All"

    if "type_filter" in st.session_state:
        st.session_state.type_filter = "All"

    # Animation
    st.markdown(
        '<div class="black-hole"></div>',
        unsafe_allow_html=True,
    )

    time.sleep(0.9)

    st.rerun()


# =========================================================
# STOP
# IMPORTANT:
# DO NOT RESET current_mc HERE
# =========================================================

if stop_button:

    st.session_state.running = False

    # Keep current_mc exactly where the search stopped.
    st.session_state.just_stopped = True

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

    # New search
    st.session_state.start_mc = cleaned

    st.session_state.current_mc = int(
        cleaned
    )

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = True

    st.session_state.just_stopped = False

    st.rerun()


# =========================================================
# LIVE STATUS
# =========================================================

if st.session_state.running:

    st.markdown(
        f"""
<div class="glass-card">

    <span class="live-dot"></span>

    <b>
        Searching MC
        {int(st.session_state.current_mc):,}
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
    st.session_state.just_stopped
    and st.session_state.searched_count > 0
):

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
    # MOVE TO NEXT MC
    #
    # Example:
    #
    # 1800000 searched
    # current_mc becomes 1800001
    #
    # Next rerun:
    #
    # 1800001 searched
    # current_mc becomes 1800002
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )

    # -----------------------------------------------------
    # DELAY
    # -----------------------------------------------------

    time.sleep(0.5)

    # -----------------------------------------------------
    # RERUN
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


    columns = [
        "MC Number",
        "Owner",
        "Carrier/Broker Name",
        "Broker/Carrier",
        "Operating Status",
        "Number",
        "Email Address",
        "Location",
    ]


    df = pd.DataFrame(
        rows,
        columns=columns,
    )


    # =====================================================
    # NORMALIZE FILTER VALUES
    # =====================================================

    df["Operating Status"] = (
        df["Operating Status"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["Broker/Carrier"] = (
        df["Broker/Carrier"]
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
        "### 🔎 Filters"
    )

    filter_col1, filter_col2 = st.columns(2)


    with filter_col1:

        status_filter = st.selectbox(
            "Operating Status",
            [
                "All",
                "ACTIVE",
                "INACTIVE",
            ],
            key="status_filter",
        )


    with filter_col2:

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
            == status_filter
        ]


    if type_filter != "All":

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ]
            == type_filter
        ]


    # =====================================================
    # FILTER RESULT COUNT
    # =====================================================

    st.caption(
        f"Showing {len(filtered_df):,} "
        f"of {len(df):,} searched MC numbers."
    )


    # =====================================================
    # TABLE COLORS
    # =====================================================

    def color_status(value):

        if value == "ACTIVE":

            return (
                "color:#39ff88;"
                "font-weight:800;"
            )

        if value == "INACTIVE":

            return (
                "color:#ff526b;"
                "font-weight:800;"
            )

        return ""


    def color_type(value):

        if value == "BROKER":

            return (
                "color:#c084fc;"
                "font-weight:800;"
            )

        if value == "CARRIER":

            return (
                "color:#60a5fa;"
                "font-weight:800;"
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


    # =====================================================
    # DISPLAY TABLE
    # =====================================================

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=550,
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
        "Downloads contain only the rows currently "
        "selected by your filters."
    )


    download_col1, download_col2 = st.columns(2)


    # =====================================================
    # CSV
    # =====================================================

    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8")


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

                st.write(
                    error
                )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )
