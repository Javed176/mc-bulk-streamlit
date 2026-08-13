from __future__ import annotations

import re
import time
from typing import Dict, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

SAFER_BASE = (
    "https://safer.fmcsa.dot.gov/query.asp"
)

DOTSEARCH_BASE = (
    "https://www.dotsearch.io/dot/"
)

DEFAULT_TIMEOUT = 20


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}


# ---------------------------------------------------------
# NORMALIZE IDENTIFIER
# ---------------------------------------------------------

def normalize_identifier(
    value: str,
) -> str:

    return re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(value or "").upper(),
    )


# ---------------------------------------------------------
# IDENTIFIER TYPE
# ---------------------------------------------------------

def classify_identifier(
    value: str,
) -> str:

    raw = str(value or "").strip().upper()

    compact = normalize_identifier(
        raw
    )

    # Plain numbers are assumed to be MC.
    if compact.isdigit():

        return "MC"


    if compact.startswith(
        "USDOT"
    ):

        return "DOT"


    if compact.startswith(
        "DOT"
    ):

        return "DOT"


    if compact.startswith(
        ("MC", "MX", "FF")
    ):

        return compact[:2]


    return "UNKNOWN"


# ---------------------------------------------------------
# SAFER URL
# ---------------------------------------------------------

def safer_url(
    identifier: str,
) -> str:

    kind = classify_identifier(
        identifier
    )

    value = normalize_identifier(
        identifier
    )


    if kind == "DOT":

        query_param = "USDOT"

        query_string = (
            value
            .replace("USDOT", "")
            .replace("DOT", "")
        )


    elif kind in {
        "MC",
        "MX",
        "FF",
    }:

        query_param = kind

        query_string = value[2:]


    else:

        query_param = "MC"

        query_string = value


    return (
        f"{SAFER_BASE}"
        f"?original_query_param="
        f"{quote_plus(query_param)}"
        f"&original_query_string="
        f"{quote_plus(query_string)}"
        f"&query_param="
        f"{quote_plus(query_param)}"
        f"&query_string="
        f"{quote_plus(query_string)}"
        f"&query_type=queryCarrierSnapshot"
        f"&searchtype=ANY"
    )


# ---------------------------------------------------------
# DOTSEARCH URL
# ---------------------------------------------------------

def dotsearch_url(
    dot_number: str,
) -> str:

    clean_dot = normalize_identifier(
        dot_number
    )

    clean_dot = (
        clean_dot
        .replace("USDOT", "")
        .replace("DOT", "")
    )

    return (
        DOTSEARCH_BASE
        + clean_dot
    )


# ---------------------------------------------------------
# CLEAN TEXT
# ---------------------------------------------------------

def _clean(
    text: Optional[str],
) -> str:

    return re.sub(
        r"\s+",
        " ",
        (text or "").strip(),
    )


# ---------------------------------------------------------
# EXTRACT VALUE AFTER LABEL
# ---------------------------------------------------------

def _text_after_label(
    soup: BeautifulSoup,
    label: str,
) -> str:

    target = label.strip().upper()


    for text_node in soup.find_all(
        string=lambda s:
            s and target in _clean(s).upper()
    ):

        parent = text_node.parent

        value = _clean(
            parent.get_text(
                " ",
                strip=True,
            )
        )


        if (
            value
            and target in value.upper()
        ):

            remainder = re.sub(
                re.escape(label),
                "",
                value,
                flags=re.I,
            ).strip(" :")

            if remainder:
                return remainder


    return ""


# ---------------------------------------------------------
# CARRIER PARSER
# ---------------------------------------------------------

