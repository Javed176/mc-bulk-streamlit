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
    "results": [],
    "start_mc": "",
    "searched_count": 0,
    "show_black_hole": False,
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
            rgba(76, 110, 255, 0.20),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(175, 75, 255, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(30, 90, 255, 0.08),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #040509 0%,
            #090b12 45%,
            #05060a 100%
        );

    color: #f5f7ff;

}


/* =====================================================
   CONTAINER
   ===================================================== */

.block-container {

    max-width: 1450px;

    padding-top: 2.5rem;
    padding-bottom: 5rem;

}


/* =====================================================
   HEADINGS
   ===================================================== */

h1 {

    font-size: 3.1rem !important;

    font-weight: 800 !important;

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

    border-radius: 28px;

    padding: 26px;

    margin-bottom: 20px;

    box-shadow:
        0 25px 80px
        rgba(0,0,0,0.45),

        inset 0 1px 0
        rgba(255,255,255,0.08);

    backdrop-filter:
        blur(28px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(28px)
        saturate(160%);

}


/* =====================================================
   SUBTITLE
   ===================================================== */

.subtitle {

    color:
        rgba(235,240,255,0.62);

    font-size:
        1rem;

    margin-top:
        -18px;

}


/* =====================================================
   INPUT
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
        rgba(110,140,255,0.9) !important;

    box-shadow:
        0 0 0 3px
        rgba(100,125,255,0.13),

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

    min-height:
        52px;

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
        rgba(0,0,0,0.28),

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
            rgba(100,130,255,0.32),
            rgba(150,75,255,0.22)
        ) !important;

    box-shadow:
        0 15px 40px
        rgba(75,95,255,0.30),

        0 0 30px
        rgba(100,110,255,0.20);

}


.stButton > button:active {

    transform:
        scale(0.96);

}


/* =====================================================
   SELECTBOX
   ===================================================== */

div[data-baseweb="select"] > div {

    background:
        rgba(255,255,255,0.055) !important;

    border:
        1px solid
        rgba(255,255,255,0.13) !important;

    border-radius:
        16px !important;

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
   BADGES
   ===================================================== */

.stats-row {

    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        12px;

    margin:
        20px 0 24px 0;

}


.badge {

    display:
        inline-flex;

    align-items:
        center;

    padding:
        10px 18px;

    border-radius:
        999px;

    font-size:
        0.92rem;

    font-weight:
        750;

    border:
        1px solid
        rgba(255,255,255,0.12);

    backdrop-filter:
        blur(15px);

    box-shadow:
        0 8px 25px
        rgba(0,0,0,0.25),

        inset 0 1px 0
        rgba(255,255,255,0.08);

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease;

}


.badge:hover {

    transform:
        translateY(-3px)
        scale(1.03);

}


.badge-active {

    color:
        #5cff9a;

    background:
        rgba(40,255,130,0.10);

    border-color:
        rgba(60,255,140,0.25);

    box-shadow:
        0 0 25px
        rgba(50,255,130,0.12);

}


.badge-inactive {

    color:
        #ff6478;

    background:
        rgba(255,60,90,0.10);

    border-color:
        rgba(255,70,100,0.25);

    box-shadow:
        0 0 25px
        rgba(255,50,80,0.10);

}


.badge-carrier {

    color:
        #62a8ff;

    background:
        rgba(70,130,255,0.10);

    border-color:
        rgba(80,140,255,0.25);

    box-shadow:
        0 0 25px
        rgba(70,130,255,0.10);

}


.badge-broker {

    color:
        #c084fc;

    background:
        rgba(170,80,255,0.10);

    border-color:
        rgba(180,90,255,0.25);

    box-shadow:
        0 0 25px
        rgba(170,80,255,0.10);

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
        0 0 22px #36ff8a;

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
        transform: scale(1.25);
        opacity: 1;
    }

    100% {
        transform: scale(0.85);
        opacity: 0.6;
    }

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

    width:
        240px;

    height:
        240px;

    border-radius:
        50%;

    z-index:
        999999;

    pointer-events:
        none;

    background:

        radial-gradient(
            circle,
            #000000 0%,
            #000000 25%,
            #17002c 30%,
            #7025ff 42%,
            #ff4fd8 49%,
            #171020 58%,
            transparent 72%
        );

    box-shadow:

        0 0 40px
        #7a2cff,

        0 0 100px
        #5a1cff,

        0 0 180px
        rgba(255,40,210,0.45);

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
            rotate(0deg)
            scale(0.2);

    }

    20% {

        width:
            240px;

        height:
            240px;

        opacity:
            1;

        transform:
            translate(-50%, -50%)
            rotate(100deg)
            scale(1);

    }

    55% {

        width:
            350px;

        height:
            350px;

        opacity:
            1;

        filter:
            brightness(1.5);

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
            rotate(720deg)
            scale(0);

    }

}


/* =====================================================
   FILTER HEADER
   ===================================================== */

.filter-title {

    color:
        rgba(235,240,255,0.65);

    font-size:
        0.85rem;

    font-weight:
        700;

    text-transform:
        uppercase;

    letter-spacing:
        0.08em;

    margin-bottom:
        8px;

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

    .stats-row {

        gap:
            8px;

    }

    .badge {

        font-size:
            0.82rem;

        padding:
            8px 13px;

    }

}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# BLACK HOLE EFFECT
# =========================================================

