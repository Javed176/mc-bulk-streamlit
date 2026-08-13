from __future__ import annotations

import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
import streamlit as st


# =========================================================
# SETTINGS
# =========================================================

FMCSA_API_BASE = (
    "https://mobile.fmcsa.dot.gov/qc/services"
)

DOTSEARCH_BASE = (
    "https://www.dotsearch.io/dot"
)

REQUEST_TIMEOUT = 30

# Small delay between DotSearch requests.
# Increase this if you are searching very large lists.
DOTSEARCH_DELAY = 0.5


# =========================================================
# FMCSA WEB KEY
# =========================================================

def get_fmcsa_web_key() -> str:
    """
    Reads the FMCSA API key from Streamlit Secrets.

    Streamlit Cloud:
        Manage app
        -> Settings
        -> Secrets

    Add:

        FMCSA_WEB_KEY = "YOUR_REAL_KEY"
    """

    try:
        key = st.secrets.get(
            "FMCSA_WEB_KEY",
            "",
        )
    except Exception:
        key = ""

    return str(key).strip()


# =========================================================
# CLEAN IDENTIFIER
# =========================================================

def normalize_identifier(
    value: str,
) -> str:

    return re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(value or "").upper(),
    )


# =========================================================
# REMOVE MC / DOT PREFIX
# =========================================================

def remove_prefix(
    value: str,
) -> str:

    value = normalize_identifier(
        value
    )

    prefixes = (
        "USDOT",
        "DOT",
        "MC",
        "MX",
        "FF",
    )

    for prefix in prefixes:

        if value.startswith(prefix):

            return value[
                len(prefix):
            ]

    return value


# =========================================================
# FMCSA API
# =========================================================

def fmcsa_get(
    endpoint: str,
):

    web_key = get_fmcsa_web_key()

    if not web_key:

        raise RuntimeError(
            "FMCSA API key is missing. "
            "Add FMCSA_WEB_KEY to Streamlit Secrets."
        )

    url = (
        FMCSA_API_BASE
        + endpoint
    )

    response = requests.get(
        url,
        params={
            "webKey": web_key,
        },
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": (
                "MC-Bulk-Streamlit/1.0"
            ),
            "Accept": "application/json",
        },
    )

    if response.status_code == 401:

        raise RuntimeError(
            "FMCSA API authentication failed. "
            "Check your FMCSA WebKey."
        )

    if response.status_code == 404:

        return None

    response.raise_for_status()

    return response.json()


# =========================================================
# FIND VALUE IN NESTED JSON
# =========================================================

def find_value(
    data,
    possible_keys,
):

    wanted_keys = set()

    for key in possible_keys:

        wanted_keys.add(
            str(key)
            .replace("_", "")
            .replace("-", "")
            .lower()
        )

    if isinstance(data, dict):

        for key, value in data.items():

            normalized_key = (
                str(key)
                .replace("_", "")
                .replace("-", "")
                .lower()
            )

            if normalized_key in wanted_keys:

                if value is not None:

                    return value

            result = find_value(
                value,
                possible_keys,
            )

            if result is not None:

                return result

    elif isinstance(data, list):

        for item in data:

            result = find_value(
                item,
                possible_keys,
            )

            if result is not None:

                return result

    return None


# =========================================================
# MC → DOT USING FMCSA
# =========================================================

def get_dot_from_mc(
    mc_number: str,
) -> str:

    mc = remove_prefix(
        mc_number
    )

    endpoint = (
        "/carriers/docket-number/"
        + mc
        + "/"
    )

    data = fmcsa_get(
        endpoint
    )

    if not data:

        raise RuntimeError(
            f"FMCSA did not find MC {mc}."
        )

    dot_number = find_value(
        data,
        [
            "dotNumber",
            "USDOTNumber",
            "usdotNumber",
        ],
    )

    if not dot_number:

        raise RuntimeError(
            f"FMCSA found MC {mc}, "
            "but did not return a DOT number."
        )

    return str(
        dot_number
    ).strip()


# =========================================================
# DOTSEARCH URL
# =========================================================

def dotsearch_url(
    dot_number: str,
) -> str:

    dot = remove_prefix(
        dot_number
    )

    return (
        DOTSEARCH_BASE
        + "/"
        + dot
    )


# =========================================================
# DOWNLOAD DOTSEARCH PAGE
# =========================================================

