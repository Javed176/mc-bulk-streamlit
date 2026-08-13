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
            circle at 10% 10%,
            rgba(70, 100, 255, 0.20),
            transparent 30%
        ),

        radial-gradient(
            circle at 90% 10%,
            rgba(190, 70, 255, 0.18),
            transparent 30%
        ),

        radial-gradient(
            circle at 50% 100%,
            rgba(40, 100, 255, 0.10),
            transparent 35%
        ),

        linear-gradient(
            135deg,
            #05060a 0%,
            #0a0d15 45%,
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

        0 25px 80px
        rgba(0,0,0,0.45),

        inset 0 1px 0
        rgba(255,255,255,0.08);

    backdrop-filter:
        blur(25px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(25px)
        saturate(160%);

    border-radius: 28px;

    padding: 28px;

    margin-bottom: 22px;

}


/* =====================================================
   TITLE
   ===================================================== */

.hero-title {

    font-size: 3rem;

    font-weight: 800;

    letter-spacing: -0.055em;

    margin-bottom: 4px;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #b9c7ff,
            #ffffff,
            #d7b8ff
        );

    background-size: 250% auto;

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    animation:
        titleGlow 5s linear infinite;

}


@keyframes titleGlow {

    0% {
        background-position: 0% center;
    }

    100% {
        background-position: 250% center;
    }

}


.subtitle {

    color:
        rgba(235,240,255,0.62);

    font-size: 1rem;

}


/* =====================================================
   INPUTS
   ===================================================== */

div[data-baseweb="input"] {

    background:
        rgba(255,255,255,0.055) !important;

    border:
        1px solid
        rgba(255,255,255,0.13) !important;

    border-radius:
        18px !important;

    transition:
        all 0.25s ease;

}


div[data-baseweb="input"]:focus-within {

    border-color:
        rgba(110,140,255,0.90) !important;

    box-shadow:

        0 0 0 3px
        rgba(90,120,255,0.12),

        0 0 35px
        rgba(80,100,255,0.18);

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

    min-height: 52px;

    border-radius: 18px !important;

    border:
        1px solid
        rgba(255,255,255,0.14) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.12),
            rgba(255,255,255,0.035)
        ) !important;

    color:
        #ffffff !important;

    font-weight:
        700 !important;

    box-shadow:

        0 12px 35px
        rgba(0,0,0,0.30),

        inset 0 1px 0
        rgba(255,255,255,0.10);

    transition:
        transform 0.20s ease,
        box-shadow 0.20s ease,
        background 0.20s ease;

}


.stButton > button:hover {

    transform:
        translateY(-3px)
        scale(1.015);

    background:
        linear-gradient(
            135deg,
            rgba(100,130,255,0.34),
            rgba(150,75,255,0.24)
        ) !important;

    box-shadow:

        0 15px 45px
        rgba(65,90,255,0.30),

        0 0 30px
        rgba(100,80,255,0.20);

}


.stButton > button:active {

    transform:
        scale(0.96);

}


/* =====================================================
   PRIMARY START BUTTON
   ===================================================== */

button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            #526dff,
            #793cff
        ) !important;

    border:
        1px solid
        rgba(160,175,255,0.60) !important;

    box-shadow:

        0 12px 35px
        rgba(75,80,255,0.35),

        0 0 25px
        rgba(110,80,255,0.18);

}


/* =====================================================
   CURRENT MC DISPLAY
   ===================================================== */

.current-mc-box {

    position: relative;

    overflow: hidden;

    border-radius: 22px;

    padding: 20px 24px;

    margin-top: 8px;

    margin-bottom: 10px;

    background:
        linear-gradient(
            135deg,
            rgba(65,90,255,0.16),
            rgba(145,65,255,0.10)
        );

    border:
        1px solid
        rgba(105,125,255,0.30);

    box-shadow:

        0 15px 45px
        rgba(20,25,70,0.35),

        inset 0 1px 0
        rgba(255,255,255,0.08);

}


.current-mc-label {

    color:
        #9da8c8;

    font-size:
        0.82rem;

    text-transform:
        uppercase;

    letter-spacing:
        0.12em;

}


