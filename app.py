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
    "searched_count": 0,
    "last_searched_mc": None,
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
            circle at 10% 5%,
            rgba(75, 110, 255, 0.20),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(175, 70, 255, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(40, 100, 255, 0.08),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #04050a 0%,
            #0a0d16 45%,
            #05060b 100%
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
   HERO
   ===================================================== */

.hero-card {
    position: relative;

    padding: 32px;

    margin-bottom: 22px;

    border-radius: 30px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.11),
            rgba(255,255,255,0.035)
        );

    border:
        1px solid rgba(255,255,255,0.13);

    box-shadow:
        0 25px 80px rgba(0,0,0,0.42),
        inset 0 1px 0 rgba(255,255,255,0.10);

    backdrop-filter:
        blur(25px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(25px)
        saturate(160%);
}


.hero-title {
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -0.055em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #b9c8ff,
            #ffffff
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}


.hero-subtitle {
    margin-top: 5px;

    color: rgba(230,235,255,0.60);

    font-size: 1rem;
}


/* =====================================================
   GLASS CARD
   ===================================================== */

.glass-card {
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.095),
            rgba(255,255,255,0.028)
        );

    border:
        1px solid rgba(255,255,255,0.11);

    border-radius: 26px;

    padding: 26px;

    margin-bottom: 20px;

    box-shadow:
        0 20px 65px rgba(0,0,0,0.35),
        inset 0 1px 0 rgba(255,255,255,0.07);

    backdrop-filter:
        blur(22px)
        saturate(150%);

    -webkit-backdrop-filter:
        blur(22px)
        saturate(150%);
}


/* =====================================================
   CURRENT MC
   ===================================================== */

.current-mc-box {
    margin-top: 18px;

    padding: 20px 24px;

    border-radius: 22px;

    background:
        linear-gradient(
            135deg,
            rgba(90,115,255,0.15),
            rgba(145,70,255,0.08)
        );

    border:
        1px solid rgba(115,135,255,0.22);

    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.06),
        0 15px 45px rgba(50,70,180,0.12);
}


.current-mc-label {
    color: #9ca8c9;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 700;
}


.current-mc-number {
    margin-top: 4px;

    color: #ffffff;

    font-size: 2.15rem;

    font-weight: 800;

    letter-spacing: -0.04em;
}


.current-mc-hint {
    margin-top: 3px;

    color: #78839f;

    font-size: 0.82rem;
}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {
    background:
        rgba(255,255,255,0.055) !important;

    border:
        1px solid rgba(255,255,255,0.12) !important;

    border-radius:
        18px !important;

    transition:
        all 0.25s ease !important;
}


div[data-baseweb="input"]:focus-within {
    border-color:
        rgba(115,140,255,0.9) !important;

    box-shadow:
        0 0 0 3px rgba(90,120,255,0.13),
        0 0 35px rgba(80,100,255,0.15) !important;
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
        1px solid rgba(255,255,255,0.14) !important;

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
        transform 0.20s ease,
        box-shadow 0.20s ease,
        background 0.20s ease !important;
}


.stButton > button:hover,
.stDownloadButton > button:hover {
    transform:
        translateY(-2px)
        scale(1.015);

    background:
        linear-gradient(
            135deg,
            rgba(100,125,255,0.30),
            rgba(145,70,255,0.22)
        ) !important;

    box-shadow:
        0 15px 40px rgba(70,90,255,0.28),
        0 0 28px rgba(90,110,255,0.18);
}


.stButton > button:active,
.stDownloadButton > button:active {
    transform: scale(0.97);
}


/* =====================================================
   LIVE DOT
   ===================================================== */

.live-dot {
    display: inline-block;

    width: 10px;
    height: 10px;

    border-radius: 50%;

    margin-right: 8px;

    background: #39ff88;

    box-shadow:
        0 0 8px #39ff88,
        0 0 22px #39ff88;

    animation:
        pulse 1.3s infinite;
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

    font-weight: 750;

    border: 1px solid;
}


.badge-active {
    color: #58ff9b;

    background:
        rgba(50,255,135,0.08);

    border-color:
        rgba(60,255,145,0.20);

    box-shadow:
        0 0 18px rgba(50,255,130,0.08);
}


.badge-inactive {
    color: #ff6478;

    background:
        rgba(255,60,85,0.08);

    border-color:
        rgba(255,70,90,0.20);
}


.badge-carrier {
    color: #65a9ff;

    background:
        rgba(70,130,255,0.09);

    border-color:
        rgba(80,140,255,0.20);
}


.badge-broker {
    color: #c98aff;

    background:
        rgba(175,80,255,0.09);

    border-color:
        rgba(180,90,255,0.20);
}


/* =====================================================
   METRICS
   ===================================================== */

