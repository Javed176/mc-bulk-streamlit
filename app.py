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
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(170, 70, 255, 0.18),
            transparent 28%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(30, 80, 255, 0.10),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #030409 0%,
            #080b14 50%,
            #030409 100%
        );

    color: #f7f8ff;
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
   HEADER
   ===================================================== */

.hero {

    padding: 34px;

    border-radius: 30px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.12),
            rgba(255,255,255,0.035)
        );

    border: 1px solid rgba(255,255,255,0.12);

    box-shadow:
        0 25px 80px rgba(0,0,0,0.45),
        inset 0 1px 0 rgba(255,255,255,0.10);

    backdrop-filter: blur(30px);

    margin-bottom: 22px;

}


.hero-title {

    font-size: 3.2rem;

    font-weight: 800;

    letter-spacing: -0.055em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #9fb0ff,
            #d58cff,
            #ffffff
        );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;

    margin: 0;

}


.subtitle {

    color: rgba(230,235,255,0.60);

    margin-top: 7px;

    font-size: 1rem;

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
        1px solid rgba(255,255,255,0.11);

    border-radius: 28px;

    padding: 27px;

    margin-bottom: 20px;

    box-shadow:
        0 20px 70px rgba(0,0,0,0.40),
        inset 0 1px 0 rgba(255,255,255,0.07);

    backdrop-filter:
        blur(25px)
        saturate(150%);

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
        18px !important;

    transition:
        all 0.25s ease !important;

}


div[data-baseweb="input"]:focus-within {

    border-color:
        rgba(105,135,255,0.90) !important;

    box-shadow:
        0 0 0 3px rgba(90,115,255,0.13),
        0 0 35px rgba(80,100,255,0.20);

}


input {

    color: #ffffff !important;

    font-size: 1.05rem !important;

}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button {

    min-height: 52px;

    border-radius: 18px !important;

    border:
        1px solid rgba(255,255,255,0.15) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.12),
            rgba(255,255,255,0.045)
        ) !important;

    color: #ffffff !important;

    font-weight: 700 !important;

    box-shadow:
        0 12px 35px rgba(0,0,0,0.28),
        inset 0 1px 0 rgba(255,255,255,0.10);

    transition:
        all 0.20s ease !important;

}


.stButton > button:hover {

    transform:
        translateY(-3px)
        scale(1.015);

    border-color:
        rgba(125,145,255,0.55) !important;

    background:
        linear-gradient(
            135deg,
            rgba(90,120,255,0.30),
            rgba(150,70,255,0.20)
        ) !important;

    box-shadow:
        0 15px 45px rgba(60,80,255,0.25),
        0 0 28px rgba(100,80,255,0.18);

}


.stButton > button:active {

    transform:
        scale(0.96);

}


/* =====================================================
   PRIMARY BUTTON
   ===================================================== */

button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            #536dff,
            #8d42ff
        ) !important;

    border-color:
        rgba(180,190,255,0.55) !important;

    box-shadow:
        0 12px 35px rgba(80,90,255,0.35),
        0 0 30px rgba(110,70,255,0.18);

}


button[kind="primary"]:hover {

    background:
        linear-gradient(
            135deg,
            #6680ff,
            #a052ff
        ) !important;

    box-shadow:
        0 16px 50px rgba(90,90,255,0.45),
        0 0 35px rgba(150,70,255,0.25);

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
        1px solid rgba(255,255,255,0.10);

    border-radius: 22px;

    padding: 18px;

    box-shadow:
        0 15px 40px rgba(0,0,0,0.25);

    backdrop-filter: blur(18px);

}


div[data-testid="stMetricValue"] {

    color: #ffffff !important;

}


/* =====================================================
   BADGES
   ===================================================== */

.badges {

    display: flex;

    gap: 10px;

    flex-wrap: wrap;

    margin: 20px 0;

}


.badge {

    display: inline-block;

    padding: 9px 15px;

    border-radius: 999px;

    font-size: 0.88rem;

    font-weight: 700;

    border: 1px solid;

    backdrop-filter: blur(15px);

}


.badge-active {

    color: #55ff9b;

    background: rgba(40,255,130,0.08);

    border-color: rgba(70,255,150,0.25);

    box-shadow: 0 0 18px rgba(50,255,130,0.10);

}


.badge-inactive {

    color: #ff6178;

    background: rgba(255,60,90,0.08);

    border-color: rgba(255,70,100,0.23);

}


.badge-carrier {

    color: #70a8ff;

    background: rgba(70,130,255,0.09);

    border-color: rgba(80,140,255,0.25);

}


.badge-broker {

    color: #d18aff;

    background: rgba(170,70,255,0.09);

    border-color: rgba(180,80,255,0.25);

}


