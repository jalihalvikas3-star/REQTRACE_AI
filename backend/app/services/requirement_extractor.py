import json
import re

from app.models.requirement import Requirement
from app.services.text_cleaner import clean_text
from app.services.sentence_splitter import split_into_sentences
from app.services.gemini_service import generate_response


# =========================================================
# LARGE DOCUMENT SETTINGS
# =========================================================

# For large SRS documents, do not send the entire document
# to Gemini in one enormous prompt.
#
# This keeps 1000+ requirement comparisons practical.
#
# Small documents:
#     Gemini extraction
#
# Large documents:
#     Fast local rule-based extraction

LARGE_DOCUMENT_THRESHOLD = 300


# =========================================================
# REQUIREMENT KEYWORDS
# =========================================================

REQUIREMENT_KEYWORDS = [
    "shall",
    "must",
    "should",
    "will",
    "required to",
    "needs to",
    "need to",
    "has to",
    "have to",
    "can",
    "able to",
    "allow",
    "allows",
    "enable",
    "enables",
    "provide",
    "provides",
    "support",
    "supports",
]


# =========================================================
# EXCLUDED PATTERNS
# =========================================================

EXCLUDED_PATTERNS = [
    "author:",
    "authors:",
    "journal:",
    "designation:",
    "mobile number:",
    "college address:",
    "phone:",
    "email:",
    "copyright",
    "references",
    "bibliography",
    "table of contents",
    "acknowledgement",
    "acknowledgment",
]


# =========================================================
# REQUIREMENT ID
# =========================================================

def extract_requirement_id(
    sentence,
    fallback_count
):

    match = re.search(
        r"\bREQ[-_ ]?(\d+)\b",
        sentence,
        re.IGNORECASE
    )

    if match:

        number = int(
            match.group(1)
        )

        return f"REQ-{number:03}"

    return f"REQ-{fallback_count:03}"


# =========================================================
# REQUIREMENT VALIDATION
# =========================================================

def is_requirement(
    sentence
):

    sentence_lower = (
        sentence
        .lower()
        .strip()
    )

    # -----------------------------------------------------
    # Ignore extremely short sentences.
    # -----------------------------------------------------

    if len(
        sentence_lower.split()
    ) < 5:

        return False

    # -----------------------------------------------------
    # Ignore known non-requirement content.
    # -----------------------------------------------------

    if any(
        pattern in sentence_lower
        for pattern in EXCLUDED_PATTERNS
    ):

        return False

    # -----------------------------------------------------
    # Explicit requirement ID
    # -----------------------------------------------------

    has_requirement_id = bool(
        re.search(
            r"\bREQ[-_ ]?\d+\b",
            sentence_lower
        )
    )

    # -----------------------------------------------------
    # Requirement keyword
    # -----------------------------------------------------

    has_requirement_keyword = any(
        keyword in sentence_lower
        for keyword in REQUIREMENT_KEYWORDS
    )

    # -----------------------------------------------------
    # Common requirement/action patterns
    # -----------------------------------------------------

    action_patterns = [

        r"\buser(s)?\s+(shall|must|should|can|will)\b",

        r"\badministrator(s)?\s+(shall|must|should|can|will)\b",

        r"\badmin\s+(shall|must|should|can|will)\b",

        r"\blibrarian(s)?\s+(shall|must|should|can|will)\b",

        r"\bpatient(s)?\s+(shall|must|should|can|will)\b",

        r"\bdoctor(s)?\s+(shall|must|should|can|will)\b",

        r"\bstaff\s+(shall|must|should|can|will)\b",

        r"\bmember(s)?\s+(shall|must|should|can|will)\b",

        r"\bthe\s+\w+\s+(shall|must|should|can|will)\b",

        r"\bsystem\s+(shall|must|should|can|will)\b",

        r"\bapplication\s+(shall|must|should|can|will)\b",

        r"\bsoftware\s+(shall|must|should|can|will)\b",

        r"\bplatform\s+(shall|must|should|can|will)\b",

        r"\bmodule\s+(shall|must|should|can|will)\b",

        r"\bthe\s+system\s+(shall|must|should|can|will)\b",

        r"\bthe\s+application\s+(shall|must|should|can|will)\b",

        r"\bthe\s+software\s+(shall|must|should|can|will)\b",

        r"\bthe\s+platform\s+(shall|must|should|can|will)\b",

        r"\bthe\s+module\s+(shall|must|should|can|will)\b",

    ]

    has_action_pattern = any(
        re.search(
            pattern,
            sentence_lower
        )
        for pattern in action_patterns
    )

    # -----------------------------------------------------
    # Strong rule:
    #
    # REQ-ID + requirement keyword
    #
    # OR
    #
    # actor + requirement keyword
    #
    # OR
    #
    # system/action pattern
    # -----------------------------------------------------

    if (
        has_requirement_id
        and
        has_requirement_keyword
    ):

        return True

    if has_action_pattern:

        return True

    # -----------------------------------------------------
    # Generic requirement sentence
    # -----------------------------------------------------

    if has_requirement_keyword:

        # Avoid accepting obvious prose sentences.

        prose_patterns = [

            "this document",

            "this section",

            "in this document",

            "the purpose of",

            "the objective of",

            "this project aims",

            "is defined as",

            "refers to",

        ]

        if any(
            pattern in sentence_lower
            for pattern in prose_patterns
        ):

            return False

        return True

    return False