div[data-testid="stMetric"] {
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.09),
            rgba(255,255,255,0.025)
        );

    border:
        1px solid rgba(255,255,255,0.09);

    border-radius: 20px;

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
    border-radius: 20px;

    overflow: hidden;

    border:
        1px solid rgba(255,255,255,0.10);

    box-shadow:
        0 20px 60px rgba(0,0,0,0.30);
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

    width: 240px;
    height: 240px;

    border-radius: 50%;

    z-index: 999999;

    pointer-events: none;

    background:
        radial-gradient(
            circle,
            #000 0%,
            #000 25%,
            #18002e 29%,
            #7020ff 42%,
            #ff42d0 49%,
            #171020 59%,
            transparent 71%
        );

    box-shadow:
        0 0 40px #7b2cff,
        0 0 110px #5d1dff,
        0 0 190px rgba(255,40,210,0.35);

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

    20% {
        width: 250px;
        height: 250px;
        opacity: 1;
    }

    60% {
        width: 350px;
        height: 350px;
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

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero-title {
        font-size: 2.2rem;
    }

    .current-mc-number {
        font-size: 1.8rem;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def clean_mc(value):
    """
    Convert input such as:
        MC1800000
        mc 1800000
        1800000
    into:
        1800000
    """

    value = str(value or "").strip()

    value = (
        value
        .replace("MC", "")
        .replace("mc", "")
        .strip()
    )

    return value


def get_last_searched_mc():
    """
    Returns the highest MC actually searched.
    """

    if not st.session_state.results:
        return None

    numbers = []

    for result in st.session_state.results:

        value = result.get("MC Number", "")

        cleaned = clean_mc(value)

        if cleaned.isdigit():
            numbers.append(int(cleaned))

    if not numbers:
        return None

    return max(numbers)


def build_dataframe(results):
    """
    Convert internal result dictionaries into the
    visible dataframe.
    """

    rows = []

    for result in results:

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

    return pd.DataFrame(
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

st.markdown("### 🎯 Search Control")


# ---------------------------------------------------------
# START MC INPUT
#
# IMPORTANT:
# This widget owns its own key.
# We NEVER modify st.session_state.start_mc_input
# after the widget is created.
# ---------------------------------------------------------

last_searched = get_last_searched_mc()

default_start = ""

if st.session_state.running and st.session_state.current_mc is not None:

    default_start = str(
        st.session_state.current_mc
    )

elif last_searched is not None:

    default_start = str(
        last_searched + 1
    )


start_mc = st.text_input(
    "Start MC",
    value=default_start,
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
            "Search running • next MC will update automatically"
        )

    else:

        current_hint = (
            "Search stopped • press START to continue"
        )

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

    st.session_state.last_searched_mc = None

    st.session_state.clear_animation = False

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Do NOT erase current_mc.
    #
    # This means after STOP the user can still see
    # exactly which MC was being processed.
    # -----------------------------------------------------

    st.session_state.running = False

    st.rerun()


# =========================================================
# START
# =========================================================

if start_button:

    cleaned = clean_mc(start_mc)

    if not cleaned.isdigit():

        st.error(
            "Enter a valid numeric MC number."
        )

        st.stop()


    starting_mc = int(cleaned)


    # -----------------------------------------------------
    # Prevent duplicate searches.
    #
    # Example:
    #
    # Last searched = 1800003
    # User enters 1800003 again
    #
    # We automatically begin at:
    #
    # 1800004
    # -----------------------------------------------------

    existing_numbers = set()

    for result in st.session_state.results:

        value = clean_mc(
            result.get(
                "MC Number",
                "",
            )
        )

        if value.isdigit():

            existing_numbers.add(
                int(value)
            )


    while starting_mc in existing_numbers:

        starting_mc += 1


    # -----------------------------------------------------
    # DO NOT CLEAR RESULTS HERE.
    #
    # Old results remain until Clear History.
    # -----------------------------------------------------

    st.session_state.current_mc = (
        starting_mc
    )

    st.session_state.running = True

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

    <span class="live-dot"></span>

    <b>Searching sequential MC numbers...</b>

    <br>

    <small style="color:#9da6c0;">
        The current MC updates after every completed search.
    </small>

</div>
""",
        unsafe_allow_html=True,
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

    st.session_state.last_searched_mc = (
        current_mc
    )


    # -----------------------------------------------------
    # NEXT MC
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )


    # -----------------------------------------------------
    # SMALL DELAY
    # -----------------------------------------------------

    time.sleep(0.35)


    # -----------------------------------------------------
    # RERUN
    # -----------------------------------------------------

    st.rerun()


# =========================================================
# STOPPED MESSAGE
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
        Results are preserved until Clear History.
    </small>

</div>
""",
        unsafe_allow_html=True,
    )


# =========================================================
# RESULTS
# =========================================================

if st.session_state.results:

    df = build_dataframe(
        st.session_state.results
    )


    # =====================================================
    # RESULT HEADER
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 📊 Search Results"
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


    carrier_count = int(
        (
            df["Broker/Carrier"]
            .astype(str)
            .str.upper()
            == "CARRIER"
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
        f"Showing {len(filtered_df):,} of "
        f"{len(df):,} searched records."
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


    export_col1, export_col2 = st.columns(2)


    # =====================================================
    # CSV
    # =====================================================

    csv_data = (
        filtered_df
        .to_csv(index=False)
        .encode("utf-8")
    )


    with export_col1:

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


    with export_col2:

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

    errors = []

    for result in st.session_state.results:

        error = result.get(
            "_error",
            "",
        )

        if error:

            errors.append(error)


    if errors:

        with st.expander(
            "⚠ Search messages"
        ):

            for error in errors:

                st.write(error)
