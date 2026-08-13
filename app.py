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
    "last_searched_mc": None,
    "searched_count": 0,
    "results": [],
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
   CONTAINER
   ===================================================== */

.block-container {
    max-width: 1450px;
    padding-top: 2.2rem;
    padding-bottom: 4rem;
}


/* =====================================================
   TEXT
   ===================================================== */

h1, h2, h3, h4 {
    color: #ffffff !important;
}

.hero-title {
    font-size: 3.1rem;
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
    color: rgba(235,240,255,0.62);
    font-size: 1rem;
    margin-top: 5px;
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
        1px solid
        rgba(255,255,255,0.12);

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
   CURRENT MC
   ===================================================== */

.current-mc-box {
    background:
        linear-gradient(
            135deg,
            rgba(90,110,255,0.16),
            rgba(130,70,255,0.08)
        );

    border:
        1px solid
        rgba(125,145,255,0.25);

    border-radius: 22px;

    padding: 22px;

    text-align: center;

    box-shadow:
        0 15px 45px rgba(50,70,180,0.18);
}

.current-mc-label {
    color: #9da6c0;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.current-mc-number {
    color: #ffffff;
    font-size: 2.2rem;
    font-weight: 800;
    margin-top: 5px;
}

.current-mc-hint {
    color: #858da5;
    font-size: 0.82rem;
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
    color: #ffffff !important;
    font-size: 1.05rem !important;
}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button,
.stDownloadButton > button {

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

    color: #ffffff !important;

    font-weight: 700 !important;

    min-height: 50px;

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease,
        background 0.2s ease;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.25),
        inset 0 1px 0 rgba(255,255,255,0.10);
}

.stButton > button:hover,
.stDownloadButton > button:hover {

    transform:
        translateY(-3px)
        scale(1.015);

    background:
        linear-gradient(
            135deg,
            rgba(105,130,255,0.30),
            rgba(130,80,255,0.20)
        ) !important;

    box-shadow:
        0 12px 35px rgba(75,95,255,0.28),
        0 0 25px rgba(90,110,255,0.18);
}

.stButton > button:active,
.stDownloadButton > button:active {
    transform: scale(0.96);
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
        0 15px 40px rgba(0,0,0,0.25);

    backdrop-filter: blur(20px);
}

div[data-testid="stMetricValue"] {
    color: #ffffff !important;
}


/* =====================================================
   SELECTBOX
   ===================================================== */

div[data-baseweb="select"] > div {
    background:
        rgba(255,255,255,0.065) !important;

    border:
        1px solid
        rgba(255,255,255,0.12) !important;

    border-radius: 16px !important;
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
            #000 27%,
            #17002c 30%,
            #6d1cff 43%,
            #ff4fd8 48%,
            #151020 58%,
            transparent 70%
        );

    box-shadow:
        0 0 35px #7a2cff,
        0 0 100px #5a1cff,
        0 0 180px rgba(255,40,210,0.35);

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
        font-size: 2.2rem;
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
    <div class="hero-title">✦ MC Search</div>
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

st.subheader("🎯 Search Control")


# ---------------------------------------------------------
# START MC INPUT
#
# IMPORTANT:
# We NEVER modify st.session_state.start_mc_input
# after creating this widget.
# This prevents StreamlitAPIException.
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


# ---------------------------------------------------------
# CURRENT MC DISPLAY
# ---------------------------------------------------------

if st.session_state.running:

    current_display = st.session_state.current_mc

    hint = "Search running • next MC will update automatically"

elif st.session_state.last_searched_mc is not None:

    current_display = st.session_state.last_searched_mc

    hint = "Search stopped"

elif st.session_state.start_mc:

    current_display = st.session_state.start_mc

    hint = "Ready to search"

else:

    current_display = "—"

    hint = "Enter a starting MC"


st.markdown(
    f"""
<div class="current-mc-box">

    <div class="current-mc-label">
        Current MC Number
    </div>

    <div class="current-mc-number">
        {current_display:,}
    </div>

    <div class="current-mc-hint">
        {hint}
    </div>

</div>
""",
    unsafe_allow_html=True,
)


st.write("")


# =========================================================
# BUTTONS
# =========================================================

button1, button2, button3 = st.columns(3)


with button1:

    start_button = st.button(
        "▶ Start Search",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running,
    )


with button2:

    stop_button = st.button(
        "■ Stop",
        use_container_width=True,
        disabled=not st.session_state.running,
    )