def get_dotsearch_page(
    dot_number: str,
):

    url = dotsearch_url(
        dot_number
    )

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8"
            ),
            "Accept-Language": (
                "en-US,en;q=0.9"
            ),
        },
    )

    if response.status_code == 404:

        return None, url

    response.raise_for_status()

    return response.text, url


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(
    value: str,
) -> str:

    if not value:

        return ""

    value = re.sub(
        r"\s+",
        " ",
        str(value),
    )

    return value.strip()


# =========================================================
# FIND SECTION BY HEADING
# =========================================================

def get_section_text(
    soup,
    heading_text: str,
) -> str:
    """
    Find a heading such as:

        Contact Information
        Operation Information
        Address

    and return text from that section.
    """

    heading = soup.find(
        lambda tag:
        tag.name in [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]
        and heading_text.lower()
        in tag.get_text(
            " ",
            strip=True,
        ).lower()
    )

    if not heading:

        return ""

    section_parts = []

    for element in heading.find_all_next():

        if element == heading:
            continue

        # Stop at another heading
        if element.name in [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]:

            break

        text = clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            section_parts.append(
                text
            )

    return " ".join(
        section_parts
    )


# =========================================================
# EXTRACT EMAIL
# =========================================================

def extract_email(
    soup,
) -> str:

    # First look for mailto links.
    mailto = soup.find(
        "a",
        href=re.compile(
            r"^mailto:",
            re.I,
        ),
    )

    if mailto:

        href = mailto.get(
            "href",
            "",
        )

        email = re.sub(
            r"^mailto:",
            "",
            href,
            flags=re.I,
        ).strip()

        if "@" in email:

            return email


    # Look through page text for email
    text = soup.get_text(
        "\n",
        strip=True,
    )

    match = re.search(
        r"[A-Z0-9._%+-]+"
        r"@[A-Z0-9.-]+\.[A-Z]{2,}",
        text,
        flags=re.I,
    )

    if match:

        return match.group(
            0
        ).strip()


    return "Not available"


# =========================================================
# EXTRACT LOCATION
# =========================================================

def extract_location(
    soup,
) -> str:

    # Find the "Physical Address" label.
    label = soup.find(
        string=re.compile(
            r"^\s*Physical Address\s*$",
            re.I,
        )
    )

    if label:

        parent = label.parent

        # Look for nearby address text.
        text = clean_text(
            parent.parent.get_text(
                " ",
                strip=True,
            )
        )

        text = re.sub(
            r"^Physical Address\s*",
            "",
            text,
            flags=re.I,
        ).strip()

        if text:

            # Remove accidental "Mailing Address"
            text = re.split(
                r"Mailing Address",
                text,
                flags=re.I,
            )[0].strip()

            if text:

                return text


    # Fallback: search for common US address
    full_text = soup.get_text(
        "\n",
        strip=True,
    )

    # We don't want to accidentally return
    # an unrelated address.
    lines = [
        clean_text(line)
        for line in full_text.splitlines()
    ]

    for index, line in enumerate(
        lines
    ):

        if re.search(
            r"physical address",
            line,
            re.I,
        ):

            for candidate in lines[
                index + 1:
                index + 5
            ]:

                if re.search(
                    r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b",
                    candidate,
                ):

                    return candidate

    return "Not available"


# =========================================================
# EXTRACT COMPANY NAME
# =========================================================

def extract_company_name(
    soup,
) -> str:

    # DotSearch puts the company name
    # at the top of the page.

    h1 = soup.find(
        "h1"
    )

    if h1:

        name = clean_text(
            h1.get_text(
                " ",
                strip=True,
            )
        )

        if name:

            return name


    # Fallback:
    # Find page title.

    title = soup.find(
        "title"
    )

    if title:

        text = clean_text(
            title.get_text(
                " ",
                strip=True,
            )
        )

        # Remove common suffix.
        text = re.sub(
            r"\s*-\s*DOT\s*#.*$",
            "",
            text,
            flags=re.I,
        )

        if text:

            return text


    return "Not available"


# =========================================================
# EXTRACT MC NUMBER
# =========================================================

def extract_mc_number(
    soup,
    fallback_mc: str,
) -> str:

    text = soup.get_text(
        "\n",
        strip=True,
    )

    match = re.search(
        r"\bMC\s+([0-9]+)\b",
        text,
        flags=re.I,
    )

    if match:

        return match.group(
            1
        )

    return remove_prefix(
        fallback_mc
    )


