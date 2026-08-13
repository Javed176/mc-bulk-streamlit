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
            rgba(73, 105, 255, 0.20),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(175, 65, 255, 0.18),
            transparent 28%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(35, 80, 255, 0.10),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #030409 0%,
            #090b13 45%,
            #04050a 100%
        );

    color: #f5f7ff;
}


/* =====================================================
   MAIN WIDTH
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
    font-size: 3.1rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.055em;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #aebcff,
            #d69cff,
            #ffffff
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    text-shadow:
        0 0 35px rgba(115, 125, 255, 0.18);
}

h2,
h3 {
    color: #f7f8ff !important;
}


/* =====================================================
   GLASS CARDS
   ===================================================== */

.glass-card {
    position: relative;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.105),
            rgba(255,255,255,0.035)
        );

    border:
        1px solid
        rgba(255,255,255,0.13);

    border-radius: 28px;

    padding: 27px;

    margin-bottom: 20px;

    box-shadow:
        0 25px 80px rgba(0,0,0,0.42),
        inset 0 1px 0 rgba(255,255,255,0.10);

    backdrop-filter:
        blur(28px)
        saturate(160%);

    -webkit-backdrop-filter:
        blur(28px)
        saturate(160%);
}


/* =====================================================
   TOP GLOW
   ===================================================== */

.glass-card::before {
    content: "";

    position: absolute;

    top: 0;
    left: 8%;
    right: 8%;

    height: 1px;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(150,170,255,0.65),
            transparent
        );

    opacity: 0.8;
}


/* =====================================================
   SUBTITLE
   ===================================================== */

.subtitle {
    color: rgba(235,240,255,0.62);
    font-size: 1rem;
    margin-top: -18px;
    letter-spacing: 0.01em;
}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {
    background:
        rgba(255,255,255,0.055) !important;

    border:
        1px solid
        rgba(255,255,255,0.12) !important;

    border-radius:
        18px !important;

    transition:
        all 0.25s ease !important;

    box-shadow:
        inset 0 1px 0
        rgba(255,255,255,0.05);
}

div[data-baseweb="input"]:hover {
    border-color:
        rgba(130,150,255,0.45) !important;

    box-shadow:
        0 0 22px
        rgba(90,110,255,0.10);
}

div[data-baseweb="input"]:focus-within {
    border-color:
        rgba(120,145,255,0.90) !important;

    box-shadow:
        0 0 0 3px
        rgba(100,125,255,0.12),

        0 0 35px
        rgba(80,100,255,0.18);
}

input {
    color: #ffffff !important;
    font-size: 1.05rem !important;
}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button {
    position: relative;

    min-height: 52px;

    border-radius: 18px !important;

    border:
        1px solid
        rgba(255,255,255,0.14) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.13),
            rgba(255,255,255,0.045)
        ) !important;

    color: #ffffff !important;

    font-weight: 700 !important;

    letter-spacing: 0.01em;

    box-shadow:
        0 12px 35px rgba(0,0,0,0.30),
        inset 0 1px 0 rgba(255,255,255,0.10);

    transition:
        transform 0.18s ease,
        box-shadow 0.25s ease,
        border-color 0.25s ease,
        background 0.25s ease !important;
}

.stButton > button:hover {
    transform:
        translateY(-3px)
        scale(1.015);

    border-color:
        rgba(135,155,255,0.60) !important;

    background:
        linear-gradient(
            135deg,
            rgba(95,120,255,0.32),
            rgba(145,75,255,0.20)
        ) !important;

    box-shadow:
        0 16px 45px
        rgba(50,70,200,0.30),

        0 0 35px
        rgba(95,110,255,0.18),

        inset 0 1px 0
        rgba(255,255,255,0.16);
}

.stButton > button:active {
    transform:
        translateY(1px)
        scale(0.965);

    box-shadow:
        0 5px 15px
        rgba(0,0,0,0.35);
}


/* PRIMARY BUTTON */

button[kind="primary"] {
    background:
        linear-gradient(
            135deg,
            #536dff,
            #704cff,
            #934dff
        ) !important;

    border:
        1px solid
        rgba(180,190,255,0.45) !important;

    box-shadow:
        0 12px 35px
        rgba(75,80,255,0.35),

        0 0 30px
        rgba(100,80,255,0.20),

        inset 0 1px 0
        rgba(255,255,255,0.25);
}

