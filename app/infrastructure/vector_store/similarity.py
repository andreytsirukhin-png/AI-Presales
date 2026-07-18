def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        left: First embedding vector.
        right: Second embedding vector.

    Returns:
        Cosine similarity in the range [-1.0, 1.0], or 0.0 when either vector
        has zero magnitude.

    Raises:
        ValueError: If the vectors have different dimensions.
    """
    if len(left) != len(right):
        raise ValueError(
            f"Vector dimension mismatch: expected {len(left)}, got {len(right)}"
        )

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return dot_product / (left_norm * right_norm)
