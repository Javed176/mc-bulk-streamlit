import io
import time

import pandas as pd
import streamlit as st

from src.search import search_one
from src.auth import require_login


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

if "clearing" not in st.session_state:
    st.session_state.clearing = False

if "mc_input_value" not in st.session_state:
    st.session_state.mc_input_value = ""


# =========================================================
# MODERN IOS / GLASS UI
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
            circle at 15% 10%,
            rgba(80, 110, 255, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 85% 15%,
            rgba(170, 80, 255, 0.16),
            transparent 30%
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
   MAIN
   ===================================================== */

.block-container {

    max-width: 1450px;

    padding-top: 2.5rem;
    padding-bottom: 4rem;

}


/* =====================================================
   HEADINGS
   ===================================================== */

h1 {

    font-size: 3rem !important;

    font-weight: 750 !important;

    letter-spacing: -0.05em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #b9c5ff,
            #ffffff
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

}

h2,
h3 {

    color: #f5f7ff !important;

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

    padding: 26px;

    margin-bottom: 20px;

}


/* =====================================================
   SUBTITLE
   ===================================================== */

.subtitle {

    color:
        rgba(235,240,255,0.62);

    font-size: 1rem;

    margin-top: -20px;

    margin-bottom: 28px;

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
        650 !important;

    min-height:
        50px;

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease,
        background 0.2s ease;

    box-shadow:
        0 10px 30px
        rgba(0,0,0,0.25),

        inset 0 1px 0
        rgba(255,255,255,0.10);

}

.stButton > button:hover {

    transform:
        translateY(-2px)
        scale(1.015);

    background:
        linear-gradient(
            135deg,
            rgba(105,130,255,0.30),
            rgba(130,80,255,0.20)
        ) !important;

    box-shadow:
        0 12px 35px
        rgba(75,95,255,0.28),

        0 0 25px
        rgba(90,110,255,0.18);

}

.stButton > button:active {

    transform:
        scale(0.97);

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
   CURRENT MC
   ===================================================== */

.current-mc-label {

    color:
        #9da6c0;

    font-size:
        0.85rem;

    text-transform:
        uppercase;

    letter-spacing:
        0.12em;

    font-weight:
        700;

    margin-top:
        22px;

}

.current-mc-number {

    font-size:
        2.8rem;

    font-weight:
        800;

    letter-spacing:
        -0.04em;

    color:
        #ffffff;

    text-shadow:
        0 0 30px
        rgba(110,130,255,0.25);

}

.current-mc-hint {

    color:
        #78829c;

    font-size:
        0.85rem;

    margin-top:
        4px;

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

    display:
        inline-block;

    padding:
        8px 14px;

    margin:
        4px 6px 12px 0;

    border-radius:
        999px;

    font-weight:
        700;

    font-size:
        0.88rem;

    border:
        1px solid
        rgba(255,255,255,0.12);

    background:
        rgba(255,255,255,0.055);

    box-shadow:
        inset 0 1px 0
        rgba(255,255,255,0.06);

}

.badge-active {

    color:
        #72ffae;

    box-shadow:
        0 0 20px
        rgba(54,255,138,0.08);

}

.badge-inactive {

    color:
        #ff7184;

}

.badge-carrier {

    color:
        #60a5fa;

}

.badge-broker {

    color:
        #c084fc;

}


/* =====================================================
   FILTER BOX
   ===================================================== */

.filter-card {

    background:
        rgba(255,255,255,0.045);

    border:
        1px solid
        rgba(255,255,255,0.08);

    border-radius:
        20px;

    padding:
        18px;

    margin-top:
        18px;

    margin-bottom:
        18px;

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

        filter:
            brightness(1.4);

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

    h1 {

        font-size:
            2.2rem !important;

    }

    .block-container {

        padding-left:
            1rem;

        padding-right:
            1rem;

    }

    .current-mc-number {

        font-size:
            2.2rem;

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
# CONTROL CARD
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
# =========================================================

if st.session_state.running:

    current_display = (
        st.session_state.current_mc
    )

    current_hint = (
        "Search running • next MC will update automatically"
    )

elif st.session_state.current_mc is not None:

    current_display = (
        st.session_state.current_mc
    )

    current_hint = (
        "Search stopped • press START to continue"
    )

else:

    current_display = "—"

    current_hint = "Waiting to start"


st.markdown(
    f"""
    <div class="current-mc-label">
        Current MC Number
    </div>

    <div class="current-mc-number">
        {current_display:,}
    </div>

    <div class="current-mc-hint">
        {current_hint}
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

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    st.session_state.running = False

    # IMPORTANT:
    # Keep current_mc so the user can see exactly
    # where the search stopped.

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

    # Store starting MC.

    st.session_state.start_mc = cleaned

    # Start exactly at the MC entered.

    st.session_state.current_mc = int(
        cleaned
    )

    # IMPORTANT:
    # Do NOT clear existing results here.
    #
    # Results remain until Clear History.

    st.session_state.running = True

    st.rerun()


# =========================================================
# LIVE STATUS
# =========================================================

if st.session_state.running:

    st.markdown(
        """
        <div class="glass-card">

        <span class="live-dot"></span>

        <b>
            Searching sequential MC numbers...
        </b>

        <br>

        <small style="color:#9da6c0;">
            The current MC updates automatically.
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

    current_mc = (
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
    # Move to next MC
    #
    # Example:
    #
    # 1800000
    # 1800001
    # 1800002
    # 1800003
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )

    # -----------------------------------------------------
    # Small delay
    # -----------------------------------------------------

    time.sleep(0.5)

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
    # FILTERS
    # =====================================================

    st.markdown(
        '<div class="filter-card">',
        unsafe_allow_html=True,
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

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered_df = df.copy()

    if status_filter != "All":

        filtered_df = filtered_df[
            filtered_df[
                "Operating Status"
            ] == status_filter
        ]

    if type_filter != "All":

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ] == type_filter
        ]


    # =====================================================
    # METRICS FROM FULL RESULTS
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

    broker_count = int(
        (
            df["Broker/Carrier"]
            == "BROKER"
        ).sum()
    )

    carrier_count = int(
        (
            df["Broker/Carrier"]
            == "CARRIER"
        ).sum()
    )


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
    # TABLE COLORS
    # =====================================================

    def color_status(value):

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


    st.caption(
        f"Showing {len(filtered_df):,} "
        f"of {len(df):,} results."
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
        "### ⬇ Export Filtered Data"
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
            "Download CSV",
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
