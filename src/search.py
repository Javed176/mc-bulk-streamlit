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

FMCSA_API_BASE = "https://mobile.fmcsa.dot.gov/qc/services"
DOTSEARCH_BASE = "https://www.dotsearch.io/dot"

REQUEST_TIMEOUT = 30
DOTSEARCH_DELAY = 0.5


# =========================================================
# FMCSA API KEY
# =========================================================

def get_fmcsa_web_key() -> str:

    try:
        key = st.secrets.get(
            "FMCSA_WEB_KEY",
            "",
        )
    except Exception:
        key = ""

    return str(key).strip()


# =========================================================
# NORMALIZE
# =========================================================

def normalize_identifier(value: str) -> str:

    return re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(value or "").upper(),
    )


def remove_prefix(value: str) -> str:

    value = normalize_identifier(value)

    for prefix in (
        "USDOT",
        "DOT",
        "MC",
        "MX",
        "FF",
    ):

        if value.startswith(prefix):

            return value[len(prefix):]

    return value


# =========================================================
# FMCSA REQUEST
# =========================================================

def fmcsa_get(endpoint: str):

    web_key = get_fmcsa_web_key()

    if not web_key:

        raise RuntimeError(
            "FMCSA API key is missing. "
            "Add FMCSA_WEB_KEY to Streamlit Secrets."
        )

    url = FMCSA_API_BASE + endpoint

    response = requests.get(
        url,
        params={
            "webKey": web_key,
        },
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": "MC-Bulk-Streamlit/1.0",
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

def find_value(data, possible_keys):

    wanted = {
        str(key)
        .replace("_", "")
        .replace("-", "")
        .lower()
        for key in possible_keys
    }

    if isinstance(data, dict):

        for key, value in data.items():

            normalized = (
                str(key)
                .replace("_", "")
                .replace("-", "")
                .lower()
            )

            if normalized in wanted:

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
# MC → DOT
# FMCSA IS ONLY USED HERE
# =========================================================

def get_dot_from_mc(mc_number: str) -> str:

    mc = remove_prefix(mc_number)

    endpoint = (
        "/carriers/docket-number/"
        + mc
        + "/"
    )

    data = fmcsa_get(endpoint)

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
            "but no DOT number was returned."
        )

    return str(dot_number).strip()


# =========================================================
# DOTSEARCH URL
# =========================================================

def dotsearch_url(dot_number: str) -> str:

    return (
        DOTSEARCH_BASE
        + "/"
        + remove_prefix(dot_number)
    )


# =========================================================
# DOWNLOAD DOTSEARCH
# =========================================================

def get_dotsearch_page(dot_number: str):

    url = dotsearch_url(dot_number)

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
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    if response.status_code == 404:
        return None, url

    response.raise_for_status()

    return response.text, url


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(value: str) -> str:

    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


# =========================================================
# PAGE LINES
# =========================================================

def page_lines(soup):

    text = soup.get_text(
        "\n",
        strip=True,
    )

    return [
        clean_text(line)
        for line in text.splitlines()
        if clean_text(line)
    ]


# =========================================================
# COMPANY NAME
# =========================================================

