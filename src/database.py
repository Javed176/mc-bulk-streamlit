# =========================================================
# ACCESS REQUESTS
# =========================================================

def create_access_request(
    whatsapp_number: str,
):
    """
    Create an access request using only a WhatsApp number.

    Duplicate protection:
    - If the number already has a WAITING request,
      no new request is created.
    - If the previous request was APPROVED,
      the user sees APPROVED.
    - If the previous request was REJECTED,
      a new request is allowed.
    """

    client = get_supabase()

    number = str(
        whatsapp_number
    ).strip()

    if not number:
        raise ValueError(
            "WhatsApp number is required."
        )

    # -----------------------------------------------------
    # Check previous request
    # -----------------------------------------------------

    response = (
        client.table("access_requests")
        .select("*")
        .eq(
            "whatsapp_number",
            number,
        )
        .order(
            "created_at",
            desc=True,
        )
        .limit(1)
        .execute()
    )

    existing = (
        response.data[0]
        if response.data
        else None
    )

    # -----------------------------------------------------
    # Existing request
    # -----------------------------------------------------

    if existing:

        status = str(
            existing.get(
                "status",
                "waiting",
            )
        ).lower()

        # Waiting = don't create spam
        if status == "waiting":

            return {
                "success": False,
                "status": "waiting",
                "message": (
                    "Your access request is "
                    "already waiting for admin review."
                ),
                "request": existing,
            }

        # Approved = tell user it's approved
        if status == "approved":

            return {
                "success": False,
                "status": "approved",
                "message": (
                    "Your access request has "
                    "already been approved."
                ),
                "request": existing,
            }

        # Rejected = allow a fresh request
        # We continue below.

    # -----------------------------------------------------
    # Create new request
    # -----------------------------------------------------

    insert_response = (
        client.table("access_requests")
        .insert(
            {
                "whatsapp_number": number,
                "status": "waiting",
            }
        )
        .execute()
    )

    return {
        "success": True,
        "status": "waiting",
        "message": (
            "Access request submitted. "
            "The administrator will contact you on WhatsApp."
        ),
        "request": (
            insert_response.data[0]
            if insert_response.data
            else None
        ),
    }


def list_access_requests(
    status: str | None = None,
):

    client = get_supabase()

    query = (
        client.table("access_requests")
        .select("*")
        .order(
            "created_at",
            desc=True,
        )
    )

    if status:

        query = query.eq(
            "status",
            status,
        )

    response = query.execute()

    return response.data or []


def get_access_request(
    whatsapp_number: str,
):

    client = get_supabase()

    number = str(
        whatsapp_number
    ).strip()

    response = (
        client.table("access_requests")
        .select("*")
        .eq(
            "whatsapp_number",
            number,
        )
        .order(
            "created_at",
            desc=True,
        )
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def update_access_request_status(
    request_id: str,
    status: str,
    reviewed_by: str = "",
):

    status = str(
        status
    ).strip().lower()

    if status not in {
        "waiting",
        "approved",
        "rejected",
    }:

        raise ValueError(
            "Invalid access request status."
        )

    client = get_supabase()

    values = {
        "status": status,
    }

    if status in {
        "approved",
        "rejected",
    }:

        values["reviewed_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        values["reviewed_by"] = (
            str(
                reviewed_by
            ).strip()
        )

    else:

        values["reviewed_at"] = None
        values["reviewed_by"] = None

    return (
        client.table("access_requests")
        .update(values)
        .eq(
            "id",
            request_id,
        )
        .execute()
    )
