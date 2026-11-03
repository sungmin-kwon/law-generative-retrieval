"""Provider-independent embedding validation; no network clients are constructed."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from genrag.errors import ValidationError
from genrag.models import identifier, positive_integer


@dataclass(frozen=True, slots=True)
class EmbeddingSpec:
    model: str
    dimensions: int

    def __post_init__(self) -> None:
        identifier(self.model, "embedding model")
        positive_integer(self.dimensions, "embedding dimensions")


class QueryEmbedder(Protocol):
    """An injected backend; callers own authentication, billing and retries."""

    def embed_query(self, text: str) -> Sequence[float]: ...


def validate_embedding(vector: Sequence[float], spec: EmbeddingSpec) -> tuple[float, ...]:
    """Check dimensional/numeric validity, not model or vector-space equivalence."""
    if len(vector) != spec.dimensions:
        raise ValidationError("Embedding dimensions differ from the explicit specification")
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in vector
    ):
        raise ValidationError("Embedding values must be finite numbers")
    if not any(vector):
        raise ValidationError("Embedding vector must be nonzero")
    return tuple(float(v) for v in vector)
