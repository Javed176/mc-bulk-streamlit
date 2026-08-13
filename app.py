import io

import pandas as pd
import streamlit as st

from src.search import bulk_fetch


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="MC Bulk Search",
    page_icon="🚛",
    layout="wide",
)


# =========================================================
# TITLE
# =========================================================

st.title("🚛 MC Bulk Search")

st.write(
    "MC → FMCSA DOT lookup → "
    "DotSearch data extraction"
)


# =========================================================
# INPUT
# =========================================================

st.subheader(
    "Enter MC Numbers"
)

input_text = st.text_area(
    "MC Numbers",
    height=180,
    placeholder=(
        "1066434\n"
        "123456\n"
        "987654"
    ),
)


# =========================================================
# SEARCH
# =========================================================

search_button = st.button(
    "🔎 Search",
    type="primary",
    use_container_width=True,
)


if search_button:

    if not input_text.strip():

        st.warning(
            "Please enter at least one MC number."
        )

        st.stop()


    identifiers = [
        line.strip()
        for line in input_text.splitlines()
        if line.strip()
    ]


    identifiers = list(
        dict.fromkeys(
            identifiers
        )
    )


    st.info(
        f"Searching {len(identifiers):,} MC number(s)..."
    )


    progress_bar = st.progress(
        0
    )

    status_text = st.empty()


    def update_progress(
        current,
        total,
    ):

        progress_bar.progress(
            current / total
        )

        status_text.write(
            f"Searching {current:,} of {total:,}..." 
        )


    results = bulk_fetch(
        identifiers,
        progress_callback=update_progress,
    )


    progress_bar.progress(
        1.0
    )

    status_text.success(
        "Search complete."
    )


    # =====================================================
    # BUILD DATAFRAME
    # =====================================================

    rows = []

    errors = []


    for result in results:

        rows.append(
            {
                "MC Number": result.get(
                    "MC Number",
                    "",
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

                "Email Address": result.get(
                    "Email Address",
                    "Not available",
                ),

                "Location": result.get(
                    "Location",
                    "Not available",
                ),

                "Owner": result.get(
                    "Owner",
                    "Not available",
                ),

                "Number": result.get(
                    "Number",
                    "Not available",
                ),
            }
        )


        if result.get(
            "_error"
        ):

            errors.append(
                result["_error"]
            )


    df = pd.DataFrame(
        rows,
        columns=[
            "MC Number",
            "Carrier/Broker Name",
            "Broker/Carrier",
            "Operating Status",
            "Email Address",
            "Location",
            "Owner",
            "Number",
        ],
    )


    # =====================================================
    # SUMMARY
    # =====================================================

    active_count = int(
        (
            df[
                "Operating Status"
            ]
            == "ACTIVE"
        ).sum()
    )


    inactive_count = int(
        (
            df[
                "Operating Status"
            ]
            == "INACTIVE"
        ).sum()
    )


    broker_count = int(
        (
            df[
                "Broker/Carrier"
            ]
            == "BROKER"
        ).sum()
    )


    carrier_count = int(
        (
            df[
                "Broker/Carrier"
            ]
            == "CARRIER"
        ).sum()
    )


    col1, col2, col3, col4 = st.columns(
        4
    )


    col1.metric(
        "Total",
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
    # COLOR STATUS
    # =====================================================

    def color_status(
        value,
    ):

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


    def color_type(
        value,
    ):

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
    # RESULTS
    # =====================================================

    st.subheader(
        "Results"
    )


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