with button3:

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
    st.session_state.start_mc = ""
    st.session_state.current_mc = None
    st.session_state.last_searched_mc = None
    st.session_state.searched_count = 0
    st.session_state.results = []

    # IMPORTANT:
    # Do NOT modify start_mc_input here.
    # It is a widget-managed key.

    st.rerun()


# =========================================================
# START SEARCH
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

    else:

        starting_mc = int(cleaned)

        st.session_state.start_mc = str(
            starting_mc
        )

        st.session_state.current_mc = (
            starting_mc
        )

        st.session_state.last_searched_mc = None

        st.session_state.searched_count = 0

        st.session_state.results = []

        st.session_state.running = True

        st.rerun()


# =========================================================
# STOP SEARCH
# =========================================================

if stop_button:

    st.session_state.running = False

    # IMPORTANT:
    # Do NOT reset current_mc.
    # Do NOT reset start_mc.
    # Do NOT modify widget state.

    st.rerun()


# =========================================================
# LIVE SEARCH
# =========================================================

if st.session_state.running:

    current_mc = int(
        st.session_state.current_mc
    )

    # -----------------------------------------------------
    # LIVE STATUS
    # -----------------------------------------------------

    st.markdown(
        """
<div class="glass-card">
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<span class="live-dot"></span>
<b>Searching MC {current_mc:,}</b>
""",
        unsafe_allow_html=True,
    )

    st.caption(
        "Searching sequential MC numbers automatically..."
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # SEARCH ONE MC
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

    st.session_state.last_searched_mc = (
        current_mc
    )

    # -----------------------------------------------------
    # NEXT MC
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
    # DELAY
    # -----------------------------------------------------

    time.sleep(0.5)

    # -----------------------------------------------------
    # RERUN
    # -----------------------------------------------------

    st.rerun()


# =========================================================
# STOPPED STATUS
# =========================================================

if (
    not st.session_state.running
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
# RESULTS
# =========================================================

if st.session_state.results:

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.subheader("📊 Search Results")

    # -----------------------------------------------------
    # BUILD DATAFRAME
    # -----------------------------------------------------

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


    df = pd.DataFrame(rows)


    # =====================================================
    # NORMALIZE FILTER COLUMNS
    # =====================================================

    df["Operating Status"] = (
        df["Operating Status"]
        .fillna("INACTIVE")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["Broker/Carrier"] = (
        df["Broker/Carrier"]
        .fillna("Not available")
        .astype(str)
        .str.upper()
        .str.strip()
    )


    # =====================================================
    # METRICS
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


    m1, m2, m3, m4 = st.columns(4)

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
    # FILTERS
    # =====================================================

    st.markdown("#### 🔎 Filters")

    filter1, filter2 = st.columns(2)


    with filter1:

        status_filter = st.selectbox(
            "Operating Status",
            [
                "ALL",
                "ACTIVE",
                "INACTIVE",
            ],
            index=0,
        )


    with filter2:

        type_filter = st.selectbox(
            "Broker / Carrier",
            [
                "ALL",
                "CARRIER",
                "BROKER",
            ],
            index=0,
        )


    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered_df = df.copy()


    if status_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df["Operating Status"]
            == status_filter
        ]


    if type_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df["Broker/Carrier"]
            == type_filter
        ]


    # =====================================================
    # FILTER SUMMARY
    # =====================================================

    st.caption(
        f"Showing {len(filtered_df):,} matching record(s)"
    )


    # =====================================================
    # TABLE COLORS
    # =====================================================

    def color_status(value):

        if value == "ACTIVE":

            return (
                "color:#39ff88;"
                "font-weight:800;"
                "background-color:rgba(57,255,136,0.08);"
            )

        if value == "INACTIVE":

            return (
                "color:#ff4d67;"
                "font-weight:800;"
                "background-color:rgba(255,77,103,0.08);"
            )

        return ""


    def color_type(value):

        if value == "BROKER":

            return (
                "color:#c084fc;"
                "font-weight:800;"
                "background-color:rgba(192,132,252,0.08);"
            )

        if value == "CARRIER":

            return (
                "color:#60a5fa;"
                "font-weight:800;"
                "background-color:rgba(96,165,250,0.08);"
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

    st.subheader("⬇ Export Filtered Data")

    st.caption(
        "Downloads contain only the records currently "
        "selected by the filters."
    )


    download1, download2 = st.columns(2)


    # =====================================================
    # CSV
    # =====================================================

    csv_data = (
        filtered_df
        .to_csv(index=False)
        .encode("utf-8")
    )


    with download1:

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


    with download2:

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
