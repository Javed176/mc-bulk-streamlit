from __future__ import annotations

from io import BytesIO

import pandas as pd


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """
    Convert a pandas DataFrame into an Excel file
    stored in memory.
    """

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Results",
        )

    output.seek(0)

    return output.getvalue()