# =========================================================
# EXTRACT BROKER / CARRIER
# =========================================================

def extract_business_type(
    soup,
) -> str:

    text = soup.get_text(
        "\n",
        strip=True,
    )


    # =====================================================
    # FIRST: DotSearch normally shows this near the top:
    #
    # Carrier
    #
    # or
    #
    # Broker
    # =====================================================

    # Search explicit standalone labels.
    if re.search(
        r"(?m)^\s*Broker\s*$",
        text,
        re.I,
    ):

        return "BROKER"

    if re.search(
        r"(?m)^\s*Carrier\s*$",
        text,
        re.I,
    ):

        return "CARRIER"


    # =====================================================
    # SECOND: USE AUTHORITY SECTION
    #
    # Common: Active
    # Contract: None
    # Broker: None
    #
    # If Broker is active → BROKER
    # Otherwise carrier authority → CARRIER
    # =====================================================

    authority_match = re.search(
        r"Common:\s*([^\s]+)"
        r".*?"
        r"Contract:\s*([^\s]+)"
        r".*?"
        r"Broker:\s*([^\s]+)",
        text,
        flags=re.I | re.S,
    )

    if authority_match:

        common_status = (
            authority_match.group(1)
            .strip()
            .upper()
        )

        contract_status = (
            authority_match.group(2)
            .strip()
            .upper()
        )

        broker_status = (
            authority_match.group(3)
            .strip()
            .upper()
        )

        if broker_status not in (
            "",
            "NONE",
            "INACTIVE",
            "N/A",
        ):

            return "BROKER"

        if common_status not in (
            "",
            "NONE",
            "INACTIVE",
            "N/A",
        ):

            return "CARRIER"

        if contract_status not in (
            "",
            "NONE",
            "INACTIVE",
            "N/A",
        ):

            return "CARRIER"


    return "CARRIER"


# =========================================================
# EXTRACT OPERATING STATUS
# =========================================================

def extract_operating_status(
    soup,
) -> str:

    text = soup.get_text(
        "\n",
        strip=True,
    )


    # =====================================================
    # DotSearch authority example:
    #
    # Common: Active Contract: None Broker: None
    # =====================================================

    authority_match = re.search(
        r"Common:\s*([^\s]+)"
        r".*?"
        r"Contract:\s*([^\s]+)"
        r".*?"
        r"Broker:\s*([^\s]+)",
        text,
        flags=re.I | re.S,
    )


    if authority_match:

        common_status = (
            authority_match.group(1)
            .strip()
            .upper()
        )

        contract_status = (
            authority_match.group(2)
            .strip()
            .upper()
        )

        broker_status = (
            authority_match.group(3)
            .strip()
            .upper()
        )


        statuses = [
            common_status,
            contract_status,
            broker_status,
        ]


        # If any authority is active,
        # operating status = ACTIVE.
        if any(
            status == "ACTIVE"
            for status in statuses
        ):

            return "ACTIVE"


        # If all authorities are none/inactive,
        # return inactive.
        if all(
            status in (
                "",
                "NONE",
                "INACTIVE",
                "N/A",
            )
            for status in statuses
        ):

            return "INACTIVE"


    # =====================================================
    # Fallback searches
    # =====================================================

    if re.search(
        r"\bActive\b",
        text,
        re.I,
    ):

        return "ACTIVE"


    if re.search(
        r"\bInactive\b",
        text,
        re.I,
    ):

        return "INACTIVE"


    return "INACTIVE"


# =========================================================
# SCRAPE DOTSEARCH
# =========================================================

def scrape_dotsearch(
    mc_number: str,
    dot_number: str,
) -> dict:

    html, url = get_dotsearch_page(
        dot_number
    )

    if not html:

        return {
            "MC Number": remove_prefix(
                mc_number
            ),

            "Carrier/Broker Name": (
                "Not found"
            ),

            "Broker/Carrier": (
                "Not found"
            ),

            "Operating Status": (
                "INACTIVE"
            ),

            "Email Address": (
                "Not available"
            ),

            "Location": (
                "Not available"
            ),

            "_dot_number": (
                remove_prefix(
                    dot_number
                )
            ),

            "_dotsearch_url": url,

            "_error": (
                "DotSearch page returned 404."
            ),
        }


    soup = BeautifulSoup(
        html,
        "html.parser",
    )


    # =====================================================
    # EXTRACT DATA FROM DOTSEARCH
    # =====================================================

    company_name = (
        extract_company_name(
            soup
        )
    )

    business_type = (
        extract_business_type(
            soup
        )
    )

    operating_status = (
        extract_operating_status(
            soup
        )
    )

    email = extract_email(
        soup
    )

    location = extract_location(
        soup
    )

    mc = extract_mc_number(
        soup,
        mc_number,
    )


    return {

        "MC Number": mc,

        "Carrier/Broker Name": (
            company_name
        ),

        "Broker/Carrier": (
            business_type
        ),

        "Operating Status": (
            operating_status
        ),

        "Email Address": email,

        "Location": location,

        "_dot_number": (
            remove_prefix(
                dot_number
            )
        ),

        "_dotsearch_url": url,

        "_error": "",
    }