button[kind="primary"]:hover {
    background:
        linear-gradient(
            135deg,
            #627bff,
            #815aff,
            #a85cff
        ) !important;

    box-shadow:
        0 18px 50px
        rgba(85,75,255,0.45),

        0 0 45px
        rgba(125,80,255,0.28);
}


/* =====================================================
   METRICS
   ===================================================== */

div[data-testid="stMetric"] {
    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.095),
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

    backdrop-filter:
        blur(20px);
}

div[data-testid="stMetricLabel"] {
    color:
        rgba(220,225,245,0.65) !important;
}

div[data-testid="stMetricValue"] {
    color:
        #ffffff !important;

    font-weight:
        800 !important;
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
        rgba(255,255,255,0.12);

    box-shadow:
        0 20px 65px
        rgba(0,0,0,0.32);
}


/* =====================================================
   LIVE DOT
   ===================================================== */

.live-dot {
    display: inline-block;

    width: 11px;
    height: 11px;

    border-radius: 50%;

    background:
        #35ff8a;

    box-shadow:
        0 0 8px #35ff8a,
        0 0 20px #35ff8a,
        0 0 35px rgba(53,255,138,0.65);

    animation:
        pulse 1.25s infinite;

    margin-right: 9px;
}

@keyframes pulse {
    0% {
        transform: scale(0.80);
        opacity: 0.60;
    }

    50% {
        transform: scale(1.25);
        opacity: 1;
    }

    100% {
        transform: scale(0.80);
        opacity: 0.60;
    }
}


/* =====================================================
   CURRENT MC DISPLAY
   ===================================================== */

.current-mc-box {
    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 20px 24px;

    border-radius: 22px;

    background:
        linear-gradient(
            135deg,
            rgba(65,90,255,0.16),
            rgba(140,60,255,0.10)
        );

    border:
        1px solid
        rgba(115,135,255,0.24);

    box-shadow:
        0 0 35px
        rgba(70,90,255,0.10),

        inset 0 1px 0
        rgba(255,255,255,0.07);

    margin-bottom: 18px;
}

.current-mc-label {
    color:
        rgba(220,225,245,0.60);

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
        1.65rem;

    font-weight:
        800;

    letter-spacing:
        0.02em;

    text-shadow:
        0 0 22px
        rgba(120,140,255,0.45);
}


/* =====================================================
   RESULT BADGES
   ===================================================== */

.result-summary {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 18px;
}

.badge {
    display: inline-flex;

    align-items: center;

    padding:
        8px 14px;

    border-radius:
        999px;

    font-size:
        0.82rem;

    font-weight:
        700;

    border:
        1px solid
        rgba(255,255,255,0.10);
}

.badge-active {
    color: #5dff9a;

    background:
        rgba(40,255,125,0.08);

    border-color:
        rgba(50,255,130,0.20);

    box-shadow:
        0 0 20px
        rgba(50,255,130,0.08);
}

.badge-inactive {
    color: #ff6478;

    background:
        rgba(255,55,85,0.08);

    border-color:
        rgba(255,70,100,0.20);
}

.badge-carrier {
    color: #72a7ff;

    background:
        rgba(70,120,255,0.09);

    border-color:
        rgba(80,130,255,0.20);
}

.badge-broker {
    color: #d091ff;

    background:
        rgba(170,75,255,0.09);

    border-color:
        rgba(180,80,255,0.20);
}


/* =====================================================
   BLACK HOLE
   ===================================================== */

.black-hole-overlay {
    position: fixed;

    inset: 0;

    z-index: 999999;

    pointer-events: none;

    background:
        radial-gradient(
            circle,
            rgba(0,0,0,0.05),
            rgba(0,0,0,0.80)
        );

    animation:
        overlayFade 1.45s ease-out forwards;
}

.black-hole {
    position: fixed;

    left: 50%;
    top: 50%;

    width: 40px;
    height: 40px;

    transform:
        translate(-50%, -50%);

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            #000000 0%,
            #000000 24%,
            #260040 30%,
            #7427ff 43%,
            #ff42d4 48%,
            #25112d 57%,
            transparent 70%
        );

    box-shadow:
        0 0 30px #7427ff,
        0 0 90px #5b22ff,
        0 0 170px rgba(255,50,215,0.55),
        0 0 280px rgba(110,40,255,0.25);

    animation:
        blackHole 1.4s
        cubic-bezier(.55,0,.08,1)
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

    15% {
        width: 150px;
        height: 150px;
        opacity: 1;
    }

    38% {
        width: 340px;
        height: 340px;
        opacity: 1;
        filter: brightness(1.35);
    }

    65% {
        width: 270px;
        height: 270px;
        opacity: 1;
    }

    100% {
        width: 0;
        height: 0;
        opacity: 0;
        transform:
            translate(-50%, -50%)
            rotate(720deg);
    }
}