if st.session_state.show_black_hole:

    st.markdown(
        """
        <div class="black-hole"></div>
        """,
        unsafe_allow_html=True,
    )

    # Clear the effect flag after rendering.
    st.session_state.show_black_hole = False


# =========================================================
# HEADER
# =========================================================

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


# =========================================================
# CONTROL CARD
# =========================================================

st.markdown(
    """
    <div class="glass-card">
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "### 🎯 Search Control"
)


# =========================================================
# CURRENT MC
# =========================================================

if st.session_state.running:

    display_mc = str(
        st.session_state.current_mc
    )

else:

    display_mc = str(
        st.session_state.start_mc or ""
    )


# IMPORTANT:
# Do not use a session-state value as the widget value
# when the widget has a key.
#
# This prevents the "Current MC is stuck" behavior.

if "mc_input_value" not in st.session_state:

    st.session_state.mc_input_value = display_mc


if st.session_state.running:

    # While running, force the visible value to current MC.
    st.session_state.mc_input_value = display_mc


start_input = st.text_input(
    "Current MC Number",
    placeholder="Example: 1066434",
    disabled=st.session_state.running,
    key="mc_input_value",
)


st.caption(
    "Enter the starting MC. The app automatically searches "
    "one MC at a time. Press STOP to stop."
)


# =========================================================
# BUTTONS
# =========================================================

col1, col2, col3 = st.columns(
    [1, 1, 1]
)


with col1:

    start_button = st.button(
        "▶  Start Search",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running,
    )


with col2:

    stop_button = st.button(
        "■  Stop",
        use_container_width=True,
        disabled=not st.session_state.running,
    )


with col3:

    clear_button = st.button(
        "◉  Clear History",
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

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = False

    st.session_state.current_mc = None

    st.session_state.start_mc = ""

    st.session_state.mc_input_value = ""

    st.session_state.show_black_hole = True

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    st.session_state.running = False

    # IMPORTANT:
    # Do NOT destroy current_mc here.
    #
    # This allows the user to see the last MC that was
    # processed and prevents the search bar from appearing
    # broken.

    if st.session_state.current_mc is not None:

        st.session_state.start_mc = str(
            st.session_state.current_mc
        )

        st.session_state.mc_input_value = str(
            st.session_state.current_mc
        )

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

    st.session_state.mc_input_value = cleaned

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
                {st.session_state.current_mc:,}
            </b>

            <br><br>

            <small style="color:#9da6c0;">
                Searching sequentially...
                Press STOP at any time.
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

            <br><br>

            <small style="color:#9da6c0;">
                {st.session_state.searched_count}
                MC number(s) processed.
            </small>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# AUTOMATIC SEARCH LOOP
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


    # -----------------------------------------------------
    # Move to next MC
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )


    # -----------------------------------------------------
    # Keep the visible current MC updated
    # -----------------------------------------------------

    st.session_state.mc_input_value = str(
        current_mc + 1
    )


    # -----------------------------------------------------
    # Small delay
    # -----------------------------------------------------

    time.sleep(0.5)


    # -----------------------------------------------------
    # Run next MC
    # -----------------------------------------------------

    st.rerun()


# =========================================================
# RESULTS
# =========================================================

if st.session_state.results:

    st.markdown(
        """
        <div class="glass-card">
        """,
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
                    "Not available",
                ),

                "Broker/Carrier": result.get(
                    "Broker/Carrier",
                    "Not available",
                ),

                "Operating Status": result.get(
                    "Operating Status",
                    "INACTIVE",
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
    # NORMALIZE VALUES
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


    # =====================================================
    # COLORED BADGES
    # =====================================================

    st.markdown(
        f"""
        <div class="stats-row">

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

    c1, c2, c3, c4 = st.columns(
        4
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
    # FILTERS
    # =====================================================

    st.markdown(
        "### 🔎 Filter Results"
    )


    filter_col1, filter_col2 = st.columns(
        2
    )


    with filter_col1:

        st.markdown(
            '<div class="filter-title">Operating Status</div>',
            unsafe_allow_html=True,
        )

        status_filter = st.selectbox(
            "Operating Status",
            [
                "All",
                "ACTIVE",
                "INACTIVE",
            ],
            label_visibility="collapsed",
            key="status_filter",
        )


    with filter_col2:

        st.markdown(
            '<div class="filter-title">Business Type</div>',
            unsafe_allow_html=True,
        )

        type_filter = st.selectbox(
            "Business Type",
            [
                "All",
                "CARRIER",
                "BROKER",
            ],
            label_visibility="collapsed",
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
    # FILTERED COUNT
    # =====================================================

    st.caption(
        f"{len(filtered_df)} matching MC number(s)"
    )


    # =====================================================
    # COLOR TABLE
    # =====================================================

    def color_status(value):

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


    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
    )


    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True,
    )


    # =========================================================
    # EXPORT CARD
    # =========================================================

    st.markdown(
        """
        <div class="glass-card">

            <h3>⬇ Export Filtered Data</h3>

            <div class="subtitle">
                Downloads contain only the records matching
                your selected filters.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
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


    # =====================================================
    # ERRORS
    # =====================================================

    if errors:

        st.markdown(
            """
            <div class="glass-card">
            """,
            unsafe_allow_html=True,
        )

        with st.expander(
            "⚠ Search messages"
        ):

            for error in errors:

                st.write(error)

        st.markdown(
            """
            </div>
            """,
            unsafe_allow_html=True,
        )