# =========================================================
# GEMINI JSON EXTRACTION
# =========================================================

def _extract_json_from_response(
    response_text
):

    response_text = (
        response_text
        .strip()
    )

    code_block_match = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        response_text,
        re.DOTALL | re.IGNORECASE
    )

    if code_block_match:

        response_text = (
            code_block_match
            .group(1)
            .strip()
        )

    return json.loads(
        response_text
    )


# =========================================================
# GEMINI EXTRACTION
# =========================================================

def _extract_with_gemini(
    cleaned_text
):

    prompt = f"""
You are a software requirements extraction system.

Extract ONLY actual software/system requirements from
the SRS text below.

A requirement may describe:

- what the system must do
- what a user must be able to do
- what an administrator must do
- what a librarian must do
- what a patient must do
- what a doctor must do
- what staff must do
- what another system actor must do

Valid requirement keywords include:

shall
must
should
will
can
able to
required to
needs to
need to
allow
enable
provide
support

Do NOT extract:

- author information
- contact information
- references
- bibliography
- headings
- introductions
- explanations
- background information
- unrelated sentences

IMPORTANT:

1. Preserve requirement IDs when present.
2. Preserve the requirement wording.
3. Do not invent requirements.
4. Do not modify the meaning.
5. Return ONLY valid JSON.
6. The JSON must be an array.

Required JSON format:

[
  {{
    "id": "REQ-001",
    "type": "Functional",
    "text": "REQ-001 — The system shall ..."
  }}
]

SRS TEXT:

{cleaned_text}
"""

    response = generate_response(
        prompt
    )

    data = _extract_json_from_response(
        response
    )

    if not isinstance(
        data,
        list
    ):

        raise ValueError(
            "Gemini response is not a JSON array."
        )

    return data


# =========================================================
# BUILD GEMINI REQUIREMENTS
# =========================================================

def _build_requirements_from_gemini(
    data
):

    requirements = []

    fallback_count = 1

    used_ids = set()

    for item in data:

        if not isinstance(
            item,
            dict
        ):

            continue

        text = str(
            item.get(
                "text",
                ""
            )
        ).strip()

        if not text:

            continue

        # -------------------------------------------------
        # Validate Gemini result
        # -------------------------------------------------

        if not is_requirement(
            text
        ):

            continue

        # -------------------------------------------------
        # Determine ID
        # -------------------------------------------------

        provided_id = str(
            item.get(
                "id",
                ""
            )
        ).strip()

        if re.fullmatch(
            r"REQ-\d{3}",
            provided_id,
            re.IGNORECASE
        ):

            req_id = (
                provided_id
                .upper()
            )

        else:

            req_id = extract_requirement_id(
                text,
                fallback_count
            )

        # -------------------------------------------------
        # Prevent duplicate IDs
        # -------------------------------------------------

        if req_id in used_ids:

            while (
                f"REQ-{fallback_count:03}"
                in used_ids
            ):

                fallback_count += 1

            req_id = (
                f"REQ-{fallback_count:03}"
            )

        used_ids.add(
            req_id
        )

        # -------------------------------------------------
        # Requirement type
        # -------------------------------------------------

        requirement_type = str(
            item.get(
                "type",
                "Functional"
            )
        ).strip()

        if not requirement_type:

            requirement_type = (
                "Functional"
            )

        # -------------------------------------------------
        # Create requirement
        # -------------------------------------------------

        req = Requirement(
            req_id,
            requirement_type,
            text
        )

        requirements.append(
            req
        )

        fallback_count += 1

    return requirements


