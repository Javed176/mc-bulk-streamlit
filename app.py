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

if "results" not in st.session_state:
    st.session_state.results = []

if "searched_count" not in st.session_state:
    st.session_state.searched_count = 0


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
            rgba(80, 110, 255, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(170, 70, 255, 0.16),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #05060a 0%,
            #0b0d14 50%,
            #05060a 100%
        );

    color: #f5f7ff;
}


.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}


/* =====================================================
   HERO
   ===================================================== */

.hero-card {
    padding: 30px;
    border-radius: 28px;
    margin-bottom: 22px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.12),
            rgba(255,255,255,0.035)
        );

    border: 1px solid rgba(255,255,255,0.12);

    box-shadow:
        0 25px 80px rgba(0,0,0,0.45),
        inset 0 1px 0 rgba(255,255,255,0.08);

    backdrop-filter: blur(25px);
}


.hero-title {
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -0.05em;

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
    color: rgba(235,240,255,0.60);
    font-size: 1rem;
}


/* =====================================================
   GLASS CARD
   ===================================================== */

.glass-card {
    padding: 25px;
    border-radius: 26px;
    margin-bottom: 20px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.095),
            rgba(255,255,255,0.025)
        );

    border: 1px solid rgba(255,255,255,0.10);

    box-shadow:
        0 20px 65px rgba(0,0,0,0.35),
        inset 0 1px 0 rgba(255,255,255,0.06);

    backdrop-filter: blur(22px);
}


/* =====================================================
   CURRENT MC
   ===================================================== */

.current-mc-card {
    padding: 22px 25px;
    margin-top: 18px;

    border-radius: 22px;

    background:
        linear-gradient(
            135deg,
            rgba(70,95,255,0.17),
            rgba(130,70,255,0.08)
        );

    border: 1px solid rgba(120,140,255,0.25);

    box-shadow:
        0 15px 45px rgba(60,70,200,0.15);
}


.current-mc-title {
    color: #9da6c0;
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.09em;
}


.current-mc-value {
    color: #ffffff;
    font-size: 2.5rem;
    font-weight: 850;
    line-height: 1.15;
    margin-top: 5px;
}


.current-mc-status {
    color: #858da5;
    font-size: 0.85rem;
    margin-top: 5px;
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

    color: #ffffff !important;

    font-weight: 700 !important;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.25),
        inset 0 1px 0 rgba(255,255,255,0.10);

    transition:
        all 0.22s ease !important;
}


.stButton > button:hover {

    transform:
        translateY(-2px)
        scale(1.015);

    background:
        linear-gradient(
            135deg,
            rgba(90,120,255,0.35),
            rgba(150,70,255,0.22)
        ) !important;

    box-shadow:
        0 14px 40px rgba(80,100,255,0.30),
        0 0 25px rgba(100,80,255,0.18);
}


.stButton > button:active {
    transform: scale(0.97);
}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {

    border-radius: 18px !important;

    background:
        rgba(255,255,255,0.055) !important;

    border:
        1px solid
        rgba(255,255,255,0.12) !important;
}


div[data-baseweb="input"]:focus-within {

    border-color:
        rgba(110,140,255,0.80) !important;

    box-shadow:
        0 0 0 3px
        rgba(90,120,255,0.12);
}


input {
    color: white !important;
}


/* =====================================================
   METRICS
   ===================================================== */

div[data-testid="stMetric"] {

    border-radius: 22px;

    padding: 18px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.085),
            rgba(255,255,255,0.025)
        );

    border:
        1px solid
        rgba(255,255,255,0.09);

    box-shadow:
        0 15px 40px rgba(0,0,0,0.25);
}


div[data-testid="stMetricValue"] {
    color: white !important;
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

    animation: pulse 1.3s infinite;

    margin-right: 8px;
}


@keyframes pulse {

    0% {
        transform: scale(0.8);
        opacity: 0.55;
    }

    50% {
        transform: scale(1.2);
        opacity: 1;
    }

    100% {
        transform: scale(0.8);
        opacity: 0.55;
    }
}


/* =====================================================
   BLACK HOLE
   ===================================================== */