def extract_company_name(soup) -> str:

    lines = page_lines(soup)

    # =====================================================
    # FIRST: Look for the company name in the page text.
    # DotSearch normally displays the company name before
    # the DBA/address information.
    # =====================================================

    for line in lines:

        line = clean_text(line)

        if not line:
            continue

        # Skip navigation / headings
        if line.lower() in (
            "back",
            "dot search",
            "company officers",
            "contact information",
            "operation information",
            "authority",
            "physical address",
            "mailing address",
        ):
            continue

        # Skip DBA
        if line.lower().startswith("dba "):
            continue

        # Skip DOT/MC information
        if re.search(
            r"\bDOT\s*#?\s*\d+",
            line,
            flags=re.I,
        ):
            continue

        if re.search(
            r"\bMC\s*#?\s*\d+",
            line,
            flags=re.I,
        ):
            continue

        # Skip obvious page title
        if "DOT Search" in line:
            continue

        # Skip carrier/broker labels
        if line.upper() in (
            "CARRIER",
            "BROKER",
            "INTERSTATE",
            "INTRASTATE",
        ):
            continue

        # Skip addresses
        if re.search(
            r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b",
            line,
        ):
            continue

        # =================================================
        # COMPANY NAME
        # =================================================
        #
        # Remove anything accidentally appended after
        # " - DOT #..."
        #

        company = re.split(
            r"\s*-\s*DOT\s*#.*$",
            line,
            flags=re.I,
        )[0].strip()

        # Remove accidental " | DOT Search™"
        company = re.split(
            r"\s*\|\s*DOT Search",
            company,
            flags=re.I,
        )[0].strip()

        if company:
            return company

    # =====================================================
    # FALLBACK: H1
    # =====================================================

    h1 = soup.find("h1")

    if h1:

        company = clean_text(
            h1.get_text(
                " ",
                strip=True,
            )
        )

        # Remove:
        # - DOT # 3341131
        # - | DOT Search™
        # - anything after it

        company = re.split(
            r"\s*-\s*DOT\s*#.*$",
            company,
            flags=re.I,
        )[0].strip()

        company = re.split(
            r"\s*\|\s*DOT Search",
            company,
            flags=re.I,
        )[0].strip()

        if company:
            return company

    return "Not available"
# =========================================================
# MC NUMBER
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
        return match.group(1)

    return remove_prefix(
        fallback_mc
    )


# =========================================================
# BROKER / CARRIER
# =========================================================

def extract_business_type(soup) -> str:

    lines = page_lines(soup)

    # DotSearch explicitly shows:
    #
    # Carrier
    #
    # or:
    #
    # Broker

    for line in lines[:30]:

        normalized = line.upper().strip()

        if normalized == "CARRIER":
            return "CARRIER"

        if normalized == "BROKER":
            return "BROKER"

    # Fallback: authority section

    text = "\n".join(lines)

    authority = re.search(
        r"Common:\s*([A-Za-z]+)"
        r"\s+Contract:\s*([A-Za-z]+)"
        r"\s+Broker:\s*([A-Za-z]+)",
        text,
        flags=re.I,
    )

    if authority:

        common = authority.group(1).upper()
        contract = authority.group(2).upper()
        broker = authority.group(3).upper()

        if broker not in (
            "NONE",
            "INACTIVE",
        ):
            return "BROKER"

        if common not in (
            "NONE",
            "INACTIVE",
        ):
            return "CARRIER"

        if contract not in (
            "NONE",
            "INACTIVE",
        ):
            return "CARRIER"

    return "Not available"


# =========================================================
# OPERATING STATUS
# =========================================================

def extract_operating_status(soup) -> str:

    lines = page_lines(soup)

    text = "\n".join(lines)

    authority = re.search(
        r"Common:\s*([A-Za-z]+)"
        r"\s+Contract:\s*([A-Za-z]+)"
        r"\s+Broker:\s*([A-Za-z]+)",
        text,
        flags=re.I,
    )

    if authority:

        statuses = [
            authority.group(1).upper(),
            authority.group(2).upper(),
            authority.group(3).upper(),
        ]

        if "ACTIVE" in statuses:
            return "ACTIVE"

        return "INACTIVE"

    for line in lines:

        if line.upper() == "ACTIVE":
            return "ACTIVE"

        if line.upper() == "INACTIVE":
            return "INACTIVE"

    return "INACTIVE"


# =========================================================
# EMAIL
# =========================================================

def extract_email(soup) -> str:

    # First try mailto

    mailto = soup.find(
        "a",
        href=re.compile(
            r"^mailto:",
            re.I,
        ),
    )

    if mailto:

        email = re.sub(
            r"^mailto:",
            "",
            mailto.get(
                "href",
                "",
            ),
            flags=re.I,
        ).strip()

        if "@" in email:
            return email

    # Search whole page

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
        return match.group(0).strip()

    return "Not available"


# =========================================================
# LOCATION
# =========================================================

