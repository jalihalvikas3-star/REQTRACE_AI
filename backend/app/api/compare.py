from typing import Dict, List

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.storage.file_manager import save_uploaded_file
from app.parsers.pdf_parser import extract_pdf_text
from app.services.requirement_extractor import extract_requirements
from app.services.mutation_detector import detect_mutations
from app.services.relationship_review import (
    review_relationships,
    update_relationship_status,
    get_pending_relationships,
    get_accepted_relationships,
    get_rejected_relationships,
)
from app.graph.graph_builder import build_graph, graph_to_json
from app.services.neo4j_service import store_graph


router = APIRouter()


# =========================================================
# RELATIONSHIP REVIEW STORAGE
# =========================================================

relationship_store: List[Dict] = []


# =========================================================
# REQUEST MODEL
# =========================================================

class RelationshipStatusRequest(BaseModel):

    source: str
    target: str
    status: str


class RelationshipReviewRequest(BaseModel):

    relationships: List[Dict]


# =========================================================
# PROJECT / SYSTEM IDENTIFICATION
# =========================================================

def extract_project_name(text: str):

    """
    Identify the SRS project/system from the document.

    This prevents comparing two completely different
    SRS projects such as Library and Hospital.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # Check the first part of the document because
    # the project/system name normally appears in
    # the title/front page.

    for line in lines[:30]:

        normalized = " ".join(
            line.lower().split()
        )

        # Library SRS
        if (
            "online library management system"
            in normalized
        ):
            return "online library management system"

        if (
            "library management system"
            in normalized
        ):
            return "library management system"

        # Hospital SRS
        if (
            "hospital management system"
            in normalized
        ):
            return "hospital management system"

    return None


# =========================================================
# IMPACT LEVEL
# =========================================================

def calculate_impact_level(
    related_requirements,
    affected_components
):

    related_count = len(
        related_requirements
    )

    component_count = len(
        affected_components
    )

    # -----------------------------------------------------
    # HIGH IMPACT
    # -----------------------------------------------------

    if (
        component_count >= 2
        or related_count >= 3
    ):
        return "HIGH"

    # -----------------------------------------------------
    # MEDIUM IMPACT
    # -----------------------------------------------------

    if (
        component_count >= 1
        or related_count >= 1
    ):
        return "MEDIUM"

    # -----------------------------------------------------
    # LOW IMPACT
    # -----------------------------------------------------

    return "LOW"


# =========================================================
# IMPACT REASON
# =========================================================

# =========================================================
# IMPACT REASON
# =========================================================

def generate_impact_reason(
    requirement_id,
    related_requirements,
    affected_components,
    impact_level
):

    reasons = []

    # -----------------------------------------------------
    # RELATED REQUIREMENTS
    # -----------------------------------------------------

    if related_requirements:

        count = len(related_requirements)

        if count == 1:

            reasons.append(
                f"it is connected to related requirement "
                f"{related_requirements[0]}"
            )

        else:

            reasons.append(
                f"it is connected to {count} related requirements: "
                + ", ".join(related_requirements)
            )

    # -----------------------------------------------------
    # AFFECTED COMPONENTS
    # -----------------------------------------------------

    if affected_components:

        count = len(affected_components)

        if count == 1:

            reasons.append(
                f"the change affects the "
                f"{affected_components[0]}"
            )

        else:

            reasons.append(
                f"the change affects {count} components: "
                + ", ".join(affected_components)
            )

    # -----------------------------------------------------
    # IMPACT LEVEL EXPLANATION
    # -----------------------------------------------------

    if impact_level.lower() == "high":

        reasons.append(
            "changes at this level may propagate "
            "to multiple related requirements or components"
        )

    elif impact_level.lower() == "medium":

        reasons.append(
            "the change has dependencies that may require "
            "updates to related functionality"
        )

    else:

        reasons.append(
            "the change has limited traceability dependencies"
        )

    # -----------------------------------------------------
    # FINAL EXPLANATION
    # -----------------------------------------------------

    return (
        f"{requirement_id} has "
        f"{impact_level.lower()} impact because "
        + "; ".join(reasons)
        + "."
    )

# =========================================================
# COMPARE
# =========================================================

@router.post("/compare")
async def compare_files(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...)
):

    # =====================================================
    # 1. SAVE FILES
    # =====================================================

    old_path = save_uploaded_file(
        old_file
    )

    new_path = save_uploaded_file(
        new_file
    )

    # =====================================================
    # 2. EXTRACT TEXT
    # =====================================================

    old_text = extract_pdf_text(
        old_path
    )

    new_text = extract_pdf_text(
        new_path
    )

    # =====================================================
    # 3. VALIDATE SAME SRS PROJECT
    # =====================================================

    old_project = extract_project_name(
        old_text
    )

    new_project = extract_project_name(
        new_text
    )

    # -----------------------------------------------------
    # PROJECT IDENTIFICATION FAILED
    # -----------------------------------------------------

    if old_project is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not identify the SRS project "
                "from the Old SRS document."
            )
        )

    if new_project is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not identify the SRS project "
                "from the New SRS document."
            )
        )

    # -----------------------------------------------------
    # DIFFERENT PROJECTS
    # -----------------------------------------------------

    if old_project != new_project:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    "Cannot compare different SRS projects.",

                "old_file":
                    old_file.filename,

                "new_file":
                    new_file.filename,

                "old_project":
                    old_project,

                "new_project":
                    new_project
            }
        )

    # =====================================================
    # 4. EXTRACT REQUIREMENTS
    # =====================================================

    old_requirements = extract_requirements(
        old_text
    )

    new_requirements = extract_requirements(
        new_text
    )

    # =====================================================
    # 5. COMPARE V1 AND V2
    # =====================================================

    changes = detect_mutations(
        old_requirements,
        new_requirements
    )

    # =====================================================
    # 6. BUILD V1 GRAPH
    # =====================================================

    old_graph = build_graph(
        old_requirements
    )

    old_graph_json = graph_to_json(
        old_graph
    )

    # =====================================================
    # 7. BUILD V2 GRAPH
    # =====================================================

    new_graph = build_graph(
        new_requirements
    )

    new_graph_json = graph_to_json(
        new_graph
    )

    # =====================================================
    # 8. PREPARE AI RELATIONSHIPS FOR HUMAN REVIEW
    # =====================================================

    ai_relationships = []

    for edge in new_graph_json.get(
        "edges",
        []
    ):

        if edge.get(
            "relation"
        ) != "RELATED_TO":

            continue

        ai_relationships.append({

            "source":
                edge.get(
                    "source"
                ),

            "target":
                edge.get(
                    "target"
                ),

            "relation":
                "RELATED_TO",

            "confidence":
                edge.get(
                    "confidence",
                    0.0
                ),

            "evidence":
                edge.get(
                    "evidence",
                    ""
                )

        })

    reviewed_relationships = (
        review_relationships(
            ai_relationships
        )
    )

    # -----------------------------------------------------
    # SAVE RELATIONSHIPS FOR REVIEW API
    # -----------------------------------------------------

    relationship_store.clear()

    relationship_store.extend(
        reviewed_relationships
    )

    # =====================================================
    # 9. NODE LOOKUP
    # =====================================================

    node_lookup = {

        node["id"]: node

        for node in new_graph_json.get(
            "nodes",
            []
        )

    }

from fastapi import APIRouter, UploadFile, File

from app.storage.file_manager import save_uploaded_file
from app.parsers.pdf_parser import extract_pdf_text
from app.services.requirement_extractor import extract_requirements
from app.services.mutation_detector import detect_mutations
from app.services.relationship_review import review_relationships
from app.graph.graph_builder import build_graph, graph_to_json
from app.services.neo4j_service import store_graph


router = APIRouter()


# =========================================================
# IMPACT LEVEL
# =========================================================

def calculate_impact_level(
    related_requirements,
    affected_components
):
    """
    Determine impact severity using:

    - number of related requirements
    - number of affected components
    """

    related_count = len(
        related_requirements
    )

    component_count = len(
        affected_components
    )

    # -----------------------------------------------------
    # HIGH IMPACT
    # -----------------------------------------------------

    if (
        component_count >= 2
        or related_count >= 3
    ):
        return "HIGH"

    # -----------------------------------------------------
    # MEDIUM IMPACT
    # -----------------------------------------------------

    if (
        component_count >= 1
        or related_count >= 1
    ):
        return "MEDIUM"

    # -----------------------------------------------------
    # LOW IMPACT
    # -----------------------------------------------------

    return "LOW"


# =========================================================
# IMPACT REASON
# =========================================================

def generate_impact_reason(
    requirement_id,
    related_requirements,
    affected_components,
    impact_level
):
    """
    Generate a human-readable explanation
    for the calculated impact.
    """

    reasons = []

    # -----------------------------------------------------
    # RELATED REQUIREMENTS
    # -----------------------------------------------------

    if related_requirements:

        reasons.append(
            "The requirement is related to "
            + ", ".join(
                related_requirements
            )
        )

    # -----------------------------------------------------
    # AFFECTED COMPONENTS
    # -----------------------------------------------------

    if affected_components:

        reasons.append(
            "It directly affects "
            + ", ".join(
                affected_components
            )
        )

    # -----------------------------------------------------
    # NO EVIDENCE
    # -----------------------------------------------------

    if not reasons:

        return (
            f"{requirement_id} has "
            f"{impact_level.lower()} impact "
            "based on the available "
            "traceability evidence."
        )

    return (
        f"{requirement_id} has "
        f"{impact_level.lower()} impact because "
        + "; ".join(reasons)
        + "."
    )


# =========================================================
# COMPARE
# =========================================================

@router.post("/compare")
async def compare_files(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...)
):

    # =====================================================
    # 1. SAVE FILES
    # =====================================================

    old_path = save_uploaded_file(
        old_file
    )

    new_path = save_uploaded_file(
        new_file
    )

    # =====================================================
    # 2. EXTRACT TEXT
    # =====================================================

    old_text = extract_pdf_text(
        old_path
    )

    new_text = extract_pdf_text(
        new_path
    )

    # =====================================================
    # 3. EXTRACT REQUIREMENTS
    # =====================================================

    old_requirements = extract_requirements(
        old_text
    )

    new_requirements = extract_requirements(
        new_text
    )

    # =====================================================
    # 4. COMPARE V1 AND V2
    # =====================================================

    changes = detect_mutations(
        old_requirements,
        new_requirements
    )

    # =====================================================
    # 5. BUILD V1 GRAPH
    # =====================================================

    old_graph = build_graph(
        old_requirements
    )

    old_graph_json = graph_to_json(
        old_graph
    )

    # =====================================================
    # 6. BUILD V2 GRAPH
    # =====================================================

    new_graph = build_graph(
        new_requirements
    )

    new_graph_json = graph_to_json(
        new_graph
    )

    # =====================================================
    # 7. PREPARE AI RELATIONSHIPS FOR HUMAN REVIEW
    # =====================================================

    ai_relationships = []

    for edge in new_graph_json.get(
        "edges",
        []
    ):

        if edge.get(
            "relation"
        ) != "RELATED_TO":

            continue

        ai_relationships.append({

            "source":
                edge.get(
                    "source"
                ),

            "target":
                edge.get(
                    "target"
                ),

            "relation":
                "RELATED_TO",

            "confidence":
                edge.get(
                    "confidence",
                    0.0
                ),

            "evidence":
                edge.get(
                    "evidence",
                    ""
                )

        })

    reviewed_relationships = (
        review_relationships(
            ai_relationships
        )
    )

    # =====================================================
    # 8. NODE LOOKUP
    # =====================================================

    node_lookup = {

        node["id"]: node

        for node in new_graph_json.get(
            "nodes",
            []
        )

    }

    # =====================================================
    # 9. TRACEABILITY + IMPACT
    # =====================================================

    validated_relationships = [
        relationship
        for relationship in reviewed_relationships
        if relationship.get("status") in {
            "ACCEPTED",
            "AUTO_ACCEPTED",
        }
    ]

    traceability = []

    for modified in changes.get(
        "modified",
        []
    ):

        changed_id = modified.get(
            "id"
        )

        related_requirements = []

        affected_components = []

        # -------------------------------------------------
        # FIND GRAPH RELATIONSHIPS
        # -------------------------------------------------

        for edge in new_graph_json.get(
            "edges",
            []
        ):

            source = edge.get(
                "source"
            )

            target = edge.get(
                "target"
            )

            relation = edge.get(
                "relation"
            )

            # =============================================
            # REQUIREMENT -> COMPONENT
            # =============================================

            if (
                source == changed_id
                and relation == "AFFECTS"
            ):

                target_node = node_lookup.get(
                    target
                )

                if (
                    target_node
                    and target_node.get(
                        "node_type"
                    ) == "component"
                ):

                    affected_components.append(
                        target
                    )

            # =============================================
            # COMPONENT -> REQUIREMENT
            # =============================================

            elif (
                target == changed_id
                and relation == "AFFECTS"
            ):

                source_node = node_lookup.get(
                    source
                )

                if (
                    source_node
                    and source_node.get(
                        "node_type"
                    ) == "component"
                ):

                    affected_components.append(
                        source
                    )

        # -------------------------------------------------
        # VALIDATED REQUIREMENT RELATIONSHIPS
        # -------------------------------------------------
        #
        # Only ACCEPTED and AUTO_ACCEPTED relationships
        # participate in impact analysis.
        #

        for relationship in validated_relationships:

            source = relationship.get(
                "source"
            )

            target = relationship.get(
                "target"
            )

            relation = relationship.get(
                "relation"
            )

            if relation != "RELATED_TO":
                continue

            # =============================================
            # REQUIREMENT -> REQUIREMENT
            # =============================================

            if source == changed_id:

                target_node = node_lookup.get(
                    target
                )

                if (
                    target_node
                    and target_node.get(
                        "node_type"
                    ) == "requirement"
                ):

                    related_requirements.append(
                        target
                    )

            # =============================================
            # REQUIREMENT <- REQUIREMENT
            # =============================================

            elif target == changed_id:

                source_node = node_lookup.get(
                    source
                )

                if (
                    source_node
                    and source_node.get(
                        "node_type"
                    ) == "requirement"
                ):

                    related_requirements.append(
                        source
                    )

        # -------------------------------------------------
        # REMOVE DUPLICATES
        # -------------------------------------------------

        related_requirements = list(
            dict.fromkeys(
                related_requirements
            )
        )

        affected_components = list(
            dict.fromkeys(
                affected_components
            )
        )

        # -------------------------------------------------
        # CALCULATE IMPACT
        # -------------------------------------------------

        impact_level = calculate_impact_level(
            related_requirements,
            affected_components
        )

        # -------------------------------------------------
        # GENERATE IMPACT REASON
        # -------------------------------------------------

        impact_reason = generate_impact_reason(
            changed_id,
            related_requirements,
            affected_components,
            impact_level
        )

        # -------------------------------------------------
        # SAVE TRACEABILITY
        # -------------------------------------------------

        traceability.append({

            "requirement_id":
                changed_id,

            "change_type":
                "MODIFIED",

            "related_requirements":
                related_requirements,

            "affected_components":
                affected_components,

            "impact_level":
                impact_level,

            "impact_reason":
                impact_reason

        })

    # =====================================================
    # 10. UNIQUE AFFECTED COMPONENTS
    # =====================================================

    all_affected_components = []

    for item in traceability:

        all_affected_components.extend(
            item[
                "affected_components"
            ]
        )

    all_affected_components = list(
        dict.fromkeys(
            all_affected_components
        )
    )

    # =====================================================
    # 11. OVERALL IMPACT
    # =====================================================

    impact_levels = [

        item.get(
            "impact_level"
        )

        for item in traceability

    ]

    if "HIGH" in impact_levels:

        overall_impact = "HIGH"

    elif "MEDIUM" in impact_levels:

        overall_impact = "MEDIUM"

    elif "LOW" in impact_levels:

        overall_impact = "LOW"

    else:

        overall_impact = "NONE"

    # =====================================================
    # 12. COMPARISON DATA FOR NEO4J
    # =====================================================

    comparison_data = {

        "added":
            changes.get(
                "added",
                []
            ),

        "deleted":
            changes.get(
                "deleted",
                []
            ),

        "modified":
            changes.get(
                "modified",
                []
            ),

        "relationships":
            reviewed_relationships,

        "validated_relationships":
            validated_relationships,

        "traceability":
            traceability

    }

    # =====================================================
    # 13. STORE V1
    # =====================================================

    old_neo4j_result = store_graph(

        graph_data=
            old_graph_json,

        document_name=
            old_file.filename

    )

    # =====================================================
    # 14. STORE V2
    # =====================================================

    new_neo4j_result = store_graph(

        graph_data=
            new_graph_json,

        document_name=
            new_file.filename,

        comparison_data=
            comparison_data,

        old_document_name=
            old_file.filename

    )

    # =====================================================
    # 15. RETURN RESULT
    # =====================================================

    return {

        # -------------------------------------------------
        # FILE INFORMATION
        # -------------------------------------------------

        "old_file":
            old_file.filename,

        "new_file":
            new_file.filename,

        # -------------------------------------------------
        # REQUIREMENT COUNTS
        # -------------------------------------------------

        "old_total_requirements":
            len(
                old_requirements
            ),

        "new_total_requirements":
            len(
                new_requirements
            ),

        # -------------------------------------------------
        # CHANGES
        # -------------------------------------------------

        "added":
            changes.get(
                "added",
                []
            ),

        "deleted":
            changes.get(
                "deleted",
                []
            ),

        "modified":
            changes.get(
                "modified",
                []
            ),

        # -------------------------------------------------
        # HUMAN REVIEW
        # -------------------------------------------------

        "relationships":
            reviewed_relationships,

        # -------------------------------------------------
        # TRACEABILITY
        # -------------------------------------------------

        "traceability":
            traceability,

        # -------------------------------------------------
        # IMPACT
        # -------------------------------------------------

        "impact_summary": {

            "total_changes":
                (
                    len(
                        changes.get(
                            "added",
                            []
                        )
                    )
                    +
                    len(
                        changes.get(
                            "deleted",
                            []
                        )
                    )
                    +
                    len(
                        changes.get(
                            "modified",
                            []
                        )
                    )
                ),

            "modified":
                len(
                    changes.get(
                        "modified",
                        []
                    )
                ),

            "affected_components":
                len(
                    all_affected_components
                ),

            "affected_component_ids":
                all_affected_components,

            "overall_impact":
                overall_impact

        },

        # -------------------------------------------------
        # GRAPHS
        # -------------------------------------------------

        "old_graph":
            old_graph_json,

        "graph":
            new_graph_json,

        # -------------------------------------------------
        # NEO4J
        # -------------------------------------------------

        "neo4j": {

            "old":
                old_neo4j_result,

            "new":
                new_neo4j_result

        }

    }