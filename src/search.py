from __future__ import annotations

import re
import time
from typing import Dict, Optional

import requests
import streamlit as st


# =========================================================
# FMCSA API SETTINGS
# =========================================================

FMCSA_API_BASE = (
    "https://mobile.fmcsa.dot.gov/qc/services"
)

DEFAULT_TIMEOUT = 30


# =========================================================
# 🔑 YOUR API KEY
# =========================================================
#
# DO NOT PUT YOUR REAL KEY DIRECTLY IN THIS FILE.
#
# Put it in:
#
# Streamlit Cloud
# → Your App
# → Settings
# → Secrets
#
# Add:
#
# FMCSA_WEB_KEY = "YOUR_REAL_KEY"
#
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
# NORMALIZE IDENTIFIER
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

    compact = normalize_identifier(
        value
    )

    # Plain numeric input = MC
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

    value = normalize_identifier(
        value
    )

    for prefix in (
        "USDOT",
        "DOT",
        "MC",
        "MX",
        "FF",
    ):

        if value.startswith(prefix):

            return value[
                len(prefix):
            ]

    return value


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
        "https://www.dotsearch.io/dot/"
        + dot
    )


# =========================================================
# FMCSA API REQUEST
# =========================================================

def fmcsa_get(
    endpoint: str,
    params: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
):
    """
    Make an authenticated FMCSA QCMobile API request.
    """

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

    request_params = {}

    if params:
        request_params.update(
            params
        )

    request_params["webKey"] = (
        web_key
    )

    response = requests.get(
        url,
        params=request_params,
        timeout=timeout,
        headers={
            "User-Agent": (
                "MC-Bulk-Streamlit/1.0"
            ),
            "Accept": "application/json",
        },
    )

    # Authentication error
    if response.status_code == 401:

        raise RuntimeError(
            "FMCSA API authentication failed. "
            "Check your WebKey."
        )

    # Not found
    if response.status_code == 404:

        return None

    response.raise_for_status()

    try:

        return response.json()

    except ValueError:

        raise RuntimeError(
            "FMCSA returned a response "
            "that was not valid JSON."
        )


# =========================================================
# FIND FIRST DICT
# =========================================================

def find_first_dict(
    data,
) -> dict:

    if isinstance(data, dict):

        return data

    if isinstance(data, list):

        for item in data:

            if isinstance(item, dict):

                return item

    return {}


# =========================================================
# FIND VALUE RECURSIVELY
# =========================================================

def find_value(
    data,
    possible_keys,
):
    """
    Search nested FMCSA JSON for a value.
    """

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

                if (
                    normalized_key
                    == normalized_wanted
                ):

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
# FLATTEN BASIC CARRIER DATA
# =========================================================

