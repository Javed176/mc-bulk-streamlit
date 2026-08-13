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

defaults = {
    "running": False,
    "current_mc": None,
    "results": [],
    "searched_count": 0,
    "last_searched_mc": None,
    "clear_animation": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

/* =====================================================
   BACKGROUND
   ===================================================== */

.stApp {
    background:
        radial-gradient(
            circle at 12% 5%,
            rgba(75, 110, 255, 0.20),
            transparent 28%
        ),
        radial-gradient(
            circle at 88% 8%,
            rgba(170, 70, 255, 0.18),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #04050a 0%,
            #0a0d16 50%,
            #05060b 100%
        );
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
    font-size: 3rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.055em !important;

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


h2,
h3 {
    color: #f5f7ff !important;
}


/* =====================================================
   CAPTIONS
   ===================================================== */

.stCaption {
    color: #8d98b5 !important;
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
}


/* =====================================================
   SELECTBOX
   ===================================================== */

div[data-baseweb="select"] > div {
    background:
        rgba(255,255,255,0.055) !important;

    border:
        1px solid rgba(255,255,255,0.12) !important;

    border-radius:
        16px !important;

    color: white !important;
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
        box-shadow 0.20s ease !important;
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

    border-radius:
        22px;

    padding:
        18px;

    box-shadow:
        0 15px 40px rgba(0,0,0,0.25);
}


div[data-testid="stMetricValue"] {
    color: #ffffff !important;
}


/* =====================================================
   SUCCESS MESSAGE
   ===================================================== */

div[data-testid="stAlert"] {
    border-radius: 18px !important;
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
   SEARCHING ANIMATION
   ===================================================== */

.searching-dot {
    animation:
        searchPulse 1.2s infinite;
}


@keyframes searchPulse {

    0% {
        opacity: 0.45;
    }

    50% {
        opacity: 1;
    }

    100% {
        opacity: 0.45;
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
# HELPERS
# =========================================================

def clean_mc(value):
    value = str(value or "").strip()

    value = (
        value
        .replace("MC", "")
        .replace("mc", "")
        .strip()
    )

    return value


def existing_mc_numbers():
    numbers = set()

    for result in st.session_state.results:

        value = clean_mc(
            result.get(
                "MC Number",
                "",
            )
        )

        if value.isdigit():
            numbers.add(int(value))

    return numbers


def build_dataframe(results):

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

st.title("✦ MC Search")

st.caption(
    "FMCSA intelligence → DotSearch enrichment"
)


# =========================================================
# SEARCH CONTROL
# =========================================================

st.subheader("🎯 Search Control")


# =========================================================
# START MC
# =========================================================

start_mc = st.text_input(
    "Start MC",
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

st.markdown("#### Current MC Number")


if st.session_state.current_mc is None:

    current_value = "—"

else:

    current_value = (
        f"{int(st.session_state.current_mc):,}"
    )


st.metric(
    label="",
    value=current_value,
)


if st.session_state.running:

    st.caption(
        "🟢 Search running • next MC will update automatically"
    )

else:

    if st.session_state.current_mc is not None:

        st.caption(
            "Search stopped • press START to begin another search"
        )

    else:

        st.caption(
            "Waiting for search"
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

    st.session_state.results = []

    st.session_state.searched_count = 0

    st.session_state.running = False

    st.session_state.current_mc = None

    st.session_state.last_searched_mc = None

    st.success(
        "History cleared."
    )

    time.sleep(0.4)

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_button:

    # IMPORTANT:
    # current_mc is intentionally NOT reset.
    #
    # Results are intentionally NOT reset.

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

    used_numbers = existing_mc_numbers()


    # -----------------------------------------------------
    # Never search the exact same MC twice.
    # -----------------------------------------------------

    while starting_mc in used_numbers:

        starting_mc += 1


    st.session_state.current_mc = starting_mc

    st.session_state.running = True

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

    st.info(
        f"🟢 Searching MC {current_mc:,}..."
    )


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    result = search_one(
        str(current_mc)
    )


    # -----------------------------------------------------
    # SAVE RESULT
    # -----------------------------------------------------

    st.session_state.results.append(
        result
    )

    st.session_state.searched_count += 1

    st.session_state.last_searched_mc = current_mc


    # -----------------------------------------------------
    # NEXT MC
    # -----------------------------------------------------

    st.session_state.current_mc = (
        current_mc + 1
    )


    time.sleep(0.35)

    st.rerun()


# =========================================================
# STOPPED STATUS
# =========================================================

if (
    not st.session_state.running
    and st.session_state.searched_count > 0
):

    st.success(
        f"✓ Search stopped — "
        f"{st.session_state.searched_count:,} "
        f"MC number(s) processed. "
        f"Results are preserved until Clear History."
    )


# =========================================================
# RESULTS
# =========================================================

if st.session_state.results:

    st.subheader("📊 Search Results")


    df = build_dataframe(
        st.session_state.results
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
    # METRICS
    # =====================================================

    m1, m2, m3, m4, m5 = st.columns(5)


    with m1:

        st.metric(
            "Searched",
            len(df),
        )


    with m2:

        st.metric(
            "🟢 Active",
            active_count,
        )


    with m3:

        st.metric(
            "🔴 Inactive",
            inactive_count,
        )


    with m4:

        st.metric(
            "🔵 Carriers",
            carrier_count,
        )


    with m5:

        st.metric(
            "🟣 Brokers",
            broker_count,
        )


    # =====================================================
    # FILTERS
    # =====================================================

    st.subheader("🔎 Filters")


    filter1, filter2 = st.columns(2)


    with filter1:

        status_filter = st.selectbox(
            "Operating Status",
            [
                "All",
                "ACTIVE",
                "INACTIVE",
            ],
        )


    with filter2:

        type_filter = st.selectbox(
            "Broker / Carrier",
            [
                "All",
                "CARRIER",
                "BROKER",
            ],
        )


    # =====================================================
    # APPLY STATUS FILTER
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


    # =====================================================
    # APPLY TYPE FILTER
    # =====================================================

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
        f"Showing {len(filtered_df):,} "
        f"of {len(df):,} searched records."
    )


    # =====================================================
    # TABLE COLORS
    # =====================================================

    def color_status(value):

        value = str(value).upper()

        if value == "ACTIVE":

            return (
                "color: #39ff88; "
                "font-weight: 800;"
            )

        if value == "INACTIVE":

            return (
                "color: #ff4d67; "
                "font-weight: 800;"
            )

        return ""


    def color_type(value):

        value = str(value).upper()

        if value == "BROKER":

            return (
                "color: #c084fc; "
                "font-weight: 800;"
            )

        if value == "CARRIER":

            return (
                "color: #60a5fa; "
                "font-weight: 800;"
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


    # =====================================================
    # EXPORT
    # =====================================================

    st.subheader("⬇ Export Filtered Data")


    export1, export2 = st.columns(2)


    # =====================================================
    # CSV
    # =====================================================

    csv_data = (
        filtered_df
        .to_csv(index=False)
        .encode("utf-8")
    )


    with export1:

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


    with export2:

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


    # =====================================================
    # SEARCH ERRORS
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
