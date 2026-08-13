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
# HELPERS
# =========================================================

def clean_mc(value):
    return (
        str(value or "")
        .strip()
        .replace("MC", "")
        .replace("mc", "")
        .strip()
    )


def reset_search():
    st.session_state.running = False
    st.session_state.current_mc = None


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
            rgba(74, 100, 255, 0.20),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(180, 70, 255, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(30, 120, 255, 0.10),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #04050a,
            #090b13 50%,
            #04050a
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
    color: #ffffff !important;
}


/* =====================================================
   GLASS
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

    padding: 26px;

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
   SUBTITLE
   ===================================================== */

.subtitle {
    color: rgba(235,240,255,0.62);
    font-size: 1rem;
    margin-top: -20px;
    margin-bottom: 25px;
}


/* =====================================================
   INPUT
   ===================================================== */

div[data-baseweb="input"] {
    background:
        rgba(255,255,255,0.06) !important;

    border:
        1px solid rgba(255,255,255,0.12) !important;

    border-radius:
        18px !important;

    transition:
        all 0.25s ease;
}

div[data-baseweb="input"]:focus-within {
    border-color:
        rgba(110,135,255,0.9) !important;

    box-shadow:
        0 0 0 3px rgba(90,110,255,0.13),
        0 0 35px rgba(80,100,255,0.18);
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
        1px solid rgba(255,255,255,0.14) !important;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.12),
            rgba(255,255,255,0.045)
        ) !important;

    color: #ffffff !important;

    font-weight: 700 !important;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.25),
        inset 0 1px 0 rgba(255,255,255,0.10);

    transition:
        transform 0.18s ease,
        box-shadow 0.18s ease,
        background 0.18s ease;
}

.stButton > button:hover {
    transform:
        translateY(-3px)
        scale(1.015);

    background:
        linear-gradient(
            135deg,
            rgba(100,125,255,0.35),
            rgba(150,75,255,0.25)
        ) !important;

    box-shadow:
        0 14px 40px rgba(70,90,255,0.30),
        0 0 28px rgba(100,120,255,0.20);
}

.stButton > button:active {
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
        1px solid rgba(255,255,255,0.10);

    border-radius: 22px;

    padding: 18px;

    box-shadow:
        0 15px 40px rgba(0,0,0,0.25);

    backdrop-filter:
        blur(20px);
}

div[data-testid="stMetricValue"] {
    color: #ffffff !important;
}


/* =====================================================
   STATUS
   ===================================================== */

.live-dot {
    display: inline-block;

    width: 10px;
    height: 10px;

    border-radius: 50%;

    background: #39ff88;

    box-shadow:
        0 0 8px #39ff88,
        0 0 22px #39ff88;

    animation: pulse 1.3s infinite;

    margin-right: 8px;
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
   RESULT BADGES
   ===================================================== */

.badges {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 18px 0;
}

.badge {
    padding: 9px 15px;

    border-radius: 999px;

    font-weight: 700;

    border: 1px solid rgba(255,255,255,0.10);

    backdrop-filter: blur(15px);
}

.badge-active {
    color: #39ff88;
    background: rgba(30,255,130,0.08);
    box-shadow: 0 0 18px rgba(30,255,130,0.08);
}

.badge-inactive {
    color: #ff5870;
    background: rgba(255,60,90,0.08);
}

.badge-carrier {
    color: #62a8ff;
    background: rgba(70,130,255,0.09);
}

.badge-broker {
    color: #c084fc;
    background: rgba(170,80,255,0.09);
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

    width: 220px;
    height: 220px;

    border-radius: 50%;

    z-index: 999999;

    background:
        radial-gradient(
            circle,
            #000 0%,
            #000 25%,
            #17002c 31%,
            #7020ff 43%,
            #ff42d0 49%,
            #161020 58%,
            transparent 72%
        );

    box-shadow:
        0 0 35px #7a2cff,
        0 0 100px #5a1cff,
        0 0 180px rgba(255,40,210,0.35);

    animation:
        blackHole
        1.25s
        cubic-bezier(.6,0,.1,1)
        forwards;
}

@keyframes blackHole {

    0% {
        width: 15px;
        height: 15px;
        opacity: 0;
    }

    25% {
        width: 260px;
        height: 260px;
        opacity: 1;
    }

    60% {
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

    h1 {
        font-size: 2.2rem !important;
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


# ---------------------------------------------------------
# IMPORTANT:
# We do NOT modify the text_input's session-state key.
#
# Instead we calculate its value BEFORE creating the widget.
# ---------------------------------------------------------

if st.session_state.running:

    display_mc = str(
        st.session_state.current_mc
    )

elif st.session_state.start_mc:

    display_mc = str(
        st.session_state.start_mc
    )

else:

    display_mc = ""


start_input = st.text_input(
    "Current MC Number",
    value=display_mc,
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

    st.session_state.results = []
    st.session_state.searched_count = 0
    st.session_state.running = False
    st.session_state.current_mc = None
    st.session_state.start_mc = ""

    # IMPORTANT:
    # Do not touch st.session_state.mc_input here.
    #
    # The widget will naturally receive the empty
    # start_mc value on the next rerun.

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    # -----------------------------------------------------
    # IMPORTANT FIX
    #
    # Do NOT put current_mc back into start_mc.
    #
    # This means after STOP the starting field keeps the
    # ORIGINAL MC that the user entered.
    # -----------------------------------------------------

    st.session_state.running = False
    st.session_state.current_mc = None

    st.rerun()


# =========================================================
# START
# =========================================================

if start_button:

    cleaned = clean_mc(
        start_input
    )

    if not cleaned.isdigit():

        st.error(
            "Enter a valid numeric MC number."
        )

        st.stop()


    # -----------------------------------------------------
    # Save the ORIGINAL starting MC.
    # -----------------------------------------------------

    st.session_state.start_mc = cleaned

    # -----------------------------------------------------
    # Search begins from this MC.
    # -----------------------------------------------------

    st.session_state.current_mc = int(
        cleaned
    )

    # -----------------------------------------------------
    # New search = new result set.
    # -----------------------------------------------------

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
    # Search exactly ONE MC.
    # -----------------------------------------------------

    result = search_one(
        str(current_mc)
    )

    # -----------------------------------------------------
    # Store result.
    # -----------------------------------------------------

    st.session_state.results.append(
        result
    )

    st.session_state.searched_count += 1

    # -----------------------------------------------------
    # Move to NEXT MC.
    #
    # This does NOT change start_mc.
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )

    # -----------------------------------------------------
    # Small delay.
    # -----------------------------------------------------

    time.sleep(0.5)

    # -----------------------------------------------------
    # Rerun.
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
                "color:#ff526b;"
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
    # EXPORT
    # =====================================================

    st.markdown(
        '<div class="glass-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### ⬇ Export"
    )


    download_col1, download_col2 = st.columns(
        2
    )


    # =====================================================
    # CSV
    # =====================================================

    csv_data = (
        df
        .to_csv(index=False)
        .encode("utf-8")
    )


    with download_col1:

        st.download_button(
            "Download CSV",
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
            "Download Excel",
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