.black-hole {

    position: fixed;

    left: 50%;
    top: 50%;

    transform: translate(-50%, -50%);

    width: 230px;
    height: 230px;

    border-radius: 50%;

    z-index: 999999;

    background:
        radial-gradient(
            circle,
            #000 0%,
            #000 25%,
            #17002c 30%,
            #6d1cff 42%,
            #ff4fd8 48%,
            #151020 58%,
            transparent 70%
        );

    box-shadow:
        0 0 35px #7a2cff,
        0 0 100px #5a1cff,
        0 0 180px rgba(255,40,210,0.35);

    animation:
        blackHole 1.25s
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
        width: 270px;
        height: 270px;
        opacity: 1;
    }

    60% {
        width: 340px;
        height: 340px;
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

    .current-mc-value {
        font-size: 1.9rem;
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
        <div class="hero-title">✦ MC Search</div>
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

st.subheader("🎯 Search Control")


# =========================================================
# START MC
# =========================================================

start_input = st.text_input(
    "Start MC",
    value=st.session_state.start_mc,
    placeholder="Example: 1800000",
    disabled=st.session_state.running,
)


st.caption(
    "Enter the starting MC. The app searches sequentially "
    "one MC at a time. Press STOP whenever you want."
)


# =========================================================
# CURRENT MC
# =========================================================

if st.session_state.current_mc is None:

    current_number = "—"
    current_status = "Waiting for search"

elif st.session_state.running:

    current_number = (
        f"{int(st.session_state.current_mc):,}"
    )

    current_status = (
        "Search running • next MC will update automatically"
    )

else:

    current_number = (
        f"{int(st.session_state.current_mc):,}"
    )

    current_status = "Search stopped"


st.markdown(
    f"""
    <div class="current-mc-card">
        <div class="current-mc-title">
            Current MC Number
        </div>

        <div class="current-mc-value">
            {current_number}
        </div>

        <div class="current-mc-status">
            {current_status}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.write("")


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


st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# CLEAR HISTORY
# =========================================================

if clear_button:

    st.markdown(
        '<div class="black-hole"></div>',
        unsafe_allow_html=True,
    )

    time.sleep(0.8)

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


    start_number = int(cleaned)


    # -----------------------------------------------------
    # IMPORTANT:
    #
    # DO NOT CLEAR st.session_state.results HERE.
    #
    # Previous searches must remain visible.
    # Only Clear History removes them.
    # -----------------------------------------------------

    st.session_state.start_mc = str(
        start_number
    )

    st.session_state.current_mc = (
        start_number
    )

    st.session_state.running = True

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    # Keep:
    # - results
    # - searched_count
    # - current_mc
    #
    # Only stop the process.

    st.session_state.running = False

    st.rerun()


# =========================================================
# AUTOMATIC SEARCH
# =========================================================

if st.session_state.running:

    current_mc = int(
        st.session_state.current_mc
    )


    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="glass-card">

            <span class="live-dot"></span>

            <b>Searching sequential MC numbers...</b>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    result = search_one(
        str(current_mc)
    )


    # -----------------------------------------------------
    # STORE
    # -----------------------------------------------------

    st.session_state.results.append(
        result
    )

    st.session_state.searched_count += 1


    # -----------------------------------------------------
    # NEXT MC
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )


    time.sleep(0.5)


    # -----------------------------------------------------
    # RERUN
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
    # NORMALIZE
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


    st.subheader("📊 Search Results")


    # =====================================================
    # NATIVE STATUS DISPLAY
    #
    # NO HTML BADGES.
    # This prevents the raw <span> problem.
    # =====================================================

    badge1, badge2, badge3, badge4 = st.columns(4)


    with badge1:

        st.success(
            f"● Active  {active_count}"
        )


    with badge2:

        st.error(
            f"● Inactive  {inactive_count}"
        )


    with badge3:

        st.info(
            f"◆ Carriers  {carrier_count}"
        )


    with badge4:

        st.warning(
            f"◆ Brokers  {broker_count}"
        )


    # =====================================================
    # METRICS
    # =====================================================

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

        status_filter = st.multiselect(
            "Operating Status",
            options=[
                "ACTIVE",
                "INACTIVE",
            ],
            default=[],
            key="status_filter",
        )


    with filter2:

        type_filter = st.multiselect(
            "Broker / Carrier",
            options=[
                "CARRIER",
                "BROKER",
            ],
            default=[],
            key="type_filter",
        )


    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered_df = df.copy()


    if status_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Operating Status"
            ].isin(
                status_filter
            )
        ]


    if type_filter:

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ].isin(
                type_filter
            )
        ]


    st.caption(
        f"Showing {len(filtered_df):,} "
        f"of {len(df):,} records"
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
                "color:#ff5c72;"
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


    st.subheader(
        "⬇ Export Filtered Results"
    )


    # -----------------------------------------------------
    # CSV
    # -----------------------------------------------------

    csv_data = (
        filtered_df
        .to_csv(index=False)
        .encode("utf-8")
    )


    # -----------------------------------------------------
    # EXCEL
    # -----------------------------------------------------

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


    export1, export2 = st.columns(2)


    with export1:

        st.download_button(
            "⬇ Download CSV",
            data=csv_data,
            file_name="mc_filtered_results.csv",
            mime="text/csv",
            use_container_width=True,
        )


    with export2:

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
    # SEARCH MESSAGES
    # =====================================================

    if errors:

        with st.expander(
            "⚠ Search messages"
        ):

            for error in errors:

                st.write(error)
