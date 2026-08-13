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
    "search_session": 0,
    "clear_animation": False,
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
            circle at 15% 5%,
            rgba(85,110,255,.20),
            transparent 30%
        ),
        radial-gradient(
            circle at 85% 10%,
            rgba(175,70,255,.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(20,120,255,.08),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #030409 0%,
            #090b13 45%,
            #030409 100%
        );

    color: #f5f7ff;
}


/* =====================================================
   MAIN
   ===================================================== */

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 5rem;
}


/* =====================================================
   HERO
   ===================================================== */

.hero-card {
    position: relative;

    padding: 35px 36px;

    margin-bottom: 22px;

    border-radius: 30px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.12),
            rgba(255,255,255,.035)
        );

    border:
        1px solid rgba(255,255,255,.13);

    box-shadow:
        0 25px 80px rgba(0,0,0,.48),
        inset 0 1px 0 rgba(255,255,255,.10);

    backdrop-filter: blur(28px);
    -webkit-backdrop-filter: blur(28px);

    overflow: hidden;
}

.hero-card::before {
    content: "";

    position: absolute;

    width: 260px;
    height: 260px;

    right: -100px;
    top: -130px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(100,120,255,.32),
            transparent 70%
        );

    filter: blur(15px);
}

.hero-title {
    position: relative;

    font-size: 3.2rem;
    font-weight: 800;

    letter-spacing: -.055em;

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
    position: relative;

    margin-top: 5px;

    color: rgba(235,240,255,.60);

    font-size: 1rem;
}


/* =====================================================
   GLASS CARD
   ===================================================== */

.glass-card {
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.095),
            rgba(255,255,255,.032)
        );

    border:
        1px solid rgba(255,255,255,.11);

    border-radius: 28px;

    padding: 26px;

    margin-bottom: 20px;

    box-shadow:
        0 20px 70px rgba(0,0,0,.40),
        inset 0 1px 0 rgba(255,255,255,.07);

    backdrop-filter: blur(25px);
    -webkit-backdrop-filter: blur(25px);
}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {
    background:
        rgba(255,255,255,.055) !important;

    border:
        1px solid rgba(255,255,255,.13) !important;

    border-radius: 18px !important;

    transition:
        border-color .25s ease,
        box-shadow .25s ease,
        transform .25s ease;
}

div[data-baseweb="input"]:focus-within {
    border-color:
        rgba(115,140,255,.90) !important;

    box-shadow:
        0 0 0 3px rgba(100,125,255,.12),
        0 0 35px rgba(80,100,255,.18);

    transform: translateY(-1px);
}

input {
    color: #ffffff !important;
    font-size: 1.05rem !important;
}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button,
.stDownloadButton > button {

    min-height: 50px;

    border-radius: 18px !important;

    border:
        1px solid rgba(255,255,255,.14) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.12),
            rgba(255,255,255,.035)
        ) !important;

    color: #ffffff !important;

    font-weight: 700 !important;

    box-shadow:
        0 10px 30px rgba(0,0,0,.28),
        inset 0 1px 0 rgba(255,255,255,.09);

    transition:
        transform .20s ease,
        box-shadow .20s ease,
        background .20s ease,
        border-color .20s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {

    transform:
        translateY(-3px)
        scale(1.015);

    border-color:
        rgba(120,145,255,.50) !important;

    background:
        linear-gradient(
            135deg,
            rgba(95,120,255,.30),
            rgba(145,70,255,.22)
        ) !important;

    box-shadow:
        0 15px 42px rgba(60,80,255,.28),
        0 0 30px rgba(100,80,255,.15);
}

.stButton > button:active,
.stDownloadButton > button:active {
    transform: scale(.96);
}


/* =====================================================
   CURRENT MC
   ===================================================== */

.current-mc-box {

    margin-top: 22px;

    padding: 25px;

    text-align: center;

    border-radius: 23px;

    background:
        radial-gradient(
            circle at 50% 0%,
            rgba(100,120,255,.13),
            transparent 65%
        ),
        rgba(255,255,255,.035);

    border:
        1px solid rgba(255,255,255,.10);

    box-shadow:
        inset 0 1px 0 rgba(255,255,255,.05),
        0 15px 45px rgba(0,0,0,.25);
}

.current-mc-label {

    color:
        rgba(220,228,255,.58);

    font-size: .85rem;

    text-transform: uppercase;

    letter-spacing: .12em;

    font-weight: 700;
}

.current-mc-number {

    margin-top: 8px;

    font-size: 2.5rem;

    line-height: 1;

    font-weight: 850;

    letter-spacing: -.04em;

    color: #ffffff;

    text-shadow:
        0 0 25px rgba(110,130,255,.25);
}

.current-mc-hint {

    margin-top: 10px;

    color:
        rgba(220,228,255,.48);

    font-size: .86rem;
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

    background: #36ff8a;

    box-shadow:
        0 0 8px #36ff8a,
        0 0 20px #36ff8a;

    animation:
        pulse 1.3s infinite;
}

@keyframes pulse {

    0% {
        transform: scale(.80);
        opacity: .55;
    }

    50% {
        transform: scale(1.18);
        opacity: 1;
    }

    100% {
        transform: scale(.80);
        opacity: .55;
    }
}


/* =====================================================
   STATUS
   ===================================================== */

.status-running {

    padding: 17px 20px;

    border-radius: 19px;

    background:
        linear-gradient(
            135deg,
            rgba(45,255,135,.09),
            rgba(80,100,255,.055)
        );

    border:
        1px solid rgba(54,255,138,.18);

    box-shadow:
        0 12px 35px rgba(0,0,0,.22);
}

