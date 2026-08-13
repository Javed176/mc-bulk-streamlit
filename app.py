from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from src.export import to_excel_bytes
from src.search import bulk_fetch, normalize_identifier


st.set_page_config(
    page_title="MC / DOT Bulk Search",
    page_icon="🚚",
    layout="wide",
)


st.title("🚚 MC / DOT Bulk Search")

st.caption(
    "Bulk search MC/DOT numbers using public FMCSA SAFER data. "
    "DotSearch links are provided for optional verification."
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Settings")

    delay = st.slider(
        "Delay between requests",
        min_value=0.5,
        max_value=5.0,
        value=1.0,
        step=0.5,
    )

    max_ids = st.number_input(
        "Maximum IDs per search",
        min_value=1,
        max_value=5000,
        value=250,
        step=25,
    )

    st.info(
        "Use reasonable request rates. Public websites may throttle "
        "or block aggressive automated requests."
    )


# ---------------------------------------------------------
# INPUT PARSER
# ---------------------------------------------------------

def parse_text(raw: str) -> list[str]:
    """
    Extract identifiers from text.

    Supports:
    MC123456
    MC-123456
    DOT123456
    USDOT123456
    comma-separated values
    space-separated values
    """

    chunks = re.split(r"[\s,;]+", raw or "")

    cleaned = []
    seen = set()

    for chunk in chunks:
        value = chunk.strip()

        if not value:
            continue

        normalized = normalize_identifier(value)

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        cleaned.append(value)

    return cleaned


# ---------------------------------------------------------
# INPUT SECTION
# ---------------------------------------------------------

st.subheader("1️⃣ Add MC / DOT numbers")

tab1, tab2 = st.tabs(
    [
        "✍️ Paste IDs",
        "📁 Upload CSV / TXT",
    ]
)


# ---------------------------------------------------------
# TAB 1
# ---------------------------------------------------------

with tab1:

    raw_input = st.text_area(
        "Paste MC / DOT numbers",
        placeholder=(
            "MC50725\n"
            "MC1762665\n"
            "DOT3052774\n"
            "USDOT3052774"
        ),
        height=220,
    )

    pasted_ids = parse_text(raw_input)


# ---------------------------------------------------------
# TAB 2
# ---------------------------------------------------------

with tab2:

    uploaded_file = st.file_uploader(
        "Upload a CSV or TXT file",
        type=["csv", "txt"],
    )

    uploaded_ids = []

    if uploaded_file:

        if uploaded_file.name.lower().endswith(".csv"):

            try:

                uploaded_df = pd.read_csv(uploaded_file)

                preferred_columns = {
                    "MC",
                    "MCNUMBER",
                    "MX",
                    "MXNUMBER",
                    "FF",
                    "FFNUMBER",
                    "DOT",
                    "DOTNUMBER",
                    "USDOT",
                    "USDOTNUMBER",
                    "NUMBER",
                    "ID",
                }

                matching_columns = []

                for column in uploaded_df.columns:

                    normalized_column = normalize_identifier(column)

                    if normalized_column in preferred_columns:
                        matching_columns.append(column)

                # If no known column exists, use the first column.
                if not matching_columns:
                    matching_columns = list(uploaded_df.columns[:1])

                for column in matching_columns:

                    values = (
                        uploaded_df[column]
                        .dropna()
                        .astype(str)
                        .tolist()
                    )

                    uploaded_ids.extend(values)

                st.success(
                    f"Loaded {len(uploaded_ids):,} IDs "
                    f"from {len(matching_columns)} column(s)."
                )

            except Exception as exc:

                st.error(
                    f"Could not read the CSV file: {exc}"
                )

        else:

            try:

                file_text = uploaded_file.read().decode(
                    "utf-8",
                    errors="ignore",
                )

                uploaded_ids = parse_text(file_text)

                st.success(
                    f"Loaded {len(uploaded_ids):,} IDs."
                )

            except Exception as exc:

                st.error(
                    f"Could not read the TXT file: {exc}"
                )


# ---------------------------------------------------------
# COMBINE INPUTS
# ---------------------------------------------------------

all_ids = parse_text(
    "\n".join(
        pasted_ids + uploaded_ids
    )
)

all_ids = all_ids[: int(max_ids)]


st.write(
    f"**Unique identifiers ready:** "
    f"{len(all_ids):,}"
)


# ---------------------------------------------------------
# PREVIEW INPUT
# ---------------------------------------------------------

if all_ids:

    preview_df = pd.DataFrame(
        {
            "Input": all_ids
        }
    )

    st.dataframe(
        preview_df,
        use_container_width=True,
        height=200,
        hide_index=True,
    )


# ---------------------------------------------------------
# SEARCH BUTTON
# ---------------------------------------------------------

search_clicked = st.button(
    "🔎 Search in Bulk",
    type="primary",
    disabled=not all_ids,
    use_container_width=True,
)


# ---------------------------------------------------------
# SEARCH
# ---------------------------------------------------------

if search_clicked:

    progress_bar = st.progress(0)

    status_message = st.empty()

    def update_progress(
        completed: int,
        total: int,
    ):

        progress = (
            completed / total
            if total
            else 0
        )

        progress_bar.progress(progress)

        status_message.write(
            f"Searching {completed:,} / {total:,} ..."
        )

    results = bulk_fetch(
        all_ids,
        delay_seconds=delay,
        progress_callback=update_progress,
    )

    results_df = pd.DataFrame(results)

    st.session_state["results"] = results_df

    status_message.success(
        f"Finished. Processed {len(results_df):,} records."
    )


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

if "results" in st.session_state:

    df = st.session_state["results"].copy()

    st.subheader("2️⃣ Results")

    if df.empty:

        st.warning(
            "No results were returned."
        )

    else:

        # -------------------------------------------------
        # FILTERS
        # -------------------------------------------------

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:

            statuses = sorted(
                df["status"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_statuses = st.multiselect(
                "Status",
                statuses,
                default=statuses,
            )

        with filter_col2:

            address_filter = st.text_input(
                "Search address"
            )

        with filter_col3:

            company_filter = st.text_input(
                "Search company"
            )


        # -------------------------------------------------
        # APPLY FILTERS
        # -------------------------------------------------

        if selected_statuses:

            filtered_df = df[
                df["status"].isin(
                    selected_statuses
                )
            ].copy()

        else:

            filtered_df = df.iloc[0:0].copy()


        if address_filter:

            address_mask = (
                filtered_df["physical_address"]
                .fillna("")
                .str.contains(
                    address_filter,
                    case=False,
                    na=False,
                )
            )

            filtered_df = filtered_df[
                address_mask
            ]


        if company_filter:

            company_mask = (
                filtered_df["legal_name"]
                .fillna("")
                .str.contains(
                    company_filter,
                    case=False,
                    na=False,
                )
            )

            filtered_df = filtered_df[
                company_mask
            ]


        # -------------------------------------------------
        # COLUMNS
        # -------------------------------------------------

        preferred_columns = [
            "input_id",
            "legal_name",
            "dba_name",
            "dot_number",
            "mc_number",
            "entity_type",
            "usdot_status",
            "operating_authority_status",
            "physical_address",
            "mailing_address",
            "phone",
            "power_units",
            "drivers",
            "mcs150_form_date",
            "mcs150_mileage",
            "safer_url",
            "dotsearch_url",
            "error",
        ]

        display_columns = [
            column
            for column in preferred_columns
            if column in filtered_df.columns
        ]


        # -------------------------------------------------
        # DISPLAY
        # -------------------------------------------------

        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            height=550,
            hide_index=True,
        )


        st.write(
            f"**Showing {len(filtered_df):,} "
            f"of {len(df):,} records**"
        )


        # -------------------------------------------------
        # DOWNLOADS
        # -------------------------------------------------

        csv_data = filtered_df.to_csv(
            index=False
        ).encode("utf-8-sig")


        excel_data = to_excel_bytes(
            filtered_df
        )


        download_col1, download_col2 = st.columns(2)


        with download_col1:

            st.download_button(
                "⬇️ Download CSV",
                data=csv_data,
                file_name="mc_bulk_results.csv",
                mime="text/csv",
                use_container_width=True,
            )


        with download_col2:

            st.download_button(
                "⬇️ Download Excel",
                data=excel_data,
                file_name="mc_bulk_results.xlsx",
                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "Data source: public FMCSA SAFER carrier information. "
    "DotSearch links are provided for optional record-level "
    "verification. Always validate information before using "
    "it for compliance, outreach, or business decisions."
)
