# =========================================================
# RELATIONSHIP REVIEW SERVICE
# =========================================================

from typing import Dict, List


# =========================================================
# CONFIDENCE THRESHOLDS
# =========================================================

# 90% or above:
# Relationship is considered strong enough to accept automatically.

AUTO_ACCEPT_THRESHOLD = 0.85


# 75% to below 90%:
# Relationship requires human/admin review.

REVIEW_THRESHOLD = 0.75


# =========================================================
# VALID STATUSES
# =========================================================

VALID_STATUSES = {
    "AUTO_ACCEPTED",
    "PENDING",
    "ACCEPTED",
    "REJECTED",
}


# =========================================================
# NORMALIZE CONFIDENCE
# =========================================================

def normalize_confidence(value):
    """
    Convert confidence into a value between 0 and 1.

    Examples:

        0.76  -> 0.76
        76    -> 0.76
        "76%" -> 0.76
    """

    try:

        if isinstance(value, str):

            value = value.strip()

            if value.endswith("%"):
                value = value[:-1]

            value = float(value)

        else:

            value = float(value)

    except (
        TypeError,
        ValueError
    ):

        return 0.0


    # Convert percentage-style values.

    if value > 1:
        value = value / 100.0


    # Keep value inside valid range.

    value = max(
        0.0,
        min(
            1.0,
            value
        )
    )


    return round(
        value,
        2
    )


# =========================================================
# DETERMINE INITIAL STATUS
# =========================================================

def determine_relationship_status(
    confidence
):
    """
    Determine whether a detected relationship should
    be automatically accepted, reviewed, or rejected.

    HIGH CONFIDENCE
        >= 0.90
        AUTO_ACCEPTED

    MEDIUM CONFIDENCE
        >= 0.75 and < 0.90
        PENDING

    LOW CONFIDENCE
        < 0.75
        REJECTED
    """

    confidence = normalize_confidence(
        confidence
    )


    if confidence >= AUTO_ACCEPT_THRESHOLD:

        return "AUTO_ACCEPTED"


    if confidence >= REVIEW_THRESHOLD:

        return "PENDING"


    return "REJECTED"


# =========================================================
# REVIEW RELATIONSHIPS
# =========================================================

def review_relationships(
    relationships: List[Dict]
):
    """
    Prepare detected relationships for scalable review.

    Strong relationships are automatically accepted.

    Medium-confidence relationships are sent to the
    reviewer as PENDING.

    Low-confidence relationships are automatically rejected.
    """

    reviewed = []

    seen = set()


    for relationship in relationships:

        if not isinstance(
            relationship,
            dict
        ):
            continue


        source = str(
            relationship.get(
                "source",
                ""
            )
        ).strip()


        target = str(
            relationship.get(
                "target",
                ""
            )
        ).strip()


        if not source or not target:

            continue


        # -------------------------------------------------
        # Do not allow self relationships.
        # -------------------------------------------------

        if source == target:

            continue


        # -------------------------------------------------
        # Prevent duplicate relationships.
        # -------------------------------------------------

        relationship_key = (
            source,
            target
        )

        reverse_key = (
            target,
            source
        )


        if (
            relationship_key in seen
            or reverse_key in seen
        ):

            continue


        seen.add(
            relationship_key
        )


        # -------------------------------------------------
        # Confidence
        # -------------------------------------------------

        confidence = normalize_confidence(
            relationship.get(
                "confidence",
                relationship.get(
                    "similarity",
                    0.0
                )
            )
        )


        # -------------------------------------------------
        # Determine status
        # -------------------------------------------------

        status = determine_relationship_status(
            confidence
        )


        # -------------------------------------------------
        # Evidence
        # -------------------------------------------------

        evidence = str(
            relationship.get(
                "evidence",
                ""
            )
        ).strip()


        if not evidence:

            if status == "AUTO_ACCEPTED":

                evidence = (
                    "High-confidence relationship "
                    "automatically accepted."
                )

            elif status == "PENDING":

                evidence = (
                    "Medium-confidence relationship "
                    "requires reviewer validation."
                )

            else:

                evidence = (
                    "Low-confidence relationship "
                    "automatically rejected."
                )


        # -------------------------------------------------
        # Build reviewed relationship
        # -------------------------------------------------

        reviewed.append({

            "source":
                source,

            "target":
                target,

            "relation":
                relationship.get(
                    "relation",
                    "RELATED_TO"
                ),

            "confidence":
                confidence,

            "evidence":
                evidence,

            "status":
                status,

        })


    return reviewed


# =========================================================
# UPDATE RELATIONSHIP STATUS
# =========================================================

def update_relationship_status(
    relationships,
    source,
    target,
    status
):
    """
    Allow the reviewer/admin to change the status
    of a relationship.

    AUTO_ACCEPTED relationships can still be manually
    rejected if a reviewer identifies an error.
    """

    status = str(
        status
    ).strip().upper()


    if status not in VALID_STATUSES:

        raise ValueError(
            "Invalid relationship status."
        )


    updated = []


    for relationship in relationships:

        item = dict(
            relationship
        )


        if (
            item.get("source") == source
            and
            item.get("target") == target
        ):

            item["status"] = status


        updated.append(
            item
        )


    return updated


# =========================================================
# GET PENDING RELATIONSHIPS
# =========================================================

def get_pending_relationships(
    relationships
):
    return [
        relationship
        for relationship in relationships
        if relationship.get(
            "status",
            "PENDING"
        ) == "PENDING"
    ]


# =========================================================
# GET AUTO-ACCEPTED RELATIONSHIPS
# =========================================================

def get_auto_accepted_relationships(
    relationships
):
    return [
        relationship
        for relationship in relationships
        if relationship.get(
            "status"
        ) == "AUTO_ACCEPTED"
    ]


# =========================================================
# GET ACCEPTED RELATIONSHIPS
# =========================================================

def get_accepted_relationships(
    relationships
):
    return [
        relationship
        for relationship in relationships
        if relationship.get(
            "status"
        ) in {
            "ACCEPTED",
            "AUTO_ACCEPTED",
        }
    ]


# =========================================================
# GET REJECTED RELATIONSHIPS
# =========================================================

def get_rejected_relationships(
    relationships
):
    return [
        relationship
        for relationship in relationships
        if relationship.get(
            "status"
        ) == "REJECTED"
    ]