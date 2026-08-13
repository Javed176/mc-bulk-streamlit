import io
import time

import pandas as pd
import streamlit as st

from src.search import search_one
from src.auth import require_login, logout_user


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
# AUTHENTICATION
# =========================================================

require_login()


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "running": False,
    "start_mc": "",
    "current_mc": None,
    "last_searched_mc": None,
    "results": [],
    "searched_count": 0,
    "status_filter": "ALL",
    "type_filter": "ALL",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {

    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(80,110,255,0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(180,70,255,0.16),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(40,120,255,0.10),
            transparent 35%
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

    padding-top: 2.2rem;
    padding-bottom: 4rem;
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
        1px solid rgba(255,255,255,0.12);

    border-radius: 28px;

    padding: 28px;

    margin-bottom: 20px;

    box-shadow:
        0 20px 70px rgba(0,0,0,0.45),
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

    font-size: 3rem;

    font-weight: 800;

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


.hero-subtitle {

    color:
        rgba(235,240,255,0.62);

    font-size: 1rem;

    margin-top: 6px;
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
        50px;

    border-radius:
        18px !important;

    border:
        1px solid rgba(255,255,255,0.14) !important;

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
        0 10px 30px rgba(0,0,0,0.25),
        inset 0 1px 0 rgba(255,255,255,0.10);

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease,
        background 0.2s ease;
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
        0 12px 35px rgba(75,95,255,0.28),
        0 0 25px rgba(90,110,255,0.18);
}


.stButton > button:active {

    transform:
        scale(0.97);
}


/* =====================================================
   CURRENT MC
   ===================================================== */

.current-mc-card {

    text-align:
        center;

    padding:
        25px 20px;

    margin-top:
        20px;

    border-radius:
        24px;

    background:
        linear-gradient(
            135deg,
            rgba(90,110,255,0.13),
            rgba(160,70,255,0.08)
        );

    border:
        1px solid rgba(130,150,255,0.18);

    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.08),
        0 15px 45px rgba(0,0,0,0.25);
}


.current-label {

    color:
        #9da6c0;

    font-size:
        0.9rem;

    font-weight:
        600;

    text-transform:
        uppercase;

    letter-spacing:
        0.08em;
}


.current-number {

    font-size:
        2.7rem;

    font-weight:
        800;

    color:
        #ffffff;

    margin-top:
        5px;

    text-shadow:
        0 0 25px rgba(100,130,255,0.35);
}


.current-hint {

    color:
        #8993ad;

    font-size:
        0.85rem;

    margin-top:
        5px;
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
        transform:
            scale(0.85);

        opacity:
            0.6;
    }

    50% {
        transform:
            scale(1.2);

        opacity:
            1;
    }

    100% {
        transform:
            scale(0.85);

        opacity:
            0.6;
    }
}


/* =====================================================
   BADGES
   ===================================================== */

.badge {

    display:
        inline-block;

    padding:
        9px 15px;

    margin:
        4px 6px 10px 0;

    border-radius:
        999px;

    font-weight:
        700;

    font-size:
        0.9rem;
}


.badge-active {

    color:
        #58ff9a;

    background:
        rgba(40,255,130,0.10);

    border:
        1px solid rgba(60,255,145,0.25);

    box-shadow:
        0 0 18px rgba(50,255,130,0.08);
}


.badge-inactive {

    color:
        #ff667d;

    background:
        rgba(255,70,100,0.10);

    border:
        1px solid rgba(255,80,105,0.22);
}


.badge-carrier {

    color:
        #66aaff;

    background:
        rgba(70,130,255,0.10);

    border:
        1px solid rgba(80,140,255,0.22);
}


.badge-broker {

    color:
        #d18aff;

    background:
        rgba(180,80,255,0.10);

    border:
        1px solid rgba(190,90,255,0.22);
}


/* =====================================================
   FILTER CARD
   ===================================================== */