def parse_carrier_data(
    data,
    input_id: str,
) -> Dict[str, str]:
    """
    Convert FMCSA JSON into the columns
    used by the Streamlit app.
    """

    result = {

        "input_id": input_id,

        "status": "FOUND",

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

        "safer_url": "",

        "dotsearch_url": "",

        "error": "",
    }


    # -----------------------------------------------------
    # DOT NUMBER
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "dotNumber",
            "USDOTNumber",
            "usdotNumber",
        ],
    )

    if value is not None:

        result["dot_number"] = str(
            value
        )


    # -----------------------------------------------------
    # MC NUMBER
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "mcNumber",
            "MCNumber",
            "docketNumber",
        ],
    )

    if value is not None:

        result["mc_number"] = str(
            value
        )


    # -----------------------------------------------------
    # LEGAL NAME
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "legalName",
            "LegalName",
        ],
    )

    if value is not None:

        result["legal_name"] = str(
            value
        )


    # -----------------------------------------------------
    # DBA NAME
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "dbaName",
            "DBAName",
        ],
    )

    if value is not None:

        result["dba_name"] = str(
            value
        )


    # -----------------------------------------------------
    # ENTITY TYPE
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "entityType",
            "carrierType",
        ],
    )

    if value is not None:

        result["entity_type"] = str(
            value
        )


    # -----------------------------------------------------
    # USDOT STATUS
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "statusCode",
            "usdotStatus",
            "USDOTStatus",
            "status",
        ],
    )

    if value is not None:

        result["usdot_status"] = str(
            value
        )


    # -----------------------------------------------------
    # OUT OF SERVICE
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "outOfServiceDate",
            "oosDate",
        ],
    )

    if value is not None:

        result["out_of_service_date"] = str(
            value
        )


    # -----------------------------------------------------
    # AUTHORITY
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "operatingAuthorityStatus",
            "authorityStatus",
            "allowToOperate",
        ],
    )

    if value is not None:

        result[
            "operating_authority_status"
        ] = str(value)


    # -----------------------------------------------------
    # STREET
    # -----------------------------------------------------

    street = find_value(
        data,
        [
            "phyStreet",
            "physicalAddress",
            "businessStreet",
        ],
    )

    city = find_value(
        data,
        [
            "phyCity",
            "businessCity",
        ],
    )

    state = find_value(
        data,
        [
            "phyState",
            "businessState",
        ],
    )

    zip_code = find_value(
        data,
        [
            "phyZip",
            "businessZipCode",
            "zipCode",
        ],
    )


    address_parts = []

    for value in (
        street,
        city,
        state,
        zip_code,
    ):

        if value:

            address_parts.append(
                str(value)
            )


    result[
        "physical_address"
    ] = ", ".join(
        address_parts
    )


    # -----------------------------------------------------
    # MAILING ADDRESS
    # -----------------------------------------------------

    mailing_street = find_value(
        data,
        [
            "mailingStreet",
            "mailStreet",
        ],
    )

    mailing_city = find_value(
        data,
        [
            "mailingCity",
            "mailCity",
        ],
    )

    mailing_state = find_value(
        data,
        [
            "mailingState",
            "mailState",
        ],
    )

    mailing_zip = find_value(
        data,
        [
            "mailingZip",
            "mailingZipCode",
            "mailZip",
        ],
    )


    mailing_parts = []

    for value in (
        mailing_street,
        mailing_city,
        mailing_state,
        mailing_zip,
    ):

        if value:

            mailing_parts.append(
                str(value)
            )


    result[
        "mailing_address"
    ] = ", ".join(
        mailing_parts
    )


    # -----------------------------------------------------
    # PHONE
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "telephone",
            "phone",
            "businessPhone",
        ],
    )

    if value is not None:

        result["phone"] = str(
            value
        )


    # -----------------------------------------------------
    # POWER UNITS
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "powerUnits",
            "powerUnit",
            "totalPowerUnits",
        ],
    )

    if value is not None:

        result["power_units"] = str(
            value
        )


    # -----------------------------------------------------
    # DRIVERS
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "drivers",
            "totalDrivers",
            "numberOfDrivers",
        ],
    )

    if value is not None:

        result["drivers"] = str(
            value
        )


    # -----------------------------------------------------
    # MCS-150 DATE
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "mcs150Date",
            "mcs150FormDate",
        ],
    )

    if value is not None:

        result[
            "mcs150_form_date"
        ] = str(value)


    # -----------------------------------------------------
    # MCS-150 MILEAGE
    # -----------------------------------------------------

    value = find_value(
        data,
        [
            "mcs150Mileage",
            "mileage",
        ],
    )

    if value is not None:

        result[
            "mcs150_mileage"
        ] = str(value)


    # -----------------------------------------------------
    # SAFER URL
    # -----------------------------------------------------

    if result["dot_number"]:

        result["safer_url"] = (
            "https://safer.fmcsa.dot.gov/"
            "?searchtype=ANY"
            "&query_type="
            "queryCarrierSnapshot"
            "&query_param=USDOT"
            "&query_string="
            + result["dot_number"]
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


    return result


# =========================================================
# SEARCH BY DOT
# =========================================================

def search_by_dot(
    dot_number: str,
) -> Dict[str, str]:
    """
    Search FMCSA by USDOT number.
    """

    clean_dot = remove_prefix(
        dot_number
    )

    endpoint = (
        "/carriers/"
        + clean_dot
    )

    try:

        data = fmcsa_get(
            endpoint
        )

        if not data:

            return {
                "input_id": dot_number,
                "status": "NOT FOUND",
                "error": (
                    "FMCSA did not return "
                    "a carrier for this DOT number."
                ),
                "safer_url": "",
                "dotsearch_url": "",
            }


        return parse_carrier_data(
            data,
            dot_number,
        )


    except Exception as exc:

        return {
            "input_id": dot_number,
            "status": "ERROR",
            "error": str(exc),
            "safer_url": "",
            "dotsearch_url": "",
        }


# =========================================================
# SEARCH BY MC / DOCKET
# =========================================================

def search_by_mc(
    mc_number: str,
) -> Dict[str, str]:
    """
    Search FMCSA directly by MC/MX/FF docket number.
    """

    clean_mc = normalize_identifier(
        mc_number
    )


    # Remove MC / MX / FF prefix
    clean_mc = remove_prefix(
        clean_mc
    )


    endpoint = (
        "/carriers/docket-number/"
        + clean_mc
        + "/"
    )


    try:

        data = fmcsa_get(
            endpoint
        )

        if not data:

            return {
                "input_id": mc_number,
                "status": "NOT FOUND",
                "error": (
                    "FMCSA did not return "
                    "a carrier for this MC/docket number."
                ),
                "safer_url": "",
                "dotsearch_url": "",
            }


        return parse_carrier_data(
            data,
            mc_number,
        )


    except Exception as exc:

        return {
            "input_id": mc_number,
            "status": "ERROR",
            "error": str(exc),
            "safer_url": "",
            "dotsearch_url": "",
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
    """
    Search one identifier.

    MC/MX/FF:
        Uses the FMCSA docket-number endpoint.

    DOT:
        Uses the FMCSA carrier endpoint.
    """

    identifier = str(
        identifier
    ).strip()


    if not identifier:

        return {
            "input_id": "",
            "status": "SKIPPED",
            "error": "Blank input.",
        }


    kind = classify_identifier(
        identifier
    )


    # -----------------------------------------------------
    # MC / MX / FF
    # -----------------------------------------------------

    if kind in {
        "MC",
        "MX",
        "FF",
    }:

        return search_by_mc(
            identifier
        )


    # -----------------------------------------------------
    # DOT
    # -----------------------------------------------------

    if kind == "DOT":

        return search_by_dot(
            identifier
        )


    # -----------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------

    return {
        "input_id": identifier,
        "status": "ERROR",
        "error": (
            "Unknown identifier type. "
            "Use MC, MX, FF or DOT."
        ),
        "safer_url": "",
        "dotsearch_url": "",
    }


# =========================================================
# BULK SEARCH
# =========================================================

def bulk_fetch(
    identifiers,
    delay_seconds: float = 0.5,
    progress_callback=None,
) -> list[Dict[str, str]]:
    """
    Search multiple MC/DOT identifiers.

    Uses the FMCSA API directly.
    """

    results = []

    total = len(
        identifiers
    )


    # -----------------------------------------------------
    # CHECK API KEY BEFORE STARTING
    # -----------------------------------------------------

    web_key = get_fmcsa_web_key()

    if not web_key:

        error_result = {

            "input_id": "",

            "status": "ERROR",

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

            "safer_url": "",

            "dotsearch_url": "",

            "error": (
                "FMCSA API key is missing. "
                "Go to Streamlit Cloud → "
                "Manage app → Settings → Secrets "
                "and add FMCSA_WEB_KEY."
            ),
        }

        return [
            error_result
        ]


    # -----------------------------------------------------
    # SESSION
    # -----------------------------------------------------

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "MC-Bulk-Streamlit/1.0"
            ),
            "Accept": (
                "application/json"
            ),
        }
    )


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

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
