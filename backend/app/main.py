from typing import Dict, List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# =========================================================
# DATABASE
# =========================================================

from app.database import Base, engine


# =========================================================
# API ROUTERS
# =========================================================

from app.api.auth import router as auth_router
from app.api.compare import router as compare_router


# =========================================================
# PARSERS
# =========================================================

from app.parsers.pdf_parser import extract_pdf_text


# =========================================================
# STORAGE
# =========================================================

from app.storage.file_manager import save_uploaded_file


# =========================================================
# SERVICES
# =========================================================

from app.services.requirement_extractor import extract_requirements

from app.services.relationship_review import (
    review_relationships,
    update_relationship_status,
    get_pending_relationships,
    get_accepted_relationships,
    get_rejected_relationships,
)


# =========================================================
# GRAPH
# =========================================================

from app.graph.graph_builder import (
    build_graph,
    graph_to_json,
)


# =========================================================
# NEO4J
# =========================================================

from app.services.neo4j_service import store_graph


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="ReqTrace AI",
    description="AI-Based Software Knowledge Graph API",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# API ROUTERS
# =========================================================

# Authentication
app.include_router(
    auth_router
)


# Document comparison
app.include_router(
    compare_router
)


# =========================================================
# RELATIONSHIP REVIEW MODELS
# =========================================================

class RelationshipReviewRequest(BaseModel):
    relationships: List[Dict]


class RelationshipStatusRequest(BaseModel):
    relationships: List[Dict]
    source: str
    target: str
    status: str


# =========================================================
# RELATIONSHIP REVIEW API
# =========================================================

@app.post(
    "/relationships/review",
    tags=["Relationship Review"],
)
def prepare_relationship_review(
    request: RelationshipReviewRequest,
):

    reviewed = review_relationships(
        request.relationships
    )

    return {
        "status": "success",
        "total_relationships": len(reviewed),
        "relationships": reviewed,
    }


# =========================================================
# UPDATE RELATIONSHIP STATUS
# =========================================================

@app.post(
    "/relationships/status",
    tags=["Relationship Review"],
)
def change_relationship_status(
    request: RelationshipStatusRequest,
):

    try:

        updated = update_relationship_status(
            relationships=request.relationships,
            source=request.source,
            target=request.target,
            status=request.status,
        )

        return {
            "status": "success",
            "relationships": updated,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# =========================================================
# PENDING RELATIONSHIPS
# =========================================================

@app.post(
    "/relationships/pending",
    tags=["Relationship Review"],
)
def pending_relationships(
    request: RelationshipReviewRequest,
):

    reviewed = review_relationships(
        request.relationships
    )

    pending = get_pending_relationships(
        reviewed
    )

    return {
        "status": "success",
        "total_pending": len(pending),
        "relationships": pending,
    }


# =========================================================
# ACCEPTED RELATIONSHIPS
# =========================================================

@app.post(
    "/relationships/accepted",
    tags=["Relationship Review"],
)
def accepted_relationships(
    request: RelationshipReviewRequest,
):

    accepted = get_accepted_relationships(
        request.relationships
    )

    return {
        "status": "success",
        "total_accepted": len(accepted),
        "relationships": accepted,
    }


# =========================================================
# REJECTED RELATIONSHIPS
# =========================================================

@app.post(
    "/relationships/rejected",
    tags=["Relationship Review"],
)
def rejected_relationships(
    request: RelationshipReviewRequest,
):

    rejected = get_rejected_relationships(
        request.relationships
    )

    return {
        "status": "success",
        "total_rejected": len(rejected),
        "relationships": rejected,
    }


# =========================================================
# HOME
# =========================================================

@app.get(
    "/",
    tags=["System"],
)
def home():

    return {
        "message":
            "AI-Based Software Knowledge Graph API is running!",
        "status": "online",
    }


# =========================================================
# UPLOAD PDF
# =========================================================

@app.post(
    "/upload",
    tags=["Document"],
)
async def upload_file(
    file: UploadFile = File(...),
):

    # -----------------------------------------------------
    # 1. VALIDATE FILE
    # -----------------------------------------------------

    if file is None or not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Error: Please upload a file.",
        )


    # -----------------------------------------------------
    # 2. PDF CHECK
    # -----------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Error: Please upload a valid PDF file.",
        )


    # -----------------------------------------------------
    # 3. SAVE FILE
    # -----------------------------------------------------

    try:

        file_path = save_uploaded_file(
            file
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error saving uploaded file: "
                f"{str(error)}"
            ),
        )


    # -----------------------------------------------------
    # 4. EXTRACT PDF TEXT
    # -----------------------------------------------------

    try:

        text = extract_pdf_text(
            file_path
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error extracting PDF text: "
                f"{str(error)}"
            ),
        )


    # -----------------------------------------------------
    # 5. EXTRACT REQUIREMENTS
    # -----------------------------------------------------

    try:

        requirements = extract_requirements(
            text
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error extracting requirements: "
                f"{str(error)}"
            ),
        )


    # -----------------------------------------------------
    # 6. BUILD KNOWLEDGE GRAPH
    # -----------------------------------------------------

    try:

        graph = build_graph(
            requirements
        )

        graph_json = graph_to_json(
            graph
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error building knowledge graph: "
                f"{str(error)}"
            ),
        )


    # -----------------------------------------------------
    # 7. STORE GRAPH IN NEO4J
    # -----------------------------------------------------

    try:

        neo4j_result = store_graph(
            graph_json,
            file.filename,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error storing graph in Neo4j: "
                f"{str(error)}"
            ),
        )


    # -----------------------------------------------------
    # 8. RETURN RESULT
    # -----------------------------------------------------

    return {

        "status": "success",

        "filename":
            file.filename,

        "total_requirements":
            len(requirements),

        "graph":
            graph_json,

        "requirements": [
            req.to_dict()
            for req in requirements
        ],

        "neo4j":
            neo4j_result,
    }