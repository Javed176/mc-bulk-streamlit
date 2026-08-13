import io
import time

import pandas as pd
import streamlit as st

from src.search import search_one


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="MC Bulk Search",
    page_icon="🚛",
    layout="wide",
)


# =========================================================
# SESSION STATE
# =========================================================

if "running" not in st.session_state:
    st.session_state.running = False

if "current_mc" not in st.session_state:
    st.session_state.current_mc = None

if "results" not in st.session_state:
    st.session_state.results = []

if "start_mc" not in st.session_state:
    st.session_state.start_mc = ""

if "searched_count" not in st.session_state:
    st.session_state.searched_count = 0


# =========================================================
# TITLE
# =========================================================

st.title("🚛 MC Automatic Bulk Search")

st.caption(
    "FMCSA is used only to convert MC → DOT. "
    "Final company data comes from DotSearch."
)


# =========================================================
# START MC
# =========================================================

st.subheader(
    "Start MC Number"
)

start_input = st.text_input(
    "Enter the first MC number",
    value=st.session_state.start_mc,
    placeholder="Example: 1066434",
    disabled=st.session_state.running,
)


# =========================================================
# BUTTONS
# =========================================================

col1, col2 = st.columns(2)


with col1:

    start_button = st.button(
        "▶️ START",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running,
    )


with col2:

    stop_button = st.button(
        "🛑 STOP",
        type="secondary",
        use_container_width=True,
        disabled=not st.session_state.running,
    )


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
            "Please enter a valid numeric MC number."
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
# CURRENT STATUS
# =========================================================

if st.session_state.running:

    st.warning(
        f"🔄 Searching MC "
        f"{st.session_state.current_mc:,}..."
    )

else:

    if st.session_state.searched_count > 0:

        st.info(
            f"Stopped after "
            f"{st.session_state.searched_count:,} "
            f"MC number(s)."
        )


# =========================================================
# AUTOMATIC SEARCH
# =========================================================

if st.session_state.running:

    current_mc = (
        st.session_state.current_mc
    )

    # -----------------------------------------------------
    # SEARCH CURRENT MC
    # -----------------------------------------------------

    result = search_one(
        str(current_mc)
    )

    # -----------------------------------------------------
    # ADD RESULT
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

    # -----------------------------------------------------
    # WAIT A LITTLE
    # -----------------------------------------------------

    time.sleep(0.5)

    # -----------------------------------------------------
    # RERUN
    #
    # This searches the next MC.
    # Stop button can interrupt between requests.
    # -----------------------------------------------------

    st.rerun()


# =========================================================
# RESULTS
# =========================================================

if st.session_state.results:

    st.divider()

    st.subheader(
        "📊 Results"
    )


    # =====================================================
    # DATAFRAME
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
    # COUNTERS
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


    col1, col2, col3, col4 = st.columns(
        4
    )


    col1.metric(
        "Searched",
        len(df),
    )

    col2.metric(
        "Active",
        active_count,
    )

    col3.metric(
        "Inactive",
        inactive_count,
    )

    col4.metric(
        "Brokers",
        broker_count,
    )


    # =====================================================
    # STATUS COLORS
    # =====================================================

    def color_status(value):

        if value == "ACTIVE":

            return (
                "color: #16a34a;"
                "font-weight: 700;"
            )

        if value == "INACTIVE":

            return (
                "color: #dc2626;"
                "font-weight: 700;"
            )

        return ""


    def color_type(value):

        if value == "BROKER":

            return (
                "color: #7c3aed;"
                "font-weight: 700;"
            )

        if value == "CARRIER":

            return (
                "color: #2563eb;"
                "font-weight: 700;"
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


    # =====================================================
    # SHOW TABLE
    # =====================================================

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
    )


    # =====================================================
    # CSV
    # =====================================================

    csv_data = df.to_csv(
        index=False
    ).encode(
        "utf-8"
    )


    st.download_button(
        "⬇️ Download CSV",
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


    st.download_button(
        "⬇️ Download Excel",
        data=excel_buffer.getvalue(),
        file_name="mc_results.xlsx",
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
            "⚠️ Search messages"
        ):

            for error in errors:

                st.write(
                    error
                )