@keyframes overlayFade {
    0% {
        opacity: 0;
    }

    20% {
        opacity: 1;
    }

    100% {
        opacity: 0;
    }
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 768px) {

    h1 {
        font-size: 2.25rem !important;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .current-mc-box {
        flex-direction: column;
        align-items: flex-start;
        gap: 5px;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# CLEAR ANIMATION
# =========================================================

if st.session_state.clear_animation:

    st.markdown(
        """
        <div class="black-hole-overlay">
            <div class="black-hole"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Clear the flag immediately.
    # The animation itself is handled by CSS in the browser.
    st.session_state.clear_animation = False


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
# RUNNING STATE
# =========================================================

if st.session_state.running:

    current_mc = st.session_state.current_mc

    st.markdown(
        f"""
        <div class="current-mc-box">

            <div>
                <div class="current-mc-label">
                    Currently Searching
                </div>

                <div class="current-mc-number">
                    MC {current_mc}
                </div>
            </div>

            <div>
                <span class="live-dot"></span>
                <span style="color:#8dffba;font-weight:700;">
                    LIVE
                </span>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "The search is automatically moving to the next MC number."
    )

else:

    start_input = st.text_input(
        "Starting MC Number",
        value=st.session_state.start_mc,
        placeholder="Example: 1066434",
        key="starting_mc_input",
    )

    st.caption(
        "Enter the first MC number. The app will search "
        "sequentially until you press STOP."
    )


# =========================================================
# BUTTONS
# =========================================================

col1, col2, col3 = st.columns(3)


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

    st.session_state.clear_animation = True

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

    st.session_state.current_mc = int(cleaned)

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
                Searching MC {st.session_state.current_mc}
            </b>

            <br>

            <small style="color:#9da6c0;">
                Search #{st.session_state.searched_count + 1}
                · automatically continuing
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

    current_mc = st.session_state.current_mc

    result = search_one(
        str(current_mc)
    )

    st.session_state.results.append(
        result
    )

    st.session_state.searched_count += 1

    st.session_state.current_mc = (
        current_mc + 1
    )

    time.sleep(0.35)

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
        <div class="result-summary">

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
    # TABLE COLORING
    # =====================================================

    def color_status(value):

        value = str(value).upper()

        if value == "ACTIVE":

            return (
                "color:#39ff88;"
                "font-weight:800;"
                "background-color:rgba(40,255,120,0.07);"
            )

        if value == "INACTIVE":

            return (
                "color:#ff5068;"
                "font-weight:800;"
                "background-color:rgba(255,50,80,0.07);"
            )

        return ""


    def color_type(value):

        value = str(value).upper()

        if value == "BROKER":

            return (
                "color:#c084fc;"
                "font-weight:800;"
                "background-color:rgba(180,80,255,0.07);"
            )

        if value == "CARRIER":

            return (
                "color:#60a5fa;"
                "font-weight:800;"
                "background-color:rgba(70,130,255,0.07);"
            )

        return ""


    def color_mc(value):

        return (
            "color:#aebcff;"
            "font-weight:700;"
        )


    styled_df = (
        df.style
        .map(
            color_status,
            subset=["Operating Status"],
        )
        .map(
            color_type,
            subset=["Broker/Carrier"],
        )
        .map(
            color_mc,
            subset=["MC Number"],
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
        "### ⬇ Export"
    )


    download_col1, download_col2 = st.columns(2)


    # =====================================================
    # CSV
    # =====================================================

    csv_data = (
        df.to_csv(
            index=False
        )
        .encode("utf-8")
    )


    with download_col1:

        st.download_button(
            "⬇  Download CSV",
            data=csv_data,
            file_name="mc_results.csv",
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

        df.to_excel(
            writer,
            index=False,
            sheet_name="MC Results",
        )


    with download_col2:

        st.download_button(
            "⬇  Download Excel",
            data=excel_buffer.getvalue(),
            file_name="mc_results.xlsx",
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
