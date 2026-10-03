import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


if not NEO4J_URI:
    raise RuntimeError("NEO4J_URI is not configured.")

if not NEO4J_USERNAME:
    raise RuntimeError("NEO4J_USERNAME is not configured.")

if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD is not configured.")


# =========================================================
# NEO4J DRIVER
# =========================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USERNAME,
        NEO4J_PASSWORD
    )
)


# =========================================================
# DATABASE CONSTRAINTS
# =========================================================

def create_constraints():

    with driver.session() as session:

        session.run("""
            CREATE CONSTRAINT document_version_name_unique
            IF NOT EXISTS
            FOR (d:DocumentVersion)
            REQUIRE d.name IS UNIQUE
        """)

        session.run("""
            CREATE CONSTRAINT knowledge_node_id_document_unique
            IF NOT EXISTS
            FOR (n:KnowledgeNode)
            REQUIRE (n.id, n.document) IS UNIQUE
        """)


create_constraints()


# =========================================================
# CONNECTION TEST
# =========================================================

def test_connection():

    with driver.session() as session:

        result = session.run(
            "RETURN 'NEO4J_OK' AS message"
        )

        return result.single()["message"]


# =========================================================
# STORE GRAPH
# =========================================================

def store_graph(
    graph_data,
    document_name,
    comparison_data=None,
    old_document_name=None
):

    """
    Store knowledge graph and comparison information.

    Stores:

    DocumentVersion
    KnowledgeNode
    CONTAINS
    RELATED_TO
    AFFECTS
    VERSION_OF
    ADDED
    DELETED
    MODIFIED
    TRACEABLE_TO
    """

    with driver.session() as session:

        # =====================================================
        # 1. CURRENT DOCUMENT VERSION
        # =====================================================

        session.run(
            """
            MERGE (d:DocumentVersion {
                name: $document_name
            })
            """,
            document_name=document_name
        )


        # =====================================================
        # 2. OLD DOCUMENT VERSION
        # =====================================================

        if old_document_name:

            session.run(
                """
                MERGE (old:DocumentVersion {
                    name: $old_document_name
                })
                """,
                old_document_name=old_document_name
            )


            # =================================================
            # V1 -> V2
            # =================================================

            session.run(
                """
                MATCH (old:DocumentVersion {
                    name: $old_document_name
                })

                MATCH (new:DocumentVersion {
                    name: $document_name
                })

                MERGE (old)-[:VERSION_OF]->(new)
                """,
                old_document_name=old_document_name,
                document_name=document_name
            )


        # =====================================================
        # 3. CREATE KNOWLEDGE NODES
        # =====================================================

        for node in graph_data.get("nodes", []):

            session.run(
                """
                MERGE (n:KnowledgeNode {
                    id: $id,
                    document: $document_name
                })

               SET
    n.name = $name,
    n.type = $type,
    n.text = $text,
    n.node_type = $node_type
                WITH n

                MATCH (d:DocumentVersion {
                    name: $document_name
                })

                MERGE (d)-[:CONTAINS]->(n)
                """,
               id=node["id"],
document_name=document_name,
name=node.get("name") or node["id"],
type=node.get("type"),
text=node.get("text"),
node_type=node.get("node_type")
            )


        # =====================================================
        # 4. CREATE GRAPH RELATIONSHIPS
        # =====================================================

        for edge in graph_data.get("edges", []):

            source = edge.get("source")
            target = edge.get("target")
            relation = edge.get("relation")
            similarity = edge.get("similarity")


            # =================================================
            # RELATED_TO
            # =================================================

            if relation == "RELATED_TO":

                session.run(
                    """
                    MATCH (a:KnowledgeNode {
                        id: $source,
                        document: $document_name
                    })

                    MATCH (b:KnowledgeNode {
                        id: $target,
                        document: $document_name
                    })

                    MERGE (a)-[r:RELATED_TO]->(b)

                    SET r.similarity = $similarity
                    """,
                    source=source,
                    target=target,
                    document_name=document_name,
                    similarity=similarity
                )


            # =================================================
            # AFFECTS
            # =================================================

            elif relation == "AFFECTS":

                session.run(
                    """
                    MATCH (a:KnowledgeNode {
                        id: $source,
                        document: $document_name
                    })

                    MATCH (b:KnowledgeNode {
                        id: $target,
                        document: $document_name
                    })

                    MERGE (a)-[:AFFECTS]->(b)
                    """,
                    source=source,
                    target=target,
                    document_name=document_name
                )


            # =================================================
            # FALLBACK RELATION
            # =================================================

            else:

                session.run(
                    """
                    MATCH (a:KnowledgeNode {
                        id: $source,
                        document: $document_name
                    })

                    MATCH (b:KnowledgeNode {
                        id: $target,
                        document: $document_name
                    })

                    MERGE (a)-[r:RELATED {
                        relation: $relation
                    }]->(b)

                    SET r.similarity = $similarity
                    """,
                    source=source,
                    target=target,
                    document_name=document_name,
                    relation=relation,
                    similarity=similarity
                )


        # =====================================================
        # 5. COMPARISON INFORMATION
        # =====================================================

        if comparison_data:

            # =================================================
            # ADDED REQUIREMENTS
            # =================================================

            for item in comparison_data.get(
                "added",
                []
            ):

                requirement_id = item.get("id")

                if not requirement_id:
                    continue


                session.run(
                    """
                    MATCH (d:DocumentVersion {
                        name: $document_name
                    })

                    MATCH (n:KnowledgeNode {
                        id: $requirement_id,
                        document: $document_name
                    })

                    MERGE (n)-[:ADDED]->(d)
                    """,
                    document_name=document_name,
                    requirement_id=requirement_id
                )


            # =================================================
            # DELETED REQUIREMENTS
            # =================================================

            for item in comparison_data.get(
                "deleted",
                []
            ):

                requirement_id = item.get("id")

                if not requirement_id:
                    continue

                if not old_document_name:
                    continue


                session.run(
                    """
                    MERGE (n:KnowledgeNode {
                        id: $requirement_id,
                        document: $old_document_name
                    })

                    SET
                        n.text = $text,
                        n.node_type = "requirement",
                        n.type = "Functional"

                    WITH n

                    MATCH (d:DocumentVersion {
                        name: $old_document_name
                    })

                    MERGE (d)-[:CONTAINS]->(n)

                    MERGE (n)-[:DELETED]->(d)
                    """,
                    requirement_id=requirement_id,
                    old_document_name=old_document_name,
                    text=item.get("text")
                )


            # =================================================
            # MODIFIED REQUIREMENTS
            # =================================================

            for item in comparison_data.get(
                "modified",
                []
            ):

                requirement_id = item.get("id")

                if not requirement_id:
                    continue

                if not old_document_name:
                    continue


                session.run(
                    """
                    MATCH (old:KnowledgeNode {
                        id: $requirement_id,
                        document: $old_document_name
                    })

                    MATCH (new:KnowledgeNode {
                        id: $requirement_id,
                        document: $document_name
                    })

                    MERGE (old)-[:MODIFIED]->(new)
                    """,
                    requirement_id=requirement_id,
                    old_document_name=old_document_name,
                    document_name=document_name
                )


            # =================================================
            # 6. TRACEABILITY
            # =================================================

            for item in comparison_data.get(
                "traceability",
                []
            ):

                requirement_id = item.get(
                    "requirement_id"
                )

                related_requirements = item.get(
                    "related_requirements",
                    []
                )

                affected_components = item.get(
                    "affected_components",
                    []
                )


                # =============================================
                # RELATED REQUIREMENTS
                # =============================================

                for related_id in related_requirements:

                    session.run(
                        """
                        MATCH (a:KnowledgeNode {
                            id: $requirement_id,
                            document: $document_name
                        })

                        MATCH (b:KnowledgeNode {
                            id: $related_id,
                            document: $document_name
                        })

                        MERGE (a)-[:TRACEABLE_TO]->(b)
                        """,
                        requirement_id=requirement_id,
                        related_id=related_id,
                        document_name=document_name
                    )


                # =============================================
                # AFFECTED COMPONENTS
                # =============================================

                for component_id in affected_components:

                    session.run(
                        """
                        MATCH (a:KnowledgeNode {
                            id: $requirement_id,
                            document: $document_name
                        })

                        MATCH (c:KnowledgeNode {
                            id: $component_id,
                            document: $document_name
                        })

                        MERGE (a)-[:AFFECTS]->(c)
                        """,
                        requirement_id=requirement_id,
                        component_id=component_id,
                        document_name=document_name
                    )


    # =========================================================
    # RESULT
    # =========================================================

    return {
        "status": "success",
        "message": (
            "Knowledge Graph and comparison stored "
            f"for {document_name}"
        )
    }