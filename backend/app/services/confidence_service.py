def calculate_confidence(similarity_score):
    """
    Convert semantic similarity into a confidence score.

    Input:
        similarity_score -> value between 0 and 1

    Output:
        confidence -> rounded value between 0 and 1
    """

    try:
        score = float(similarity_score)
    except (TypeError, ValueError):
        return 0.0

    # Keep score within valid range
    score = max(0.0, min(1.0, score))

    return round(score, 3)


def generate_evidence(
    similarity_score,
    source_text,
    target_text
):
    """
    Generate deterministic evidence explaining
    why two requirements are considered related.

    This does not call Gemini.
    """

    confidence = calculate_confidence(
        similarity_score
    )

    if confidence >= 0.80:
        level = "high"

    elif confidence >= 0.60:
        level = "medium"

    elif confidence >= 0.40:
        level = "low"

    else:
        level = "very low"

    return (
        f"The requirements have {level} semantic similarity "
        f"(score: {confidence:.3f}). "
        f"Source requirement: {source_text} "
        f"Target requirement: {target_text}"
    )


def build_confidence_data(
    source_id,
    target_id,
    similarity_score,
    source_text,
    target_text
):
    """
    Build a standard confidence/evidence object
    for a relationship.
    """

    confidence = calculate_confidence(
        similarity_score
    )

    evidence = generate_evidence(
        similarity_score,
        source_text,
        target_text
    )

    return {
        "source": source_id,
        "target": target_id,
        "confidence": confidence,
        "evidence": evidence
    }