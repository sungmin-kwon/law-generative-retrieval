"""Deterministic document aggregation and weighted reciprocal-rank fusion."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from genrag.errors import ValidationError
from genrag.models import identifier, positive_integer


@dataclass(frozen=True, slots=True)
class ChunkHit:
    document_id: str
    score: float
    chunk_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.document_id, "document ID")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise ValidationError("Chunk score must be numeric")
        if not math.isfinite(self.score):
            raise ValidationError("Chunk score must be finite")
        if not isinstance(self.chunk_id, str):
            raise ValidationError("chunk_id must be a string")


def collapse_chunks(hits: Iterable[ChunkHit], *, limit: int = 50) -> tuple[ChunkHit, ...]:
    """Keep each document's highest score, independent of chunk/section type.

    Equal scores are resolved by chunk ID, then documents by document ID. Adding
    a lower-scoring chunk cannot reduce that document's selected score.
    """
    positive_integer(limit, "limit")
    best: dict[str, ChunkHit] = {}
    for hit in hits:
        old = best.get(hit.document_id)
        if old is None or (-hit.score, hit.chunk_id) < (-old.score, old.chunk_id):
            best[hit.document_id] = hit
    return tuple(sorted(best.values(), key=lambda h: (-h.score, h.document_id))[:limit])


def reciprocal_rank_fusion(
    channels: Mapping[str, Sequence[str | None]],
    *,
    weights: Mapping[str, float] | None = None,
    constant: int = 60,
    limit: int = 10,
) -> tuple[str, ...]:
    """Fuse document ranks, with one vote per document per channel.

    Unknown positions consume a rank without receiving a vote. Tie-breaking is
    deterministic: total score, best input rank, then document identifier.
    """
    positive_integer(constant, "RRF constant")
    positive_integer(limit, "limit")
    if not channels:
        raise ValidationError("At least one ranking channel is required")
    actual = {name: 1.0 for name in channels} if weights is None else dict(weights)
    if set(actual) != set(channels):
        raise ValidationError("Weights must cover exactly the provided channels")
    for weight in actual.values():
        if (
            isinstance(weight, bool)
            or not isinstance(weight, (int, float))
            or not math.isfinite(weight)
            or weight < 0
        ):
            raise ValidationError("RRF weights must be finite nonnegative numbers")
    if not any(actual.values()):
        raise ValidationError("At least one RRF weight must be positive")
    scores: dict[str, float] = defaultdict(float)
    best_rank: dict[str, int] = {}
    for name, candidates in channels.items():
        if actual[name] == 0:
            continue
        seen: set[str] = set()
        for rank, candidate in enumerate(candidates, 1):
            if candidate is None:
                continue
            identifier(candidate, "candidate ID")
            if candidate in seen:
                continue
            seen.add(candidate)
            scores[candidate] += actual[name] / (constant + rank)
            best_rank[candidate] = min(best_rank.get(candidate, rank), rank)
    return tuple(sorted(scores, key=lambda d: (-scores[d], best_rank[d], d))[:limit])