.filter-card {

    margin-top:
        18px;

    padding:
        20px;

    border-radius:
        22px;

    background:
        rgba(255,255,255,0.035);

    border:
        1px solid rgba(255,255,255,0.08);
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
        1px solid rgba(255,255,255,0.10);

    box-shadow:
        0 20px 60px rgba(0,0,0,0.30);
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

    border-radius:
        22px;

    padding:
        18px;

    box-shadow:
        0 15px 40px rgba(0,0,0,0.25);
}


div[data-testid="stMetricValue"] {

    color:
        #ffffff !important;
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

    pointer-events:
        none;

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

        width:
            20px;

        height:
            20px;

        opacity:
            0;

        transform:
            translate(-50%, -50%)
            rotate(0deg);
    }

    25% {

        width:
            260px;

        height:
            260px;

        opacity:
            1;
    }

    65% {

        width:
            330px;

        height:
            330px;

        opacity:
            1;

        filter:
            brightness(1.4);
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
            rotate(540deg);
    }
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 768px) {

    .hero-title {

        font-size:
            2.2rem;
    }

    .block-container {

        padding-left:
            1rem;

        padding-right:
            1rem;
    }

    .current-number {

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
# IMPORTANT:
# st.html() prevents the HTML source from appearing as text.
# =========================================================

st.html(
    """
    <div class="glass-card">

        <div class="hero-title">
            ✦ MC Search
        </div>

        <div class="hero-subtitle">
            FMCSA intelligence → DotSearch enrichment
        </div>

    </div>
    """
)


# =========================================================
# CONTROL CARD
# =========================================================

st.html(
    """
    <div class="glass-card">
        <div style="
            font-size:1.35rem;
            font-weight:750;
            margin-bottom:10px;
        ">
            🎯 Search Control
        </div>
    """
)

# Streamlit components cannot safely live inside the HTML
# element above, so the visual card is closed here.

st.html("</div>")


# =========================================================
# START MC INPUT
# =========================================================

start_value = str(
    st.session_state.start_mc
)

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
# CURRENT MC
# =========================================================

if st.session_state.running:

    display_mc = st.session_state.current_mc

    display_hint = (
        "Search running • next MC will update automatically"
    )

elif st.session_state.last_searched_mc is not None:

    display_mc = (
        st.session_state.last_searched_mc
    )

    display_hint = (
        "Search stopped • press START to continue"
    )

elif st.session_state.start_mc:

    display_mc = (
        st.session_state.start_mc
    )

    display_hint = (
        "Ready to search"
    )

else:

    display_mc = "—"

    display_hint = (
        "Enter a starting MC"
    )


if display_mc != "—":

    try:

        formatted_mc = f"{int(display_mc):,}"

    except Exception:

        formatted_mc = str(
            display_mc
        )

else:

    formatted_mc = "—"


st.html(
    f"""
    <div class="current-mc-card">

        <div class="current-label">
            Current MC Number
        </div>

        <div class="current-number">
            {formatted_mc}
        </div>

        <div class="current-hint">
            {display_hint}
        </div>

    </div>
    """
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


# =========================================================
# CLEAR HISTORY
# =========================================================

if clear_button:

    st.html(
        """
        <div class="black-hole"></div>
        """
    )

    time.sleep(1.0)

    st.session_state.running = False

    st.session_state.start_mc = ""

    st.session_state.current_mc = None

    st.session_state.last_searched_mc = None

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.status_filter = "ALL"

    st.session_state.type_filter = "ALL"

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    if (
        st.session_state.current_mc
        is not None
    ):

        st.session_state.last_searched_mc = (
            int(st.session_state.current_mc) - 1
        )

    st.session_state.running = False

    st.session_state.current_mc = None

    # Results intentionally remain.

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

    start_number = int(
        cleaned
    )

    st.session_state.start_mc = (
        str(start_number)
    )

    st.session_state.current_mc = (
        start_number
    )

    st.session_state.last_searched_mc = None

    st.session_state.running = True

    # IMPORTANT:
    # Existing results are NOT cleared.

    st.rerun()


# =========================================================
# LIVE STATUS
# =========================================================

if st.session_state.running:

    current = int(
        st.session_state.current_mc
    )

    st.html(
        f"""
        <div class="glass-card">

            <span class="live-dot"></span>

            <b>
                Searching MC {current:,}
            </b>

            <br>

            <small style="color:#9da6c0;">
                Searching sequential MC numbers automatically...
            </small>

        </div>
        """
    )


elif st.session_state.searched_count > 0:

    st.html(
        f"""
        <div class="glass-card">

            <b style="color:#72ffae;">
                ✓ Search stopped
            </b>

            <br><br>

            <small style="color:#9da6c0;">
                {st.session_state.searched_count:,}
                MC number(s) processed.
                Results are preserved until Clear History.
            </small>

        </div>
        """
    )


# =========================================================
# AUTOMATIC SEARCH
# =========================================================

if st.session_state.running:

    current_mc = int(
        st.session_state.current_mc
    )

    # -----------------------------------------------------
    # Search the EXACT current MC
    # -----------------------------------------------------

    result = search_one(
        str(current_mc)
    )

    # -----------------------------------------------------
    # Save result
    # -----------------------------------------------------

    st.session_state.results.append(
        result
    )

    st.session_state.searched_count += 1

    # -----------------------------------------------------
    # Remember the MC actually searched
    # -----------------------------------------------------

    st.session_state.last_searched_mc = (
        current_mc
    )

    # -----------------------------------------------------
    # Advance to next MC
    #
    # 1800000
    # 1800001
    # 1800002
    # 1800003
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )

    time.sleep(
        0.5
    )

    st.rerun()


# =========================================================
# RESULTS
# =========================================================

if st.session_state.results:

    st.html(
        """
        <div class="glass-card">
        """
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

    st.html(
        """
        <div class="filter-card">
            <div style="
                font-size:1.1rem;
                font-weight:750;
                margin-bottom:5px;
            ">
                🔎 Filters
            </div>
        """
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
            key="status_filter",
        )


    with filter_col2:

        type_filter = st.selectbox(
            "Broker / Carrier",
            [
                "ALL",
                "CARRIER",
                "BROKER",
            ],
            key="type_filter",
        )


    filtered_df = df.copy()


    if status_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df[
                "Operating Status"
            ]
            .astype(str)
            .str.upper()
            == status_filter
        ]


    if type_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df[
                "Broker/Carrier"
            ]
            .astype(str)
            .str.upper()
            == type_filter
        ]


    st.caption(
        f"Showing {len(filtered_df):,} "
        f"of {len(df):,} result(s)"
    )


    st.html(
        """
        </div>
        """
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
    # BADGES
    # =====================================================

    st.html(
        f"""
        <div style="
            margin-top:15px;
            margin-bottom:10px;
        ">

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
        """
    )


    # =====================================================
    # TABLE COLORS
    # =====================================================

    def color_status(value):

        value = str(
            value
        ).upper()

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

        value = str(
            value
        ).upper()

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


    st.html(
        """
        </div>
        """
    )


    # =====================================================
    # EXPORT
    # =====================================================

    st.html(
        """
        <div class="glass-card">

            <div style="
                font-size:1.25rem;
                font-weight:750;
                margin-bottom:5px;
            ">
                ⬇ Export Filtered Results
            </div>

            <div style="
                color:#9da6c0;
                font-size:0.9rem;
            ">
                Downloads contain only the results
                currently selected by the filters.
            </div>

        </div>
        """
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

        with st.expander(
            "⚠ Search messages"
        ):

            for error in errors:

                st.write(
                    error
                )


# =========================================================
# LOGOUT
# =========================================================

st.markdown(
    "<br>",
    unsafe_allow_html=True,
)


logout_col1, logout_col2, logout_col3 = st.columns(
    [1, 1, 1]
)


with logout_col2:

    if st.button(
        "🔐 Sign Out",
        use_container_width=True,
    ):

        logout_user()

        st.rerun()
