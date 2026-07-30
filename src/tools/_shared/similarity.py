from __future__ import annotations

import math
from collections.abc import Collection, Sequence


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Return cosine similarity for two equal-length vectors."""
    if not left and not right:
        return 0.0
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimensions")
    if not left:
        return 0.0

    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def jaccard_similarity(
    left: Collection[str],
    right: Collection[str],
) -> float:
    """Return intersection-over-union for two topic collections."""
    left_set = set(left)
    right_set = set(right)
    union = left_set | right_set
    if not union:
        return 0.0
    return len(left_set & right_set) / len(union)

