from __future__ import annotations

import re
import time
from typing import Dict, Optional

import requests
import streamlit as st


# =========================================================
# FMCSA API
# =========================================================

FMCSA_API_BASE = "https://mobile.fmcsa.dot.gov/qc/services"

DEFAULT_TIMEOUT = 30


# =========================================================
# GET FMCSA API KEY
# =========================================================

def get_fmcsa_web_key() -> str:
    """
    Reads the FMCSA WebKey from Streamlit Secrets.

    Streamlit Cloud:
        Manage app
        -> Settings
        -> Secrets

    Add:

        FMCSA_WEB_KEY = "YOUR_KEY"
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
# NORMALIZE INPUT
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
# IDENTIFIER TYPE
# =========================================================

def classify_identifier(
    value: str,
) -> str:

    compact = normalize_identifier(value)

    if compact.isdigit():
        return "MC"

    if compact.startswith("USDOT"):
        return "DOT"

    if compact.startswith("DOT"):
        return "DOT"

    if compact.startswith("MC"):
        return "MC"

    if compact.startswith("MX"):
        return "MX"

    if compact.startswith("FF"):
        return "FF"

    return "UNKNOWN"


# =========================================================
# REMOVE PREFIX
# =========================================================

def remove_prefix(
    value: str,
) -> str:

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
# FMCSA API REQUEST
# =========================================================

def fmcsa_get(
    endpoint: str,
    params: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
):

    web_key = get_fmcsa_web_key()

    if not web_key:

        raise RuntimeError(
            "FMCSA API key is missing. "
            "Add FMCSA_WEB_KEY to Streamlit Secrets."
        )

    url = FMCSA_API_BASE + endpoint

    request_params = {}

    if params:
        request_params.update(params)

    request_params["webKey"] = web_key

    response = requests.get(
        url,
        params=request_params,
        timeout=timeout,
        headers={
            "User-Agent": "MC-Bulk-Streamlit/1.0",
            "Accept": "application/json",
        },
    )

    if response.status_code == 401:

        raise RuntimeError(
            "FMCSA API authentication failed. "
            "Check your WebKey."
        )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    try:
        return response.json()

    except ValueError:

        raise RuntimeError(
            "FMCSA returned an invalid JSON response."
        )


# =========================================================
# FIND VALUE IN NESTED JSON
# =========================================================

def find_value(
    data,
    possible_keys,
):

    if isinstance(data, dict):

        for key, value in data.items():

            normalized_key = (
                str(key)
                .replace("_", "")
                .replace("-", "")
                .lower()
            )

            for wanted in possible_keys:

                normalized_wanted = (
                    wanted
                    .replace("_", "")
                    .replace("-", "")
                    .lower()
                )

                if normalized_key == normalized_wanted:

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
# FIND ALL VALUES
# =========================================================

def find_values(
    data,
    possible_keys,
):

    found = []

    if isinstance(data, dict):

        for key, value in data.items():

            normalized_key = (
                str(key)
                .replace("_", "")
                .replace("-", "")
                .lower()
            )

            for wanted in possible_keys:

                normalized_wanted = (
                    wanted
                    .replace("_", "")
                    .replace("-", "")
                    .lower()
                )

                if normalized_key == normalized_wanted:

                    if value is not None:
                        found.append(value)

            found.extend(
                find_values(
                    value,
                    possible_keys,
                )
            )

    elif isinstance(data, list):

        for item in data:

            found.extend(
                find_values(
                    item,
                    possible_keys,
                )
            )

    return found


# =========================================================
# DETERMINE BROKER / CARRIER
# =========================================================

def determine_business_type(
    data,
) -> str:
    """
    Determine whether the entity is primarily
    a BROKER or CARRIER.

    We look at authority information returned
    by FMCSA.

    If broker authority is active/present and
    carrier authority is not present, return BROKER.

    Otherwise return CARRIER.
    """

    # Search possible broker fields
    broker_values = find_values(
        data,
        [
            "brokerAuthority",
            "broker",
            "brokerStatus",
            "brokerAuthorityStatus",
        ],
    )

    # Search carrier/common/contract fields
    carrier_values = find_values(
        data,
        [
            "commonAuthority",
            "contractAuthority",
            "commonStatus",
            "contractStatus",
            "carrierAuthority",
            "carrierStatus",
        ],
    )

    broker_text = " ".join(
        str(x).upper()
        for x in broker_values
    )

    carrier_text = " ".join(
        str(x).upper()
        for x in carrier_values
    )

    broker_active = any(
        word in broker_text
        for word in (
            "ACTIVE",
            "AUTHORIZED",
            "AUTH",
        )
    )

    carrier_active = any(
        word in carrier_text
        for word in (
            "ACTIVE",
            "AUTHORIZED",
            "AUTH",
        )
    )

    # Broker only
    if broker_active and not carrier_active:
        return "BROKER"

    # If explicit broker field exists
    if (
        "BROKER" in broker_text
        and not carrier_text
    ):
        return "BROKER"

    # Default
    return "CARRIER"


# =========================================================
# DETERMINE OPERATING STATUS
# =========================================================

def determine_operating_status(
    data,
) -> str:
    """
    Return:

        ACTIVE
        INACTIVE

    based on FMCSA status / authority data.
    """

    values = find_values(
        data,
        [
            "allowToOperate",
            "operatingStatus",
            "operatingAuthorityStatus",
            "statusCode",
            "usdotStatus",
            "USDOTStatus",
        ],
    )

    text = " ".join(
        str(x).upper()
        for x in values
    )

    # Explicit inactive conditions
    inactive_words = (
        "INACTIVE",
        "OUT OF SERVICE",
        "OUT-OF-SERVICE",
        "NOT AUTHORIZED",
        "REVOKED",
        "INACTIVE",
    )

    for word in inactive_words:

        if word in text:
            return "INACTIVE"

    # Explicit active conditions
    active_words = (
        "ACTIVE",
        "AUTHORIZED",
        "AUTHORIZED FOR",
    )

    for word in active_words:

        if word in text:
            return "ACTIVE"

    # FMCSA often uses status code A
    if re.search(
        r"\bA\b",
        text,
    ):
        return "ACTIVE"

    return "INACTIVE"


# =========================================================
# EXTRACT EMAIL
# =========================================================

def extract_email(
    data,
) -> str:
    """
    FMCSA may not provide a public email address.

    If the API contains one, use it.
    Otherwise return Not available.
    """

    value = find_value(
        data,
        [
            "email",
            "emailAddress",
            "emailAddr",
            "contactEmail",
        ],
    )

    if value:

        value = str(value).strip()

        if "@" in value:
            return value

    return "Not available"


# =========================================================
# EXTRACT LOCATION
# =========================================================

def extract_location(
    data,
) -> str:

    # Try complete address first
    complete = find_value(
        data,
        [
            "physicalAddress",
            "phyAddress",
        ],
    )

    if complete:

        text = str(
            complete
        ).strip()

        if text:
            return text

    street = find_value(
        data,
        [
            "phyStreet",
            "physicalStreet",
            "businessStreet",
        ],
    )

    city = find_value(
        data,
        [
            "phyCity",
            "physicalCity",
            "businessCity",
        ],
    )

    state = find_value(
        data,
        [
            "phyState",
            "physicalState",
            "businessState",
        ],
    )

    zip_code = find_value(
        data,
        [
            "phyZip",
            "physicalZip",
            "businessZipCode",
            "zipCode",
        ],
    )

    parts = []

    for value in (
        street,
        city,
        state,
        zip_code,
    ):

        if value:

            text = str(value).strip()

            if text:
                parts.append(text)

    return ", ".join(parts)


# =========================================================
# PARSE FMCSA RECORD
# =========================================================

def parse_carrier_data(
    data,
    input_id: str,
) -> Dict[str, str]:

    dot_number = find_value(
        data,
        [
            "dotNumber",
            "USDOTNumber",
            "usdotNumber",
        ],
    )

    mc_number = find_value(
        data,
        [
            "mcNumber",
            "MCNumber",
            "docketNumber",
        ],
    )

    legal_name = find_value(
        data,
        [
            "legalName",
            "LegalName",
        ],
    )

    dba_name = find_value(
        data,
        [
            "dbaName",
            "DBAName",
        ],
    )

    # If API doesn't return MC number,
    # use the input MC.
    if not mc_number:

        if classify_identifier(
            input_id
        ) in (
            "MC",
            "MX",
            "FF",
        ):

            mc_number = remove_prefix(
                input_id
            )

    business_type = determine_business_type(
        data
    )

    operating_status = (
        determine_operating_status(
            data
        )
    )

    email = extract_email(
        data
    )

    location = extract_location(
        data
    )

    return {

        "MC Number": (
            str(mc_number)
            if mc_number
            else ""
        ),

        "Carrier/Broker Name": (
            str(legal_name)
            if legal_name
            else ""
        ),

        "Type": business_type,

        "Operating Status": (
            operating_status
        ),

        "Email Address": email,

        "Location": location,

        # Internal fields
        # These can still be used by the app
        # but won't necessarily be displayed.
        "_dot_number": (
            str(dot_number)
            if dot_number
            else ""
        ),

        "_dba_name": (
            str(dba_name)
            if dba_name
            else ""
        ),

        "_raw": data,
    }


# =========================================================
# SEARCH BY DOT
# =========================================================

def search_by_dot(
    dot_number: str,
) -> Dict[str, str]:

    clean_dot = remove_prefix(
        dot_number
    )

    try:

        data = fmcsa_get(
            "/carriers/" + clean_dot
        )

        if not data:

            return {
                "MC Number": clean_dot,
                "Carrier/Broker Name": "",
                "Type": "",
                "Operating Status": "INACTIVE",
                "Email Address": "Not available",
                "Location": "",
                "_dot_number": clean_dot,
                "_dba_name": "",
                "_error": (
                    "FMCSA record not found."
                ),
            }

        return parse_carrier_data(
            data,
            dot_number,
        )

    except Exception as exc:

        return {
            "MC Number": clean_dot,
            "Carrier/Broker Name": "",
            "Type": "",
            "Operating Status": "INACTIVE",
            "Email Address": "Not available",
            "Location": "",
            "_dot_number": clean_dot,
            "_dba_name": "",
            "_error": str(exc),
        }


# =========================================================
# SEARCH BY MC
# =========================================================

def search_by_mc(
    mc_number: str,
) -> Dict[str, str]:

    clean_mc = remove_prefix(
        mc_number
    )

    try:

        data = fmcsa_get(
            "/carriers/docket-number/"
            + clean_mc
            + "/"
        )

        if not data:

            return {
                "MC Number": clean_mc,
                "Carrier/Broker Name": "",
                "Type": "",
                "Operating Status": "INACTIVE",
                "Email Address": "Not available",
                "Location": "",
                "_dot_number": "",
                "_dba_name": "",
                "_error": (
                    "FMCSA record not found."
                ),
            }

        return parse_carrier_data(
            data,
            mc_number,
        )

    except Exception as exc:

        return {
            "MC Number": clean_mc,
            "Carrier/Broker Name": "",
            "Type": "",
            "Operating Status": "INACTIVE",
            "Email Address": "Not available",
            "Location": "",
            "_dot_number": "",
            "_dba_name": "",
            "_error": str(exc),
        }


# =========================================================
# SEARCH ONE
# =========================================================

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
            "MC Number": "",
            "Carrier/Broker Name": "",
            "Type": "",
            "Operating Status": "INACTIVE",
            "Email Address": "Not available",
            "Location": "",
            "_dot_number": "",
            "_dba_name": "",
            "_error": "Blank input.",
        }

    kind = classify_identifier(
        identifier
    )

    if kind in (
        "MC",
        "MX",
        "FF",
    ):

        return search_by_mc(
            identifier
        )

    if kind == "DOT":

        return search_by_dot(
            identifier
        )

    return {
        "MC Number": identifier,
        "Carrier/Broker Name": "",
        "Type": "",
        "Operating Status": "INACTIVE",
        "Email Address": "Not available",
        "Location": "",
        "_dot_number": "",
        "_dba_name": "",
        "_error": (
            "Unknown identifier type."
        ),
    }


# =========================================================
# BULK SEARCH
# =========================================================

def bulk_fetch(
    identifiers,
    delay_seconds: float = 0.5,
    progress_callback=None,
):

    results = []

    total = len(
        identifiers
    )

    if not get_fmcsa_web_key():

        return [
            {
                "MC Number": "",
                "Carrier/Broker Name": "",
                "Type": "",
                "Operating Status": "INACTIVE",
                "Email Address": "Not available",
                "Location": "",
                "_dot_number": "",
                "_dba_name": "",
                "_error": (
                    "FMCSA API key is missing."
                ),
            }
        ]

    for index, identifier in enumerate(
        identifiers,
        start=1,
    ):

        result = fetch_one(
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