.current-mc-number {

    color:
        #ffffff;

    font-size:
        2rem;

    font-weight:
        800;

    letter-spacing:
        -0.03em;

    text-shadow:
        0 0 22px
        rgba(100,130,255,0.55);

}


/* =====================================================
   LIVE DOT
   ===================================================== */

.live-dot {

    display: inline-block;

    width: 10px;
    height: 10px;

    border-radius: 50%;

    background:
        #36ff8a;

    box-shadow:

        0 0 8px #36ff8a,
        0 0 22px #36ff8a;

    animation:
        pulse 1.25s infinite;

    margin-right: 8px;

}


@keyframes pulse {

    0% {
        transform: scale(0.85);
        opacity: 0.55;
    }

    50% {
        transform: scale(1.25);
        opacity: 1;
    }

    100% {
        transform: scale(0.85);
        opacity: 0.55;
    }

}


/* =====================================================
   STATUS
   ===================================================== */

.status-running {

    color:
        #72ffae;

    font-weight:
        750;

}


.status-stopped {

    color:
        #72ffae;

    font-weight:
        750;

}


/* =====================================================
   BADGES
   ===================================================== */

.badges {

    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        10px;

    margin:
        15px 0 20px 0;

}


.badge {

    display:
        inline-flex;

    align-items:
        center;

    padding:
        9px 14px;

    border-radius:
        999px;

    font-weight:
        700;

    font-size:
        0.88rem;

    border:
        1px solid
        rgba(255,255,255,0.10);

    box-shadow:
        0 8px 25px
        rgba(0,0,0,0.18);

}


.badge-active {

    color:
        #56ff9b;

    background:
        rgba(40,255,130,0.09);

    border-color:
        rgba(70,255,145,0.25);

}


.badge-inactive {

    color:
        #ff657a;

    background:
        rgba(255,55,80,0.09);

    border-color:
        rgba(255,70,90,0.25);

}


.badge-carrier {

    color:
        #72a8ff;

    background:
        rgba(80,130,255,0.10);

    border-color:
        rgba(90,140,255,0.25);

}


.badge-broker {

    color:
        #d09aff;

    background:
        rgba(170,80,255,0.10);

    border-color:
        rgba(180,90,255,0.25);

}


/* =====================================================
   FILTER AREA
   ===================================================== */

.filter-title {

    font-size:
        1rem;

    font-weight:
        750;

    color:
        #e8ebff;

    margin-bottom:
        8px;

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
        1px solid
        rgba(255,255,255,0.10);

    border-radius:
        22px;

    padding:
        18px;

    box-shadow:
        0 15px 40px
        rgba(0,0,0,0.25);

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
            #000000 0%,
            #000000 24%,
            #160026 29%,
            #6920ff 42%,
            #ff43d1 49%,
            #191020 59%,
            transparent 72%
        );

    box-shadow:

        0 0 35px
        #782cff,

        0 0 100px
        #5d1dff,

        0 0 180px
        rgba(255,40,210,0.38);

    animation:
        blackHole
        1.35s
        cubic-bezier(.6,0,.1,1)
        forwards;

}