/* =====================================================
   LIVE STATUS
   ===================================================== */

.live-dot {

    display: inline-block;

    width: 10px;
    height: 10px;

    border-radius: 50%;

    background: #38ff91;

    box-shadow:
        0 0 8px #38ff91,
        0 0 20px #38ff91;

    margin-right: 9px;

    animation:
        pulse 1.3s infinite;

}


@keyframes pulse {

    0% {
        transform: scale(.8);
        opacity: .55;
    }

    50% {
        transform: scale(1.25);
        opacity: 1;
    }

    100% {
        transform: scale(.8);
        opacity: .55;
    }

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
        0 20px 60px rgba(0,0,0,0.35);

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
            #000 0%,
            #000 25%,
            #280044 30%,
            #7625ff 43%,
            #ff42d4 49%,
            #151020 60%,
            transparent 72%
        );

    box-shadow:
        0 0 40px #792cff,
        0 0 100px #541cff,
        0 0 180px rgba(255,40,210,0.40);

    animation:
        blackHole 1.45s
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

        width: 360px;
        height: 360px;

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

        font-size: 2.3rem;

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
# BLACK HOLE
# =========================================================

if st.session_state.show_black_hole:

    st.markdown(
        '<div class="black-hole"></div>',
        unsafe_allow_html=True,
    )

    time.sleep(1.45)

    st.session_state.show_black_hole = False

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = False

    st.session_state.current_mc = None

    st.session_state.start_mc = ""

    st.rerun()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
<div class="hero">

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

st.markdown("### 🎯 Search Control")


# =========================================================
# CURRENT MC
# =========================================================

if st.session_state.running:

    display_mc = str(
        st.session_state.current_mc
    )

else:

    display_mc = st.session_state.get(
        "start_mc",
        "",
    )


# IMPORTANT:
# No key is used here.
# This prevents the StreamlitAPIException.

start_input = st.text_input(
    "Current MC Number",
    value=display_mc,
    placeholder="Example: 1800000",
    disabled=st.session_state.running,
)


st.caption(
    "Enter the starting MC. "
    "The app automatically searches one MC at a time. "
    "Press STOP to stop."
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

    st.session_state.show_black_hole = True

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    st.session_state.running = False

    st.session_state.current_mc = None

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
    # Advance MC
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )


    # -----------------------------------------------------
    # Delay
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


    # =====================================================
    # TABLE COLORS
    # =====================================================

    def color_status(value):

        value = str(value).upper()

        if value == "ACTIVE":

            return (
                "color:#39ff88;"
                "font-weight:800;"
                "background-color:rgba(40,255,130,0.07);"
            )

        if value == "INACTIVE":

            return (
                "color:#ff536d;"
                "font-weight:800;"
                "background-color:rgba(255,50,80,0.06);"
            )

        return ""


    def color_type(value):

        value = str(value).upper()

        if value == "BROKER":

            return (
                "color:#cf8aff;"
                "font-weight:800;"
                "background-color:rgba(180,80,255,0.06);"
            )

        if value == "CARRIER":

            return (
                "color:#62a4ff;"
                "font-weight:800;"
                "background-color:rgba(70,130,255,0.06);"
            )

        return ""


    styled_df = (
        df.style
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
    # FILTERS
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 🔎 Filter Results"
    )


    filter_col1, filter_col2 = st.columns(2)


    with filter_col1:

        status_filter = st.selectbox(
            "Operating Status",
            [
                "ALL",
                "ACTIVE",
                "INACTIVE",
            ],
        )


    with filter_col2:

        type_filter = st.selectbox(
            "Broker / Carrier",
            [
                "ALL",
                "CARRIER",
                "BROKER",
            ],
        )


    filtered_df = df.copy()


    if status_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df[
                "Operating Status"
            ].astype(str).str.upper()
            == status_filter
        ]


    if type_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ].astype(str).str.upper()
            == type_filter
        ]


    st.caption(
        f"Showing {len(filtered_df):,} "
        f"of {len(df):,} results"
    )


    st.dataframe(
        filtered_df.style
        .map(
            color_status,
            subset=["Operating Status"],
        )
        .map(
            color_type,
            subset=["Broker/Carrier"],
        ),
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
        "### ⬇ Export Filtered Data"
    )


    # =====================================================
    # CSV
    # =====================================================

    csv_data = filtered_df.to_csv(
        index=False
    ).encode(
        "utf-8"
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


    download_col1, download_col2 = st.columns(2)


    with download_col1:

        st.download_button(
            "⬇ Download CSV",
            data=csv_data,
            file_name="mc_filtered_results.csv",
            mime="text/csv",
            use_container_width=True,
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
