import re


# =========================================================
# RULE-BASED COMPONENT MAPPING
# =========================================================

ACTION_COMPONENTS = {
    "register": "Registration Module",
    "registration": "Registration Module",

    "login": "Authentication Module",
    "log in": "Authentication Module",
    "authenticate": "Authentication Module",
    "authentication": "Authentication Module",

    "search": "Search Module",
    "find": "Search Module",
    "filter": "Search Module",

    "add": "Management Module",
    "create": "Management Module",
    "update": "Management Module",
    "delete": "Management Module",
    "remove": "Management Module",
    "manage": "Management Module",
    "maintain": "Management Module",

    "borrow": "Transaction Module",
    "return": "Transaction Module",
    "issue": "Transaction Module",
    "purchase": "Transaction Module",

    "pay": "Payment Module",
    "payment": "Payment Module",

    "transaction": "Transaction Module",

    "generate": "Report Generation Module",
    "report": "Report Generation Module",
    "export": "Report Generation Module",

    "notify": "Notification Module",
    "notification": "Notification Module",
    "email": "Notification Module",
    "alert": "Notification Module",

    "upload": "File Management Module",
    "download": "File Management Module",
    "file": "File Management Module",

    "store": "Data Management Module",
    "save": "Data Management Module",
    "retrieve": "Data Management Module",
    "database": "Data Management Module",

    "display": "User Interface Module",
    "view": "User Interface Module",
    "interface": "User Interface Module",
}


# =========================================================
# RULE-BASED COMPONENT EXTRACTION
# =========================================================

def _extract_components_with_rules(requirement_text):
    """
    Fast keyword-based component extraction.

    This is intentionally used directly so that
    temporary Gemini 503/rate-limit problems do not
    delay SRS processing.
    """

    text = requirement_text.lower()

    components = []

    for keyword, component in ACTION_COMPONENTS.items():

        pattern = (
            r"\b"
            + re.escape(keyword)
            + r"\b"
        )

        if re.search(pattern, text):

            if component not in components:
                components.append(component)

    return components


# =========================================================
# PUBLIC COMPONENT EXTRACTION
# =========================================================

def extract_components(requirement_text):
    """
    Extract components for a requirement.

    Uses the existing rule-based mapping directly
    for fast and reliable processing.
    """

    components = _extract_components_with_rules(
        requirement_text
    )

    print(
        "[Component] Components for "
        f"requirement: {components}"
    )

    return components