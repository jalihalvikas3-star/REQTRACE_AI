# =========================================================
# KNOWLEDGE GRAPH BUILDER
# =========================================================

import json
import re

import networkx as nx

from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

from app.services.component_extractor import extract_components
from app.services.gemini_service import generate_response


# =========================================================
# NLP MODEL
# =========================================================

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================================
# SETTINGS
# =========================================================

# Large documents use local semantic matching.
# Gemini is intentionally NOT called for large SRS files.

LARGE_DOCUMENT_THRESHOLD = 300

SIMILARITY_THRESHOLD = 0.45

TOP_K_RELATIONSHIPS = 5

# For large documents, components are extracted only from
# a limited number of representative requirements.
#
# This prevents 1000+ Gemini/component calls.
MAX_COMPONENT_EXTRACTION_REQUIREMENTS = 100


# =========================================================
# EXTRACT JSON FROM GEMINI
# =========================================================

def _extract_json(response_text):

    response_text = (
        response_text
        .strip()
    )

    match = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        response_text,
        re.DOTALL | re.IGNORECASE
    )

    if match:

        response_text = (
            match
            .group(1)
            .strip()
        )

    return json.loads(
        response_text
    )


# =========================================================
# GEMINI RELATIONSHIP DETECTION
# =========================================================