# =========================================================
# SEARCH ONE MC
# =========================================================

def search_one(
    mc_number: str,
) -> dict:

    mc_number = str(
        mc_number
    ).strip()


    if not mc_number:

        return {
            "MC Number": "",
            "Carrier/Broker Name": "",
            "Broker/Carrier": "",
            "Operating Status": "INACTIVE",
            "Email Address": "Not available",
            "Location": "Not available",
            "_dot_number": "",
            "_dotsearch_url": "",
            "_error": "Blank MC number.",
        }


    # =====================================================
    # STEP 1
    # FMCSA ONLY
    # MC → DOT
    # =====================================================

    try:

        dot_number = get_dot_from_mc(
            mc_number
        )

    except Exception as exc:

        return {
            "MC Number": remove_prefix(
                mc_number
            ),

            "Carrier/Broker Name": (
                "Not found"
            ),

            "Broker/Carrier": (
                "Not found"
            ),

            "Operating Status": (
                "INACTIVE"
            ),

            "Email Address": (
                "Not available"
            ),

            "Location": (
                "Not available"
            ),

            "_dot_number": "",

            "_dotsearch_url": "",

            "_error": (
                "FMCSA MC → DOT error: "
                + str(exc)
            ),
        }


    # =====================================================
    # STEP 2
    # DOTSEARCH
    # DOT → ALL USER DATA
    # =====================================================

    try:

        result = scrape_dotsearch(
            mc_number,
            dot_number,
        )

        return result

    except Exception as exc:

        return {
            "MC Number": remove_prefix(
                mc_number
            ),

            "Carrier/Broker Name": (
                "Not found"
            ),

            "Broker/Carrier": (
                "Not found"
            ),

            "Operating Status": (
                "INACTIVE"
            ),

            "Email Address": (
                "Not available"
            ),

            "Location": (
                "Not available"
            ),

            "_dot_number": (
                remove_prefix(
                    dot_number
                )
            ),

            "_dotsearch_url": (
                dotsearch_url(
                    dot_number
                )
            ),

            "_error": (
                "DotSearch scraping error: "
                + str(exc)
            ),
        }


# =========================================================
# BACKWARD-COMPATIBLE FUNCTION
# =========================================================

def fetch_one(
    identifier: str,
    session: Optional[
        requests.Session
    ] = None,
    timeout: int = REQUEST_TIMEOUT,
) -> dict:

    return search_one(
        identifier
    )


# =========================================================
# BULK SEARCH
# =========================================================

def bulk_fetch(
    identifiers,
    delay_seconds: float = DOTSEARCH_DELAY,
    progress_callback=None,
):

    results = []

    total = len(
        identifiers
    )


    # Check API key once.
    if not get_fmcsa_web_key():

        return [
            {
                "MC Number": "",
                "Carrier/Broker Name": "",
                "Broker/Carrier": "",
                "Operating Status": "INACTIVE",
                "Email Address": "Not available",
                "Location": "Not available",
                "_dot_number": "",
                "_dotsearch_url": "",
                "_error": (
                    "FMCSA API key is missing. "
                    "Add FMCSA_WEB_KEY to "
                    "Streamlit Secrets."
                ),
            }
        ]


    for index, identifier in enumerate(
        identifiers,
        start=1,
    ):

        result = search_one(
            identifier
        )

        results.append(
            result
        )


        if progress_callback:

            progress_callback(
                index,
                total,
            )


        # =================================================
        # Delay between searches
        # =================================================

        if (
            index < total
            and delay_seconds > 0
        ):

            time.sleep(
                delay_seconds
            )


    return results