.status-stopped {

    padding: 17px 20px;

    border-radius: 19px;

    background:
        rgba(255,255,255,.035);

    border:
        1px solid rgba(255,255,255,.09);
}


/* =====================================================
   METRICS
   ===================================================== */

div[data-testid="stMetric"] {

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.085),
            rgba(255,255,255,.025)
        );

    border:
        1px solid rgba(255,255,255,.09);

    border-radius: 21px;

    padding: 18px;

    box-shadow:
        0 15px 40px rgba(0,0,0,.24);

    backdrop-filter: blur(18px);
}

div[data-testid="stMetricValue"] {
    color: #ffffff !important;
}


/* =====================================================
   FILTERS
   ===================================================== */

.filter-card {

    padding: 18px;

    border-radius: 20px;

    background:
        rgba(255,255,255,.035);

    border:
        1px solid rgba(255,255,255,.08);

    margin-bottom: 15px;
}


/* =====================================================
   TABLE
   ===================================================== */

div[data-testid="stDataFrame"] {

    border-radius: 22px;

    overflow: hidden;

    border:
        1px solid rgba(255,255,255,.10);

    box-shadow:
        0 20px 60px rgba(0,0,0,.30);
}


/* =====================================================
   BADGES
   ===================================================== */

.badges {

    display: flex;

    gap: 10px;

    flex-wrap: wrap;

    margin: 15px 0 20px 0;
}

.badge {

    display: inline-flex;

    align-items: center;

    padding: 9px 15px;

    border-radius: 999px;

    font-size: .85rem;

    font-weight: 750;

    border: 1px solid;
}

.badge-active {

    color: #55ff9a;

    background: rgba(50,255,130,.08);

    border-color:
        rgba(50,255,130,.20);

}

.badge-inactive {

    color: #ff6680;

    background: rgba(255,70,100,.08);

    border-color:
        rgba(255,70,100,.20);

}

.badge-carrier {

    color: #69a8ff;

    background: rgba(80,140,255,.08);

    border-color:
        rgba(80,140,255,.20);

}

.badge-broker {

    color: #c78aff;

    background: rgba(180,90,255,.08);

    border-color:
        rgba(180,90,255,.20);
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

    width: 220px;
    height: 220px;

    border-radius: 50%;

    z-index: 999999;

    background:
        radial-gradient(
            circle,
            #000 0%,
            #000 25%,
            #17002c 31%,
            #6d1cff 43%,
            #ff4fd8 48%,
            #151020 59%,
            transparent 70%
        );

    box-shadow:
        0 0 35px #7a2cff,
        0 0 100px #5a1cff,
        0 0 180px rgba(255,40,210,.35);

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

    25% {

        width: 260px;
        height: 260px;

        opacity: 1;
    }

    65% {

        width: 330px;
        height: 330px;

        opacity: 1;

        filter: brightness(1.4);
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

st.markdown("### 🎯 Search Control")


# ---------------------------------------------------------
# START MC INPUT
# ---------------------------------------------------------

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
            "Search running • this is the MC currently being processed"
        )

    else:

        current_hint = (
            "Search stopped • press START to continue from a new MC"
        )

else:

    current_display = "—"

    current_hint = (
        "Waiting for search"
    )


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

    st.session_state.clear_animation = True

    st.markdown(
        '<div class="black-hole"></div>',
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

    # IMPORTANT:
    # We do NOT clear existing results here.
    #
    # This means:
    #
    # Search 1800000 → Stop
    #
    # then:
    #
    # Search 1900000
    #
    # Existing results remain until Clear History.

    st.session_state.start_mc = cleaned

    st.session_state.current_mc = int(cleaned)

    st.session_state.running = True

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    # IMPORTANT:
    # Do NOT set current_mc = None.
    #
    # This keeps the last/current MC visible after STOP.

    st.session_state.running = False

    st.rerun()


# =========================================================
# RUNNING STATUS
# =========================================================

if st.session_state.running:

    st.markdown(
        """
<div class="status-running">

    <span class="live-dot"></span>

    <b>Searching sequential MC numbers...</b>

    <br>

    <small style="color:#9da6c0;">
        Current MC updates automatically after every search.
    </small>

</div>
""",
        unsafe_allow_html=True,
    )


elif st.session_state.searched_count > 0:

    st.markdown(
        f"""
<div class="status-stopped">

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
    # current = 1800000
    # search 1800000
    # next display = 1800001
    #
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )

    # -----------------------------------------------------
    # SMALL DELAY
    # -----------------------------------------------------

    time.sleep(0.4)

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

    broker_count = int(
        (
            df["Broker/Carrier"]
            .astype(str)
            .str.upper()
            == "BROKER"
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
    # METRIC CARDS
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

    f1, f2 = st.columns(2)


    with f1:

        status_filter = st.selectbox(
            "Operating Status",
            [
                "All",
                "ACTIVE",
                "INACTIVE",
            ],
            key="status_filter",
        )


    with f2:

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


    st.caption(
        f"Showing {len(filtered_df):,} of {len(df):,} searched records"
    )


    # =====================================================
    # TABLE COLORS
    # =====================================================

    def color_status(value):

        value = str(value).upper()

        if value == "ACTIVE":

            return (
                "color:#39ff88;"
                "font-weight:800;"
            )

        if value == "INACTIVE":

            return (
                "color:#ff4d67;"
                "font-weight:800;"
            )

        return ""


    def color_type(value):

        value = str(value).upper()

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
        "Downloads contain the currently filtered records."
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
            "Download Filtered CSV",
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
            "Download Filtered Excel",
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