def extract_location(soup) -> str:

    lines = page_lines(soup)

    for index, line in enumerate(lines):

        if line.lower() == "physical address":

            for candidate in lines[
                index + 1:
                index + 6
            ]:

                candidate = clean_text(candidate)

                if not candidate:
                    continue

                if candidate.lower() in (
                    "mailing address",
                    "address",
                ):
                    continue

                if re.search(
                    r"\b[A-Z]{2}\s+"
                    r"\d{5}(?:-\d{4})?\b",
                    candidate,
                ):
                    return candidate

    return "Not available"


# =========================================================
# OWNER
# =========================================================

def extract_owner(soup) -> str:

    # -----------------------------------------------------
    # PRIMARY METHOD
    #
    # Find the actual Company Officers section.
    # Then find Officer 1.
    # Then take the next person/name.
    # -----------------------------------------------------

    lines = page_lines(soup)

    company_officer_index = None

    for index, line in enumerate(lines):

        if line.lower() == "company officers":

            company_officer_index = index
            break

    if company_officer_index is not None:

        officer_index = None

        for index in range(
            company_officer_index + 1,
            min(
                company_officer_index + 10,
                len(lines),
            ),
        ):

            if re.fullmatch(
                r"Officer\s+1",
                lines[index],
                flags=re.I,
            ):

                officer_index = index
                break

        if officer_index is not None:

            # Search next few lines.
            for candidate in lines[
                officer_index + 1:
                officer_index + 6
            ]:

                candidate = clean_text(
                    candidate
                )

                if not candidate:
                    continue

                if re.match(
                    r"Officer\s+\d+",
                    candidate,
                    flags=re.I,
                ):
                    continue

                if candidate.lower() in (
                    "contact information",
                    "operation information",
                    "address",
                ):
                    break

                # Avoid obvious non-name values.
                if "@" in candidate:
                    continue

                if re.search(
                    r"\d{3}.*\d{4}",
                    candidate,
                ):
                    continue

                # A person name.
                if len(candidate.split()) >= 2:

                    return candidate

    # -----------------------------------------------------
    # SECONDARY METHOD
    #
    # Search actual links in Company Officers section.
    # This is especially useful because DotSearch makes
    # ZAHID ABBAS KHAN a clickable link.
    # -----------------------------------------------------

    for heading in soup.find_all(
        string=re.compile(
            r"Company Officers",
            re.I,
        )
    ):

        parent = heading.parent

        # Search nearby links.

        for link in parent.find_all_next(
            "a",
            limit=5,
        ):

            name = clean_text(
                link.get_text(
                    " ",
                    strip=True,
                )
            )

            if not name:
                continue

            if name.lower() in (
                "back",
                "search another company",
            ):
                continue

            if re.match(
                r"Officer\s+\d+",
                name,
                flags=re.I,
            ):
                continue

            if "google" in (
                link.get(
                    "href",
                    ""
                ).lower()
            ):
                continue

            if len(name.split()) >= 2:

                return name

    return "Not available"


# =========================================================
# PHONE / NUMBER
# =========================================================