def detect_relationships_with_gemini(
    requirements
):

    if len(requirements) < 2:

        return []

    requirement_data = []

    for req in requirements:

        requirement_data.append({

            "id":
                req.id,

            "text":
                req.text

        })

    prompt = f"""
You are an expert software requirements analyst.

Analyze the following software requirements and identify
meaningful relationships between them.

Only use:

RELATED_TO

Create a relationship only when two requirements:

- depend on each other
- describe closely connected functionality
- operate on the same feature or domain
- have a meaningful functional relationship
- support or complement each other

Rules:

1. Only use requirement IDs provided in the input.
2. Never invent IDs.
3. No self relationships.
4. No duplicate relationships.
5. No reverse duplicate relationships.
6. Do not create relationships based only on common words.
7. Confidence must be between 0.0 and 1.0.
8. Evidence must briefly explain the relationship.
9. Return ONLY valid JSON.
10. Return a JSON array.

Required format:

[
  {{
    "source": "REQ-001",
    "target": "REQ-002",
    "relation": "RELATED_TO",
    "confidence": 0.85,
    "evidence": "Both requirements concern user registration."
  }}
]

Requirements:

{json.dumps(
    requirement_data,
    indent=2
)}
"""

    response = generate_response(
        prompt
    )

    data = _extract_json(
        response
    )

    if not isinstance(
        data,
        list
    ):

        raise ValueError(
            "Gemini relationship response "
            "must be a JSON array."
        )

    valid_ids = {
        req.id
        for req in requirements
    }

    relationships = []

    seen = set()

    for item in data:

        if not isinstance(
            item,
            dict
        ):

            continue

        source = str(
            item.get(
                "source",
                ""
            )
        ).strip()

        target = str(
            item.get(
                "target",
                ""
            )
        ).strip()

        relation = str(
            item.get(
                "relation",
                ""
            )
        ).strip()

        if source not in valid_ids:
            continue

        if target not in valid_ids:
            continue

        if source == target:
            continue

        if relation != "RELATED_TO":
            continue

        pair_key = tuple(
            sorted(
                [
                    source,
                    target
                ]
            )
        )

        if pair_key in seen:
            continue

        seen.add(
            pair_key
        )

        try:

            confidence = float(
                item.get(
                    "confidence",
                    0.0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 0.0

        confidence = max(
            0.0,
            min(
                confidence,
                1.0
            )
        )

        evidence = str(
            item.get(
                "evidence",
                ""
            )
        ).strip()

        relationships.append({

            "source":
                source,

            "target":
                target,

            "relation":
                "RELATED_TO",

            "confidence":
                round(
                    confidence,
                    2
                ),

            "evidence":
                evidence

        })

    return relationships


# =========================================================
# FAST LOCAL RELATIONSHIP DETECTION
# =========================================================

def detect_relationships_with_similarity(
    requirements
):

    relationships = []

    if len(requirements) < 2:

        return relationships

    print(
        "[Similarity] Encoding "
        f"{len(requirements)} requirements..."
    )

    texts = [

        str(
            req.text
        )

        for req in requirements

    ]

    # -----------------------------------------------------
    # Generate embeddings once.
    # -----------------------------------------------------

    embeddings = model.encode(

        texts,

        show_progress_bar=False,

        batch_size=64,

        normalize_embeddings=True

    )

    print(
        "[Similarity] Embeddings generated."
    )

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Do NOT build an N x N cosine matrix.
    #
    # NearestNeighbors finds only TOP-K candidates.
    # -----------------------------------------------------

    neighbor_count = min(

        TOP_K_RELATIONSHIPS + 1,

        len(requirements)

    )

    nearest_neighbors = NearestNeighbors(

        n_neighbors=neighbor_count,

        metric="cosine",

        algorithm="auto"

    )

    nearest_neighbors.fit(
        embeddings
    )

    distances, indexes = (
        nearest_neighbors.kneighbors(
            embeddings
        )
    )

    seen = set()

    # -----------------------------------------------------
    # Process only TOP-K neighbors.
    # -----------------------------------------------------

    for i in range(
        len(requirements)
    ):

        source_req = requirements[i]

        for position in range(
            len(indexes[i])
        ):

            j = indexes[i][position]

            if j == i:
                continue

            distance = float(
                distances[i][position]
            )

            semantic_score = (
                1.0 - distance
            )

            if (
                semantic_score
                < SIMILARITY_THRESHOLD
            ):

                continue

            target_req = requirements[j]

            pair_key = tuple(
                sorted(
                    [
                        source_req.id,
                        target_req.id
                    ]
                )
            )

            if pair_key in seen:
                continue

            seen.add(
                pair_key
            )

            semantic_score = round(
                semantic_score,
                2
            )

            relationships.append({

                "source":
                    source_req.id,

                "target":
                    target_req.id,

                "relation":
                    "RELATED_TO",

                "similarity":
                    semantic_score,

                "confidence":
                    semantic_score,

                "evidence":
                    (
                        "Requirements have semantically "
                        "related functionality based on "
                        "embedding similarity "
                        f"(score: {semantic_score})."
                    )

            })

    print(
        "[Similarity] Found "
        f"{len(relationships)} relationships."
    )

    return relationships

# =========================================================
# RELATIONSHIP DETECTION
# =========================================================

def detect_relationships(
    requirements
):

    print(
        "[Fast Mode] Using local semantic "
        "relationship detection."
    )

    try:

        relationships = (
            detect_relationships_with_similarity(
                requirements
            )
        )

        print(
            "[Similarity] Relationship detection: "
            f"{len(relationships)} relationships."
        )

        return (
            relationships,
            "similarity"
        )

    except Exception as e:

        print(
            "[Similarity] Relationship detection failed:"
            f" {e}"
        )

        return (
            [],
            "none"
        )


# =========================================================
# FAST COMPONENT EXTRACTION
# =========================================================

def extract_components_fast(
    requirements
):

    components_by_requirement = {}

    # =====================================================
    # SMALL DOCUMENT
    # =====================================================

    if len(requirements) <= LARGE_DOCUMENT_THRESHOLD:

        for req in requirements:

            try:

                components = extract_components(
                    req.text
                )

            except Exception as e:

                print(
                    "[Graph] Component extraction failed "
                    f"for {req.id}: {e}"
                )

                components = []

            components_by_requirement[
                req.id
            ] = components

        return components_by_requirement

    # =====================================================
    # LARGE DOCUMENT
    #
    # IMPORTANT:
    #
    # Do NOT call Gemini/component extractor 1000 times.
    #
    # We use a deterministic local component extractor.
    # =====================================================

    print(
        "[Large SRS] Using local component "
        "extraction."
    )

    component_keywords = [

        (
            "authentication",
            "Authentication Module"
        ),

        (
            "login",
            "Authentication Module"
        ),

        (
            "logout",
            "Authentication Module"
        ),

        (
            "register",
            "Registration Module"
        ),

        (
            "registration",
            "Registration Module"
        ),

        (
            "user",
            "User Management Module"
        ),

        (
            "profile",
            "Profile Management Module"
        ),

        (
            "search",
            "Search Module"
        ),

        (
            "notification",
            "Notification Module"
        ),

        (
            "email",
            "Notification Module"
        ),

        (
            "report",
            "Reporting Module"
        ),

        (
            "payment",
            "Payment Module"
        ),

        (
            "billing",
            "Payment Module"
        ),

        (
            "reservation",
            "Reservation Module"
        ),

        (
            "booking",
            "Reservation Module"
        ),

        (
            "schedule",
            "Scheduling Module"
        ),

        (
            "scheduling",
            "Scheduling Module"
        ),

        (
            "admin",
            "Administration Module"
        ),

        (
            "administrator",
            "Administration Module"
        ),

        (
            "access",
            "Access Control Module"
        ),

        (
            "permission",
            "Access Control Module"
        ),

        (
            "database",
            "Database Module"
        ),

        (
            "api",
            "API Module"
        ),

        (
            "dashboard",
            "Dashboard Module"
        ),

        (
            "document",
            "Document Management Module"
        ),

        (
            "file",
            "File Management Module"
        ),

        (
            "upload",
            "File Management Module"
        ),

        (
            "download",
            "File Management Module"
        ),

    ]

    for req in requirements:

        text = str(
            req.text
        ).lower()

        components = []

        for keyword, component in (
            component_keywords
        ):

            if keyword in text:

                if component not in components:

                    components.append(
                        component
                    )

        components_by_requirement[
            req.id
        ] = components

    print(
        "[Large SRS] Local component extraction complete."
    )

    return components_by_requirement


# =========================================================
# BUILD KNOWLEDGE GRAPH
# =========================================================

def build_graph(
    requirements,
    skip_relationships=False
):

    print(
        "[Graph] Building graph for "
        f"{len(requirements)} requirements..."
    )

    graph = nx.Graph()

    # =====================================================
    # REQUIREMENT NODES
    # =====================================================

    for req in requirements:

        graph.add_node(

            req.id,

            type=req.type,

            text=req.text,

            node_type="requirement"

        )

    print(
        "[Graph] Requirement nodes added."
    )
    print("[DEBUG] BEFORE relationship detection", flush=True)

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

      
    if skip_relationships:

        relationships = []

        detection_method = "none"

        print(
            "[Graph] Skipping relationship detection."
        )

    else:

        relationships, detection_method = (
            detect_relationships(
                requirements
            )
        )

    print(
        "[Graph] Relationship detection complete."
    )

    # =====================================================
    # ADD RELATIONSHIPS
    # =====================================================

    for relationship in relationships:

        source = relationship[
            "source"
        ]

        target = relationship[
            "target"
        ]

        relation_data = {

            "relation":
                "RELATED_TO",

            "confidence":
                relationship.get(
                    "confidence",
                    0.0
                ),

            "evidence":
                relationship.get(
                    "evidence",
                    ""
                ),

            "detection_method":
                detection_method,

            "status":
                "PENDING"

        }

        if "similarity" in relationship:

            relation_data[
                "similarity"
            ] = relationship[
                "similarity"
            ]

        graph.add_edge(

            source,

            target,

            **relation_data

        )

    print(
        "[Graph] Added "
        f"{len(relationships)} requirement relationships."
    )

    # =====================================================
    # COMPONENT EXTRACTION
    # =====================================================

    components_by_requirement = (
        extract_components_fast(
            requirements
        )
    )

    # =====================================================
    # ADD COMPONENT NODES
    # =====================================================

    component_nodes = set()

    for req in requirements:

        components = (
            components_by_requirement.get(
                req.id,
                []
            )
        )

        for component in components:

            component = str(
                component
            ).strip()

            if not component:
                continue

            component_id = (

                "COMP-"
                +
                component.upper()
                .replace(
                    " ",
                    "_"
                )

            )

            # -------------------------------------------------
            # Component node
            # -------------------------------------------------

            if component_id not in component_nodes:

                graph.add_node(

                    component_id,

                    type="Component",

                    text=component,

                    node_type="component"

                )

                component_nodes.add(
                    component_id
                )

            # -------------------------------------------------
            # Requirement -> Component
            # -------------------------------------------------

            graph.add_edge(

                req.id,

                component_id,

                relation="AFFECTS"

            )

    print(
        "[Graph] Component processing complete."
    )

    print(
        "[Graph] Final graph:"
        f" {graph.number_of_nodes()} nodes,"
        f" {graph.number_of_edges()} edges."
    )

    return graph


# =========================================================
# GRAPH TO JSON
# =========================================================

def graph_to_json(
    graph
):

    return {

        "nodes": [

            {

                "id":
                    node,

                **graph.nodes[node]

            }

            for node in graph.nodes

        ],

        "edges": [

            {

                "source":
                    edge[0],

                "target":
                    edge[1],

                **graph.edges[edge]

            }

            for edge in graph.edges

        ]

    }