# =========================================================
# RULE-BASED FALLBACK
# =========================================================

def _extract_with_rules(
    cleaned_text
):

    sentences = split_into_sentences(
        cleaned_text
    )

    requirements = []

    fallback_count = 1

    used_ids = set()

    for sentence in sentences:

        sentence = (
            sentence
            .strip()
        )

        if not is_requirement(
            sentence
        ):

            continue

        req_id = extract_requirement_id(
            sentence,
            fallback_count
        )

        # -------------------------------------------------
        # Prevent duplicate IDs
        # -------------------------------------------------

        if req_id in used_ids:

            while (
                f"REQ-{fallback_count:03}"
                in used_ids
            ):

                fallback_count += 1

            req_id = (
                f"REQ-{fallback_count:03}"
            )

        used_ids.add(
            req_id
        )

        req = Requirement(
            req_id,
            "Functional",
            sentence
        )

        requirements.append(
            req
        )

        fallback_count += 1

    return requirements


# =========================================================
# MAIN EXTRACTION PIPELINE
# =========================================================

def extract_requirements(
    text
):

    # =====================================================
    # CLEAN TEXT
    # =====================================================

    cleaned_text = clean_text(
        text
    )

    # =====================================================
    # LARGE DOCUMENT FAST PATH
    # =====================================================
    #
    # First inspect the document locally.
    #
    # If it contains a large number of requirement-like
    # sentences, skip the expensive single huge Gemini call.
    #
    # This is the important change for 1000+ requirements.
    # =====================================================

    try:

        candidate_sentences = (
            split_into_sentences(
                cleaned_text
            )
        )

        requirement_candidates = [
            sentence
            for sentence in candidate_sentences
            if is_requirement(
                sentence
            )
        ]

    except Exception as e:

        print(
            "[Fast Path] Candidate detection failed:"
            f" {e}"
        )

        requirement_candidates = []

    # =====================================================
    # LARGE DOCUMENT
    # =====================================================

    if (
        len(requirement_candidates)
        >= LARGE_DOCUMENT_THRESHOLD
    ):

        print(
            "[Large SRS] Detected "
            f"{len(requirement_candidates)} "
            "requirement candidates."
        )

        print(
            "[Large SRS] Using fast "
            "rule-based extraction."
        )

        requirements = (
            _extract_with_rules(
                cleaned_text
            )
        )

        print(
            "[Large SRS] Extracted "
            f"{len(requirements)} requirements."
        )

        return requirements

    # =====================================================
    # SMALL / NORMAL DOCUMENT
    # =====================================================

    try:

        gemini_data = (
            _extract_with_gemini(
                cleaned_text
            )
        )

        requirements = (
            _build_requirements_from_gemini(
                gemini_data
            )
        )

        if requirements:

            print(
                "[Gemini] Extracted "
                f"{len(requirements)} requirements."
            )

            return requirements

        print(
            "[Gemini] Returned no valid "
            "requirements."
        )

    except Exception as e:

        print(
            "[Gemini] Requirement extraction "
            f"failed: {e}"
        )

    # =====================================================
    # RULE-BASED FALLBACK
    # =====================================================

    print(
        "[Fallback] Using rule-based extraction."
    )

    requirements = (
        _extract_with_rules(
            cleaned_text
        )
    )

    print(
        "[Fallback] Extracted "
        f"{len(requirements)} requirements."
    )

    return requirements