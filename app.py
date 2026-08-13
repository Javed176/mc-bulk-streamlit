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

if "running" not in st.session_state:
    st.session_state.running = False

if "current_mc" not in st.session_state:
    st.session_state.current_mc = None

if "start_mc" not in st.session_state:
    st.session_state.start_mc = ""

if "searched_count" not in st.session_state:
    st.session_state.searched_count = 0

if "results" not in st.session_state:
    st.session_state.results = []

if "show_black_hole" not in st.session_state:
    st.session_state.show_black_hole = False

if "mc_input" not in st.session_state:
    st.session_state.mc_input = ""


# =========================================================
# MODERN GLASS UI
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
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(170, 70, 255, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(30, 100, 255, 0.10),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #04050a 0%,
            #0a0d16 48%,
            #04050a 100%
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
   HEADINGS
   ===================================================== */

h1 {

    font-size: 3rem !important;

    font-weight: 800 !important;

    letter-spacing: -0.055em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #aebdff,
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
        0 25px 80px
        rgba(0,0,0,0.42),

        inset 0 1px 0
        rgba(255,255,255,0.09);

    backdrop-filter:
        blur(28px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(28px)
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

    font-size:
        1rem;

    margin-top:
        -18px;

    margin-bottom:
        10px;

}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {

    background:
        rgba(255,255,255,0.065) !important;

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
        rgba(100,125,255,0.13),

        0 0 35px
        rgba(80,100,255,0.20);

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
        rgba(255,255,255,0.15) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.13),
            rgba(255,255,255,0.045)
        ) !important;

    color:
        #ffffff !important;

    font-weight:
        700 !important;

    min-height:
        52px;

    transition:
        transform 0.18s ease,
        box-shadow 0.18s ease,
        background 0.18s ease;

    box-shadow:
        0 10px 30px
        rgba(0,0,0,0.25),

        inset 0 1px 0
        rgba(255,255,255,0.10);

}


.stButton > button:hover {

    transform:
        translateY(-3px)
        scale(1.015);

    background:
        linear-gradient(
            135deg,
            rgba(90,125,255,0.35),
            rgba(145,70,255,0.24)
        ) !important;

    box-shadow:
        0 15px 40px
        rgba(70,95,255,0.30),

        0 0 30px
        rgba(100,80,255,0.20);

}


.stButton > button:active {

    transform:
        translateY(1px)
        scale(0.97);

}


/* =====================================================
   PRIMARY BUTTON
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
        rgba(150,170,255,0.55) !important;

    box-shadow:
        0 10px 35px
        rgba(75,90,255,0.35),

        0 0 25px
        rgba(110,80,255,0.20);

}


button[kind="primary"]:hover {

    background:
        linear-gradient(
            135deg,
            #637cff,
            #8a50ff
        ) !important;

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
        0 0 20px #36ff8a;

    animation:
        pulse 1.3s infinite;

    margin-right:
        8px;

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
   STATUS BADGES
   ===================================================== */

.badge {

    display: inline-block;

    padding:
        8px 15px;

    margin:
        4px 5px 4px 0;

    border-radius:
        999px;

    font-weight:
        700;

    font-size:
        0.90rem;

    border:
        1px solid
        rgba(255,255,255,0.12);

    backdrop-filter:
        blur(10px);

}


.badge-active {

    color:
        #52ff9a;

    background:
        rgba(40,255,130,0.08);

    box-shadow:
        0 0 18px
        rgba(40,255,130,0.10);

}


.badge-inactive {

    color:
        #ff6078;

    background:
        rgba(255,50,80,0.08);

}


.badge-carrier {

    color:
        #65a7ff;

    background:
        rgba(70,130,255,0.09);

}


.badge-broker {

    color:
        #ca8cff;

    background:
        rgba(170,70,255,0.09);

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

    border-radius:
        50%;

    z-index:
        999999;

    background:
        radial-gradient(
            circle,
            #000 0%,
            #000 25%,
            #19002e 30%,
            #6d1cff 42%,
            #ff4fd8 49%,
            #171020 59%,
            transparent 72%
        );

    box-shadow:
        0 0 35px
        #7a2cff,

        0 0 100px
        #5a1cff,

        0 0 180px
        rgba(255,40,210,0.35);

    animation:
        blackHole
        1.25s
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

}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# BLACK HOLE ANIMATION
# =========================================================

if st.session_state.show_black_hole:

    st.markdown(
        '<div class="black-hole"></div>',
        unsafe_allow_html=True,
    )

    time.sleep(1.0)

    st.session_state.show_black_hole = False

    st.rerun()


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
    '<div class="glass-card">',
    unsafe_allow_html=True,
)

st.markdown("### 🎯 Search Control")


# =========================================================
# CURRENT MC DISPLAY
# IMPORTANT:
# Set widget state BEFORE creating text_input.
# Never modify it after text_input has been created.
# =========================================================

if st.session_state.running:

    display_mc = str(
        st.session_state.current_mc
    )

elif st.session_state.current_mc is not None:

    display_mc = str(
        st.session_state.current_mc
    )

elif st.session_state.start_mc:

    display_mc = str(
        st.session_state.start_mc
    )

else:

    display_mc = ""


# Keep widget synchronized safely.
# This happens BEFORE st.text_input is created.

if st.session_state.mc_input != display_mc:

    st.session_state.mc_input = display_mc


start_input = st.text_input(
    "Current MC Number",
    placeholder="Example: 1800000",
    disabled=st.session_state.running,
    key="mc_input",
)


st.caption(
    "Enter the starting MC. The app automatically searches "
    "one MC at a time. Press STOP to stop."
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

    st.session_state.show_black_hole = True

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = False

    st.session_state.current_mc = None

    st.session_state.start_mc = ""

    st.session_state.mc_input = ""

    st.rerun()


# =========================================================
# STOP
# =========================================================
#
# IMPORTANT FIX:
#
# DO NOT set current_mc = None.
#
# Instead, preserve the MC currently being searched and
# make it the new starting MC.
#
# =========================================================

if stop_button:

    if st.session_state.current_mc is not None:

        st.session_state.start_mc = str(
            st.session_state.current_mc
        )

        st.session_state.mc_input = str(
            st.session_state.current_mc
        )

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


    st.session_state.start_mc = cleaned

    st.session_state.current_mc = int(
        cleaned
    )

    st.session_state.mc_input = cleaned

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = True

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
Searching MC {st.session_state.current_mc:,}
</b>

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
    # Move to NEXT MC
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )


    # -----------------------------------------------------
    # Keep input synchronized for the next run
    # -----------------------------------------------------

    st.session_state.mc_input = str(
        current_mc + 1
    )


    # -----------------------------------------------------
    # Small delay
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
    # NORMALIZE STATUS / TYPE
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
    # FILTERS
    # =====================================================

    st.markdown("### 🔎 Filters")


    filter_col1, filter_col2 = st.columns(2)


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
            ].isin(status_filter)
        ]

    else:

        filtered_df = filtered_df.iloc[0:0]


    if type_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ].isin(type_filter)
        ]

    else:

        filtered_df = filtered_df.iloc[0:0]


    # =====================================================
    # FILTERED COUNT
    # =====================================================

    st.caption(
        f"Showing {len(filtered_df):,} matching MC records."
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

        with st.expander(
            "⚠ Search messages"
        ):

            for error in errors:

                st.write(error)
