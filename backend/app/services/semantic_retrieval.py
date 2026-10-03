from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# =========================================================
# SEMANTIC MODEL
# =========================================================

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# Minimum similarity required
SIMILARITY_THRESHOLD = 0.45


# =========================================================
# FIND SEMANTICALLY SIMILAR REQUIREMENTS
# =========================================================

def find_similar_requirements(
    requirements,
    top_k=5
):
    """
    Find semantically similar requirements.

    Uses SentenceTransformer embeddings instead
    of simple word/string matching.
    """

    if not requirements:
        return []

    # -----------------------------------------------------
    # Requirement texts
    # -----------------------------------------------------

    texts = [
        req.text
        for req in requirements
    ]

    # -----------------------------------------------------
    # Generate embeddings
    # -----------------------------------------------------

    embeddings = model.encode(
        texts
    )

    # -----------------------------------------------------
    # Calculate similarity
    # -----------------------------------------------------

    similarity_matrix = cosine_similarity(
        embeddings
    )

    results = []

    # -----------------------------------------------------
    # Compare every requirement
    # -----------------------------------------------------

    for i in range(
        len(requirements)
    ):

        matches = []

        for j in range(
            len(requirements)
        ):

            # Don't compare requirement
            # with itself
            if i == j:
                continue

            similarity = float(
                similarity_matrix[i][j]
            )

            if similarity >= SIMILARITY_THRESHOLD:

                matches.append({
                    "requirement_id": requirements[j].id,
                    "similarity": round(
                        similarity,
                        3
                    )
                })

        # Highest similarity first
        matches.sort(
            key=lambda x: x["similarity"],
            reverse=True
        )

        # Keep only top matches
        matches = matches[:top_k]

        results.append({
            "requirement_id": requirements[i].id,
            "similar_requirements": matches
        })

    return results