def _parse_carrier_snapshot(
    html: str,
    input_id: str,
) -> Dict[str, str]:

    soup = BeautifulSoup(
        html,
       "html.parser",
    )

    page_text = _clean(
        soup.get_text(
            " ",
            strip=True,
        )
    )


    result = {

        "input_id": input_id,

        "status": "NOT FOUND",

        "legal_name": "",

        "dba_name": "",

        "dot_number": "",

        "mc_number": "",

        "entity_type": "",

        "usdot_status": "",

        "out_of_service_date": "",

        "operating_authority_status": "",

        "physical_address": "",

        "mailing_address": "",

        "phone": "",

        "power_units": "",

        "drivers": "",

        "mcs150_form_date": "",

        "mcs150_mileage": "",

        "safer_url": safer_url(
            input_id
        ),

        "dotsearch_url": "",

        "error": "",
    }


    # -----------------------------------------------------
    # CHECK PAGE
    # -----------------------------------------------------

    if (
        "COMPANY SNAPSHOT" not in page_text.upper()
        and "USDOT NUMBER" not in page_text.upper()
    ):

        result["error"] = (
            "No carrier snapshot returned."
        )

        return result


    result["status"] = "FOUND"


    # -----------------------------------------------------
    # COMPANY NAME
    # -----------------------------------------------------

    headings = soup.find_all(
        ["h1", "h2", "h3"]
    )


    for heading in headings:

        candidate = _clean(
            heading.get_text(
                " ",
                strip=True,
            )
        )


        if (
            candidate
            and candidate.upper()
            not in {
                "COMPANY SNAPSHOT",
                "CARRIER DETAILS",
            }
        ):

            result["legal_name"] = (
                candidate
            )

            break


    # -----------------------------------------------------
    # REGEX HELPER
    # -----------------------------------------------------

    def regex_value(
        pattern: str,
    ) -> str:

        match = re.search(
            pattern,
            page_text,
            re.I,
        )

        if not match:
            return ""

        return _clean(
            match.group(1)
        )


    # -----------------------------------------------------
    # BASIC FIELDS
    # -----------------------------------------------------

    result["dot_number"] = regex_value(
        r"USDOT Number\s*[:#]?\s*(\d+)"
    )


    result["mc_number"] = regex_value(
        r"MC/MX/FF Number\(s\)"
        r"\s*[:#]?\s*"
        r"([A-Z0-9,;\- ]+?)"
        r"(?=\s+"
        r"(?:COMPANY|PHYSICAL|MAILING|DUNS|"
        r"POWER UNITS|DRIVERS)\b|$)"
    )


    result["entity_type"] = regex_value(
        r"ENTITY TYPE\s*[:]?\s*"
        r"([A-Z /&-]+?)"
        r"(?=\s+USDOT STATUS\b)"
    )


    result["usdot_status"] = regex_value(
        r"USDOT Status\s*[:]?\s*"
        r"([A-Z /-]+?)"
        r"(?=\s+Out of Service Date\b)"
    )


    result["out_of_service_date"] = (
        regex_value(
            r"Out of Service Date"
            r"\s*[:]?\s*"
            r"([A-Z0-9/\-]+|None)"
        )
    )


    result["operating_authority_status"] = (
        regex_value(
            r"Operating Authority Status"
            r"\s*[:]?\s*"
            r"([A-Z /-]+?)"
            r"(?=\s+\*|\s+MC/MX/FF|$)"
        )
    )


    result["phone"] = regex_value(
        r"Phone\s*[:]?\s*"
        r"(\(?\d{3}\)?[- .]\d{3}[- .]\d{4})"
    )


    result["power_units"] = regex_value(
        r"Power Units\s*[:]?\s*([\d,]+)"
    )


    result["drivers"] = regex_value(
        r"Drivers\s*[:]?\s*([\d,]+)"
    )


    result["mcs150_form_date"] = (
        regex_value(
            r"MCS-150 Form Date"
            r"\s*[:]?\s*"
            r"([0-9/\-]+)"
        )
    )


    result["mcs150_mileage"] = (
        regex_value(
            r"MCS-150 Mileage"
            r".*?"
            r"\s([\d,]+)\s*\("
        )
    )


    # -----------------------------------------------------
    # ADDRESSES
    # -----------------------------------------------------

    for key, label in (
        (
            "physical_address",
            "Physical Address",
        ),
        (
            "mailing_address",
            "Mailing Address",
        ),
    ):

        value = _text_after_label(
            soup,
            label,
        )


        if value:

            value = re.sub(
                r"\b"
                r"(Mailing Address|"
                r"Physical Address|"
                r"DUNS Number|"
                r"Power Units|"
                r"Drivers)"
                r"\b.*",
                "",
                value,
                flags=re.I,
            )


            result[key] = _clean(
                value
            )


    # -----------------------------------------------------
    # MC FALLBACK
    # -----------------------------------------------------

    if (
        not result["mc_number"]
        and classify_identifier(
            input_id
        ) in {
            "MC",
            "MX",
            "FF",
        }
    ):

        result["mc_number"] = (
            normalize_identifier(
                input_id
            )
        )


    # -----------------------------------------------------
    # DOTSEARCH URL
    # -----------------------------------------------------

    if result["dot_number"]:

        result["dotsearch_url"] = (
            dotsearch_url(
                result["dot_number"]
            )
        )


    # -----------------------------------------------------
    # TITLE FALLBACK
    # -----------------------------------------------------

    if not result["legal_name"]:

        title = ""

        if soup.title:

            title = _clean(
                soup.title.get_text(
                    " ",
                    strip=True,
                )
            )


        result["legal_name"] = re.sub(
            r"\s*[-|]\s*"
            r"(SAFER|FMCSA).*$",
            "",
            title,
            flags=re.I,
        )


    return result


# ---------------------------------------------------------
# FETCH ONE
# ---------------------------------------------------------

def fetch_one(
    identifier: str,
    session: Optional[
        requests.Session
    ] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, str]:

    identifier = str(
        identifier
    ).strip()


    if not identifier:

        return {
            "input_id": "",
            "status": "SKIPPED",
            "error": "Blank input.",
        }


    sess = (
        session
        if session
        else requests.Session()
    )


    try:

        response = sess.get(
            safer_url(identifier),
            headers=HEADERS,
            timeout=timeout,
        )

        response.raise_for_status()


        return _parse_carrier_snapshot(
            response.text,
            identifier,
        )


    except requests.RequestException as exc:

        return {

            "input_id": identifier,

            "status": "ERROR",

            "legal_name": "",

            "dba_name": "",

            "dot_number": "",

            "mc_number": (
                normalize_identifier(
                    identifier
                )
                if classify_identifier(
                    identifier
                ) != "DOT"
                else ""
            ),

            "entity_type": "",

            "usdot_status": "",

            "out_of_service_date": "",

            "operating_authority_status": "",

            "physical_address": "",

            "mailing_address": "",

            "phone": "",

            "power_units": "",

            "drivers": "",

            "mcs150_form_date": "",

            "mcs150_mileage": "",

            "safer_url": safer_url(
                identifier
            ),

            "dotsearch_url": "",

            "error": str(exc),
        }


# ---------------------------------------------------------
# BULK FETCH
# ---------------------------------------------------------

def bulk_fetch(
    identifiers,
    delay_seconds: float = 1.0,
    progress_callback=None,
) -> list[Dict[str, str]]:

    session = requests.Session()

    results = []

    total = len(
        identifiers
    )


    for index, identifier in enumerate(
        identifiers,
        start=1,
    ):

        result = fetch_one(
            identifier,
            session=session,
        )

        results.append(
            result
        )


        if progress_callback:

            progress_callback(
                index,
                total,
            )


        if (
            index < total
            and delay_seconds > 0
        ):

            time.sleep(
                delay_seconds
            )


    return results