def extract_owner_number(soup) -> str:

    lines = page_lines(soup)

    # -----------------------------------------------------
    # PRIMARY METHOD
    #
    # DotSearch:
    #
    # Contact Information
    # Phone
    # (918) 829-3191
    #
    # -----------------------------------------------------

    contact_index = None

    for index, line in enumerate(lines):

        if line.lower() == "contact information":

            contact_index = index
            break

    if contact_index is not None:

        for index in range(
            contact_index + 1,
            min(
                contact_index + 12,
                len(lines),
            ),
        ):

            if lines[index].lower() == "phone":

                for candidate in lines[
                    index + 1:
                    index + 5
                ]:

                    candidate = clean_text(
                        candidate
                    )

                    match = re.search(
                        r"\(?\d{3}\)?"
                        r"[\s.-]*\d{3}"
                        r"[\s.-]*\d{4}",
                        candidate,
                    )

                    if match:
                        return match.group(0)

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    text = "\n".join(lines)

    match = re.search(
        r"\(?\d{3}\)?"
        r"[\s.-]*\d{3}"
        r"[\s.-]*\d{4}",
        text,
    )

    if match:
        return match.group(0)

    return "Not available"


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
            "Owner": "Not available",
            "Carrier/Broker Name": "Not found",
            "Broker/Carrier": "Not found",
            "Operating Status": "INACTIVE",
            "Number": "Not available",
            "Email Address": "Not available",
            "Location": "Not available",
            "_dot_number": remove_prefix(
                dot_number
            ),
            "_dotsearch_url": url,
            "_error": "DotSearch page returned 404.",
        }

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    return {
        "MC Number": extract_mc_number(
            soup,
            mc_number,
        ),

        "Owner": extract_owner(
            soup
        ),

        "Carrier/Broker Name": extract_company_name(
            soup
        ),

        "Broker/Carrier": extract_business_type(
            soup
        ),

        "Operating Status": extract_operating_status(
            soup
        ),

        "Number": extract_owner_number(
            soup
        ),

        "Email Address": extract_email(
            soup
        ),

        "Location": extract_location(
            soup
        ),

        "_dot_number": remove_prefix(
            dot_number
        ),

        "_dotsearch_url": url,

        "_error": "",
    }


# =========================================================
# SEARCH ONE MC
# =========================================================

def search_one(mc_number: str) -> dict:

    mc_number = str(
        mc_number
    ).strip()

    if not mc_number:

        return {
            "MC Number": "",
            "Owner": "Not available",
            "Carrier/Broker Name": "",
            "Broker/Carrier": "",
            "Operating Status": "INACTIVE",
            "Number": "Not available",
            "Email Address": "Not available",
            "Location": "Not available",
            "_dot_number": "",
            "_dotsearch_url": "",
            "_error": "Blank MC number.",
        }

    # =====================================================
    # FMCSA:
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

            "Owner": "Not available",

            "Carrier/Broker Name": "Not found",

            "Broker/Carrier": "Not found",

            "Operating Status": "INACTIVE",

            "Number": "Not available",

            "Email Address": "Not available",

            "Location": "Not available",

            "_dot_number": "",

            "_dotsearch_url": "",

            "_error": (
                "FMCSA MC → DOT error: "
                + str(exc)
            ),
        }

    # =====================================================
    # DOTSEARCH:
    # DOT → FINAL DATA
    # =====================================================

    try:

        return scrape_dotsearch(
            mc_number,
            dot_number,
        )

    except Exception as exc:

        return {
            "MC Number": remove_prefix(
                mc_number
            ),

            "Owner": "Not available",

            "Carrier/Broker Name": "Not found",

            "Broker/Carrier": "Not found",

            "Operating Status": "INACTIVE",

            "Number": "Not available",

            "Email Address": "Not available",

            "Location": "Not available",

            "_dot_number": remove_prefix(
                dot_number
            ),

            "_dotsearch_url": dotsearch_url(
                dot_number
            ),

            "_error": (
                "DotSearch scraping error: "
                + str(exc)
            ),
        }


# =========================================================
# COMPATIBILITY
# =========================================================

def fetch_one(
    identifier: str,
    session: Optional[requests.Session] = None,
    timeout: int = REQUEST_TIMEOUT,
) -> dict:

    return search_one(identifier)


# =========================================================
# BULK FUNCTION
# =========================================================

def bulk_fetch(
    identifiers,
    delay_seconds: float = DOTSEARCH_DELAY,
    progress_callback=None,
):

    results = []

    total = len(identifiers)

    if not get_fmcsa_web_key():

        return [
            {
                "MC Number": "",
                "Owner": "Not available",
                "Carrier/Broker Name": "",
                "Broker/Carrier": "",
                "Operating Status": "INACTIVE",
                "Number": "Not available",
                "Email Address": "Not available",
                "Location": "Not available",
                "_dot_number": "",
                "_dotsearch_url": "",
                "_error": (
                    "FMCSA API key is missing."
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

        if (
            index < total
            and delay_seconds > 0
        ):

            time.sleep(
                delay_seconds
            )

    return results