@keyframes blackHole {

    0% {

        width: 15px;
        height: 15px;

        opacity: 0;

        transform:
            translate(-50%, -50%)
            rotate(0deg);

    }

    20% {

        width: 230px;
        height: 230px;

        opacity: 1;

    }

    60% {

        width: 340px;
        height: 340px;

        opacity: 1;

        filter:
            brightness(1.5);

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
        font-size: 2.2rem;
    }

    .block-container {

        padding-left:
            1rem;

        padding-right:
            1rem;

    }

    .current-mc-number {
        font-size: 1.6rem;
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

<div class="subtitle">
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
# START MC
# =========================================================

if not st.session_state.running:

    start_input = st.text_input(
        "Start MC",
        value=st.session_state.start_mc,
        placeholder="Example: 1800000",
    )

    st.caption(
        "Enter the starting MC. The app searches one MC at a time."
    )

else:

    # While running, show the original starting MC.
    st.markdown(
        f"""
        <div class="current-mc-box">

            <div class="current-mc-label">
                Start MC
            </div>

            <div class="current-mc-number">
                {st.session_state.start_mc}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    start_input = st.session_state.start_mc


# =========================================================
# CURRENT MC
# =========================================================

if st.session_state.current_mc is not None:

    st.markdown(
        f"""
        <div class="current-mc-box">

            <div class="current-mc-label">
                Current MC Number
            </div>

            <div class="current-mc-number">
                {st.session_state.current_mc}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        """
        <div class="current-mc-box">

            <div class="current-mc-label">
                Current MC Number
            </div>

            <div class="current-mc-number">
                —
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# BUTTONS
# =========================================================

col1, col2, col3 = st.columns(
    [1, 1, 1]
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

    st.markdown(
        '<div class="black-hole"></div>',
        unsafe_allow_html=True,
    )

    time.sleep(1.0)

    st.session_state.running = False
    st.session_state.current_mc = None
    st.session_state.start_mc = ""
    st.session_state.results = []
    st.session_state.searched_count = 0

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

    st.session_state.start_mc = cleaned

    st.session_state.current_mc = int(
        cleaned
    )

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = True

    st.rerun()


# =========================================================
# STOP SEARCH
# =========================================================

if stop_button:

    # IMPORTANT:
    #
    # Do NOT reset current_mc.
    #
    # This means if the search is currently at:
    #
    # 1800003
    #
    # pressing STOP leaves:
    #
    # Current MC Number = 1800003
    #
    # instead of returning to the start MC.

    st.session_state.running = False

    st.rerun()


# =========================================================
# LIVE STATUS
# =========================================================

if st.session_state.running:

    st.markdown(
        f"""
        <div class="glass-card">

            <span class="live-dot"></span>

            <span class="status-running">
                Searching MC {st.session_state.current_mc}
            </span>

            <br>

            <small style="color:#9da6c0;">
                Automatically searching sequential MC numbers...
            </small>

        </div>
        """,
        unsafe_allow_html=True,
    )


elif st.session_state.searched_count > 0:

    st.markdown(
        f"""
        <div class="glass-card">

            <span class="status-stopped">
                ✓ Search stopped
            </span>

            <br>

            <small style="color:#9da6c0;">
                {st.session_state.searched_count}
                MC number(s) processed.
                Current MC: {st.session_state.current_mc}
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
    # THIS IS THE IMPORTANT PART.
    #
    # 1800000
    #     ↓
    # 1800001
    #     ↓
    # 1800002
    #     ↓
    # 1800003
    #
    # The current MC is stored in session state BEFORE
    # rerunning the page.
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )

    # Small delay so the UI doesn't hammer the services.

    time.sleep(0.5)

    # Rerun.
    #
    # On the next run, Current MC Number will display
    # the newly stored number.

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


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # =====================================================
    # FILTER CARD
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 🔎 Filter Results"
    )

    filter_col1, filter_col2 = st.columns(2)


    # =====================================================
    # STATUS FILTER
    # =====================================================

    with filter_col1:

        status_filter = st.multiselect(
            "Operating Status",
            options=[
                "ACTIVE",
                "INACTIVE",
            ],
            default=[
                "ACTIVE",
                "INACTIVE",
            ],
        )


    # =====================================================
    # TYPE FILTER
    # =====================================================

    with filter_col2:

        type_filter = st.multiselect(
            "Broker / Carrier",
            options=[
                "CARRIER",
                "BROKER",
            ],
            default=[
                "CARRIER",
                "BROKER",
            ],
        )


    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered_df = df.copy()


    if status_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Operating Status"
            ].astype(str).str.upper().isin(
                status_filter
            )
        ]

    else:

        filtered_df = filtered_df.iloc[0:0]


    if type_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ].astype(str).str.upper().isin(
                type_filter
            )
        ]

    else:

        filtered_df = filtered_df.iloc[0:0]


    st.markdown(
        f"""
        <div style="
            margin-top:15px;
            color:#9da6c0;
        ">
            Showing
            <b style="color:white;">
                {len(filtered_df)}
            </b>
            of
            <b style="color:white;">
                {len(df)}
            </b>
            results
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # =====================================================
    # COLOR FUNCTIONS
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
    # RESULTS TABLE
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 📋 Filtered Results"
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
    # DOWNLOAD
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### ⬇ Download Filtered Data"
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

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        with st.expander(
            "⚠ Search messages"
        ):

            for error in errors:

                st.write(error)

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )
