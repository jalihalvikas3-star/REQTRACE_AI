# =========================================================
# REQUIREMENT MUTATION DETECTOR
# =========================================================
#
# Detects:
#   - Added requirements
#   - Deleted requirements
#   - Modified requirements
#
# IMPORTANT:
# The extractor may generate an internal ID such as:
#
#     id   = REQ-1008
#     text = REQ-0998 — The system shall ...
#
# Therefore we extract the REAL requirement number from
# the beginning of the requirement text.
#
# Example:
#
#     internal ID : REQ-1008
#     logical ID  : REQ-0998
#
# The logical ID is used for comparison.
#
# =========================================================

import re
from typing import Any, Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =========================================================
# CONFIGURATION
# =========================================================

SEMANTIC_MODIFIED_THRESHOLD = 0.86

MIN_BEST_MARGIN = 0.04

POSITION_WINDOW = 25

MAX_CANDIDATES_PER_REQUIREMENT = 5


# =========================================================
# REQUIREMENT NUMBER PATTERN
# =========================================================

REQUIREMENT_ID_PATTERN = re.compile(
    r"^\s*(REQ-\d+)\s*(?:[-—:.)])?",
    re.IGNORECASE
)


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(
    text: Any
) -> str:

    if text is None:
        return ""

    return " ".join(
        str(text)
        .lower()
        .strip()
        .split()
    )


# =========================================================
# GET INTERNAL ID
# =========================================================

def get_requirement_id(
    requirement: Any
) -> str:

    value = getattr(
        requirement,
        "id",
        ""
    )

    if value is None:
        return ""

    return str(
        value
    ).strip()


# =========================================================
# GET TEXT
# =========================================================

def get_requirement_text(
    requirement: Any
) -> str:

    value = getattr(
        requirement,
        "text",
        ""
    )

    if value is None:
        return ""

    return str(
        value
    ).strip()


# =========================================================
# GET LOGICAL REQUIREMENT ID
# =========================================================

def get_logical_requirement_id(
    requirement: Any
) -> str:
    """
    Extract the real requirement ID from the requirement
    text whenever possible.

    Example:

        internal id:
            REQ-1008

        text:
            REQ-0998 — The system shall allow...

        result:
            REQ-0998
    """

    text = get_requirement_text(
        requirement
    )

    match = REQUIREMENT_ID_PATTERN.match(
        text
    )

    if match:

        return match.group(
            1
        ).upper()

    # -----------------------------------------------------
    # Fallback to internal ID.
    # -----------------------------------------------------

    internal_id = get_requirement_id(
        requirement
    )

    return internal_id.upper()


# =========================================================
# REMOVE REQUIREMENT PREFIX FROM TEXT
# =========================================================

def remove_requirement_prefix(
    text: Any
) -> str:
    """
    Remove:

        REQ-0001 —
        REQ-0001 -
        REQ-0001 :
        REQ-0001 )

    from the beginning of requirement text.

    This prevents an ID renumbering from influencing
    semantic similarity.
    """

    if text is None:
        return ""

    value = str(
        text
    ).strip()

    value = re.sub(
        r"^\s*REQ-\d+\s*(?:[-—:.)])\s*",
        "",
        value,
        flags=re.IGNORECASE
    )

    return value


# =========================================================
# NORMALIZED REQUIREMENT CONTENT
# =========================================================

def normalized_requirement_content(
    requirement: Any
) -> str:

    return normalize_text(
        remove_requirement_prefix(
            get_requirement_text(
                requirement
            )
        )
    )


# =========================================================
# ADDED RESULT
# =========================================================

def make_added(
    requirement: Any
) -> Dict[str, Any]:

    return {
        "id": get_requirement_id(
            requirement
        ),

        "logical_id":
            get_logical_requirement_id(
                requirement
            ),

        "text":
            get_requirement_text(
                requirement
            )
    }


# =========================================================
# DELETED RESULT
# =========================================================

def make_deleted(
    requirement: Any
) -> Dict[str, Any]:

    return {
        "id": get_requirement_id(
            requirement
        ),

        "logical_id":
            get_logical_requirement_id(
                requirement
            ),

        "text":
            get_requirement_text(
                requirement
            )
    }


# =========================================================
# MODIFIED RESULT
# =========================================================

def make_modified(
    old_requirement: Any,
    new_requirement: Any,
    confidence: float
) -> Dict[str, Any]:

    return {
        "id":
            get_requirement_id(
                new_requirement
            ),

        "old_id":
            get_requirement_id(
                old_requirement
            ),

        "logical_id":
            get_logical_requirement_id(
                new_requirement
            ),

        "old":
            get_requirement_text(
                old_requirement
            ),

        "new":
            get_requirement_text(
                new_requirement
            ),

        "confidence":
            round(
                float(confidence),
                3
            )
    }


# =========================================================
# BUILD EXACT TEXT INDEX
# =========================================================

def build_text_index(
    requirements: List[Any]
) -> Dict[str, List[int]]:

    index = {}

    for position, requirement in enumerate(
        requirements
    ):

        text = normalized_requirement_content(
            requirement
        )

        if not text:
            continue

        index.setdefault(
            text,
            []
        ).append(
            position
        )

    return index


# =========================================================
# EXACT CONTENT MATCHING
# =========================================================

def match_exact_text(
    old_requirements: List[Any],
    new_requirements: List[Any],
    old_used: set,
    new_used: set
) -> int:
    """
    Exact requirement CONTENT match.

    The REQ number at the beginning is ignored.

    Therefore:

        REQ-0098 — System shall create account.

    and:

        REQ-0101 — System shall create account.

    are considered unchanged.
    """

    old_index = build_text_index(
        old_requirements
    )

    new_index = build_text_index(
        new_requirements
    )

    matched = 0

    for text, old_positions in old_index.items():

        new_positions = new_index.get(
            text,
            []
        )

        if not new_positions:
            continue

        available_old = [
            position
            for position in old_positions
            if position not in old_used
        ]

        available_new = [
            position
            for position in new_positions
            if position not in new_used
        ]

        count = min(
            len(available_old),
            len(available_new)
        )

        for index in range(
            count
        ):

            old_position = (
                available_old[index]
            )

            new_position = (
                available_new[index]
            )

            old_used.add(
                old_position
            )

            new_used.add(
                new_position
            )

            matched += 1

    return matched


# =========================================================
# LOGICAL ID MATCHING
# =========================================================

def match_same_logical_id(
    old_requirements: List[Any],
    new_requirements: List[Any],
    old_used: set,
    new_used: set,
    modified: List[Dict[str, Any]]
) -> Tuple[int, int]:
    """
    Match using the REAL REQ number found inside text.

    Example:

        old internal ID:
            REQ-0929

        old text:
            REQ-0929 — ...

        new internal ID:
            REQ-1008

        new text:
            REQ-0929 — ...

    These belong to the same logical requirement.

    If the content differs, it becomes MODIFIED.
    """

    new_by_logical_id = {}

    for new_position, requirement in enumerate(
        new_requirements
    ):

        if new_position in new_used:
            continue

        logical_id = get_logical_requirement_id(
            requirement
        )

        if not logical_id:
            continue

        new_by_logical_id.setdefault(
            logical_id,
            []
        ).append(
            new_position
        )

    common_count = 0
    modified_count = 0

    for old_position, old_requirement in enumerate(
        old_requirements
    ):

        if old_position in old_used:
            continue

        logical_id = get_logical_requirement_id(
            old_requirement
        )

        if not logical_id:
            continue

        candidates = new_by_logical_id.get(
            logical_id,
            []
        )

        new_position = None

        for candidate in candidates:

            if candidate not in new_used:

                new_position = candidate

                break

        if new_position is None:
            continue

        new_requirement = new_requirements[
            new_position
        ]

        old_used.add(
            old_position
        )

        new_used.add(
            new_position
        )

        common_count += 1

        old_content = (
            normalized_requirement_content(
                old_requirement
            )
        )

        new_content = (
            normalized_requirement_content(
                new_requirement
            )
        )

        if old_content != new_content:

            modified.append(
                make_modified(
                    old_requirement,
                    new_requirement,
                    1.0
                )
            )

            modified_count += 1

    return (
        common_count,
        modified_count
    )


# =========================================================
# BUILD TF-IDF MATRIX
# =========================================================

def build_similarity_matrix(
    old_items: List[Tuple[int, Any]],
    new_items: List[Tuple[int, Any]]
):

    old_texts = [
        normalized_requirement_content(
            requirement
        )

        for _, requirement
        in old_items
    ]

    new_texts = [
        normalized_requirement_content(
            requirement
        )

        for _, requirement
        in new_items
    ]

    all_texts = (
        old_texts
        +
        new_texts
    )

    if not any(
        all_texts
    ):
        return None

    try:

        vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            min_df=1,
            max_features=50000,
            sublinear_tf=True
        )

        vectors = vectorizer.fit_transform(
            all_texts
        )

        old_count = len(
            old_texts
        )

        old_vectors = vectors[
            :old_count
        ]

        new_vectors = vectors[
            old_count:
        ]

        return cosine_similarity(
            old_vectors,
            new_vectors
        )

    except Exception as error:

        print(
            "[Mutation] TF-IDF failed:"
            f" {error}"
        )

        return None


# =========================================================
# POSITION SCORE
# =========================================================

def calculate_position_score(
    old_position: int,
    new_position: int,
    old_count: int,
    new_count: int
) -> float:

    if old_count <= 1:

        old_ratio = 0.0

    else:

        old_ratio = (
            old_position
            /
            (old_count - 1)
        )

    if new_count <= 1:

        new_ratio = 0.0

    else:

        new_ratio = (
            new_position
            /
            (new_count - 1)
        )

    distance = abs(
        old_ratio
        -
        new_ratio
    )

    return max(
        0.0,
        1.0 - distance
    )


# =========================================================
# SEMANTIC MATCHING
# =========================================================

def semantic_match(
    old_requirements: List[Any],
    new_requirements: List[Any],
    old_used: set,
    new_used: set,
    modified: List[Dict[str, Any]]
) -> Tuple[int, int]:

    unmatched_old = [
        (
            position,
            requirement
        )

        for position, requirement
        in enumerate(old_requirements)

        if position not in old_used
    ]

    unmatched_new = [
        (
            position,
            requirement
        )

        for position, requirement
        in enumerate(new_requirements)

        if position not in new_used
    ]

    if not unmatched_old:
        return (
            0,
            0
        )

    if not unmatched_new:
        return (
            0,
            0
        )

    similarity_matrix = build_similarity_matrix(
        unmatched_old,
        unmatched_new
    )

    if similarity_matrix is None:
        return (
            0,
            0
        )

    old_count = len(
        old_requirements
    )

    new_count = len(
        new_requirements
    )

    candidates = []

    # =====================================================
    # FIND SAFE CANDIDATES
    # =====================================================

    for old_local_position in range(
        len(unmatched_old)
    ):

        old_position, old_requirement = (
            unmatched_old[
                old_local_position
            ]
        )

        candidate_list = []

        for new_local_position in range(
            len(unmatched_new)
        ):

            new_position, new_requirement = (
                unmatched_new[
                    new_local_position
                ]
            )

            # -------------------------------------------------
            # POSITION PROTECTION
            # -------------------------------------------------

            position_difference = abs(
                old_position
                -
                new_position
            )

            size_difference = abs(
                old_count
                -
                new_count
            )

            allowed_window = (
                POSITION_WINDOW
                +
                size_difference
            )

            if (
                position_difference
                >
                allowed_window
            ):
                continue

            # -------------------------------------------------
            # SEMANTIC SCORE
            # -------------------------------------------------

            similarity_score = float(
                similarity_matrix[
                    old_local_position
                ][
                    new_local_position
                ]
            )

            if (
                similarity_score
                <
                SEMANTIC_MODIFIED_THRESHOLD
            ):
                continue

            # -------------------------------------------------
            # POSITION SCORE
            # -------------------------------------------------

            position_score = (
                calculate_position_score(
                    old_position,
                    new_position,
                    old_count,
                    new_count
                )
            )

            # -------------------------------------------------
            # FINAL SCORE
            # -------------------------------------------------

            final_score = (
                similarity_score * 0.90
                +
                position_score * 0.10
            )

            candidate_list.append(
                (
                    final_score,
                    similarity_score,
                    position_score,
                    old_local_position,
                    new_local_position
                )
            )

        candidate_list.sort(
            reverse=True,
            key=lambda item: item[0]
        )

        candidate_list = candidate_list[
            :MAX_CANDIDATES_PER_REQUIREMENT
        ]

        if not candidate_list:
            continue

        best = candidate_list[0]

        best_score = best[0]

        if len(candidate_list) > 1:

            second_score = (
                candidate_list[1][0]
            )

        else:

            second_score = 0.0

        margin = (
            best_score
            -
            second_score
        )

        # -------------------------------------------------
        # AMBIGUOUS MATCH
        # -------------------------------------------------

        if (
            len(candidate_list) > 1
            and
            margin < MIN_BEST_MARGIN
        ):

            continue

        (
            final_score,
            similarity_score,
            position_score,
            old_local_position,
            new_local_position
        ) = best

        candidates.append(
            (
                final_score,
                similarity_score,
                old_local_position,
                new_local_position
            )
        )

    # =====================================================
    # STRONGEST FIRST
    # =====================================================

    candidates.sort(
        reverse=True,
        key=lambda item: item[0]
    )

    matched_count = 0
    modified_count = 0

    matched_old_local = set()
    matched_new_local = set()

    # =====================================================
    # ONE-TO-ONE MATCH
    # =====================================================

    for (
        final_score,
        similarity_score,
        old_local_position,
        new_local_position
    ) in candidates:

        if old_local_position in matched_old_local:
            continue

        if new_local_position in matched_new_local:
            continue

        old_position, old_requirement = (
            unmatched_old[
                old_local_position
            ]
        )

        new_position, new_requirement = (
            unmatched_new[
                new_local_position
            ]
        )

        if (
            similarity_score
            <
            SEMANTIC_MODIFIED_THRESHOLD
        ):
            continue

        matched_old_local.add(
            old_local_position
        )

        matched_new_local.add(
            new_local_position
        )

        old_used.add(
            old_position
        )

        new_used.add(
            new_position
        )

        matched_count += 1

        old_content = (
            normalized_requirement_content(
                old_requirement
            )
        )

        new_content = (
            normalized_requirement_content(
                new_requirement
            )
        )

        if old_content != new_content:

            modified.append(
                make_modified(
                    old_requirement,
                    new_requirement,
                    similarity_score
                )
            )

            modified_count += 1

    return (
        matched_count,
        modified_count
    )


# =========================================================
# MAIN FUNCTION
# =========================================================

def detect_mutations(
    old_requirements: List[Any],
    new_requirements: List[Any]
) -> Dict[str, List[Dict[str, Any]]]:

    print(
        "[Mutation] Starting requirement comparison..."
    )

    # =====================================================
    # SAFE INPUT
    # =====================================================

    if old_requirements is None:
        old_requirements = []

    if new_requirements is None:
        new_requirements = []

    added = []

    deleted = []

    modified = []

    old_used = set()

    new_used = set()

    # =====================================================
    # EMPTY OLD DOCUMENT
    # =====================================================

    if not old_requirements:

        for requirement in new_requirements:

            added.append(
                make_added(
                    requirement
                )
            )

        print(
            "[Mutation] Added:"
            f" {len(added)}"
        )

        print(
            "[Mutation] Deleted: 0"
        )

        print(
            "[Mutation] Modified: 0"
        )

        return {
            "added": added,
            "deleted": deleted,
            "modified": modified
        }

    # =====================================================
    # EMPTY NEW DOCUMENT
    # =====================================================

    if not new_requirements:

        for requirement in old_requirements:

            deleted.append(
                make_deleted(
                    requirement
                )
            )

        print(
            "[Mutation] Added: 0"
        )

        print(
            "[Mutation] Deleted:"
            f" {len(deleted)}"
        )

        print(
            "[Mutation] Modified: 0"
        )

        return {
            "added": added,
            "deleted": deleted,
            "modified": modified
        }

    # =====================================================
    # STEP 1
    # EXACT CONTENT
    # =====================================================

    exact_count = match_exact_text(
        old_requirements,
        new_requirements,
        old_used,
        new_used
    )

    print(
        "[Mutation] Exact unchanged:"
        f" {exact_count}"
    )

    # =====================================================
    # STEP 2
    # LOGICAL REQ ID
    # =====================================================

    (
        common_id_count,
        logical_id_modified_count
    ) = match_same_logical_id(
        old_requirements,
        new_requirements,
        old_used,
        new_used,
        modified
    )

    print(
        "[Mutation] Logical-ID matches:"
        f" {common_id_count}"
    )

    print(
        "[Mutation] Logical-ID modified:"
        f" {logical_id_modified_count}"
    )

    # =====================================================
    # STEP 3
    # SEMANTIC MATCHING
    # =====================================================

    (
        semantic_match_count,
        semantic_modified_count
    ) = semantic_match(
        old_requirements,
        new_requirements,
        old_used,
        new_used,
        modified
    )

    print(
        "[Mutation] Semantic matches:"
        f" {semantic_match_count}"
    )

    print(
        "[Mutation] Semantic modified:"
        f" {semantic_modified_count}"
    )

    # =====================================================
    # STEP 4
    # REMAINING OLD = DELETED
    # =====================================================

    for position, requirement in enumerate(
        old_requirements
    ):

        if position in old_used:
            continue

        deleted.append(
            make_deleted(
                requirement
            )
        )

    # =====================================================
    # STEP 5
    # REMAINING NEW = ADDED
    # =====================================================

    for position, requirement in enumerate(
        new_requirements
    ):

        if position in new_used:
            continue

        added.append(
            make_added(
                requirement
            )
        )

    # =====================================================
    # SORT RESULTS
    # =====================================================

    added.sort(
        key=lambda item: str(
            item.get(
                "logical_id",
                item.get(
                    "id",
                    ""
                )
            )
        )
    )

    deleted.sort(
        key=lambda item: str(
            item.get(
                "logical_id",
                item.get(
                    "id",
                    ""
                )
            )
        )
    )

    modified.sort(
        key=lambda item: str(
            item.get(
                "logical_id",
                item.get(
                    "id",
                    ""
                )
            )
        )
    )

    # =====================================================
    # FINAL LOG
    # =====================================================

    print(
        "[Mutation] --------------------------------"
    )

    print(
        "[Mutation] Old requirements:"
        f" {len(old_requirements)}"
    )

    print(
        "[Mutation] New requirements:"
        f" {len(new_requirements)}"
    )

    print(
        "[Mutation] Added:"
        f" {len(added)}"
    )

    print(
        "[Mutation] Deleted:"
        f" {len(deleted)}"
    )

    print(
        "[Mutation] Modified:"
        f" {len(modified)}"
    )

    print(
        "[Mutation] --------------------------------"
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "added": added,
        "deleted": deleted,
        "modified": modified
    }


# =========================================================
# END
# =========================================================