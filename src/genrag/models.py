"""Validated, immutable records with explicit retrieval depth and candidate universe."""

from __future__ import annotations

from dataclasses import dataclass

from genrag.errors import ValidationError


def positive_integer(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{label} must be a positive integer")


def identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValidationError(f"{label} must be a nonempty, whitespace-trimmed string")
    return value


@dataclass(frozen=True, slots=True)
class Prediction:
    """One query's ordered candidates; unknown IDs retain their rank as None.

    Duplicates also retain their raw positions. Fusion removes duplicate votes,
    but scoring must not silently improve a model's original ranking.
    """

    query_id: str
    gold_evidence_id: str
    candidates: tuple[str | None, ...]
    depth: int = 10

    def __post_init__(self) -> None:
        identifier(self.query_id, "query_id")
        identifier(self.gold_evidence_id, "gold_evidence_id")
        positive_integer(self.depth, "depth")
        if not isinstance(self.candidates, tuple):
            raise ValidationError("candidates must be a tuple")
        if len(self.candidates) > self.depth:
            raise ValidationError("Candidate count exceeds declared retrieval depth")
        for candidate in self.candidates:
            if candidate is not None:
                identifier(candidate, "candidate ID")

    @property
    def gold_rank(self) -> int | None:
        try:
            return self.candidates.index(self.gold_evidence_id) + 1
        except ValueError:
            return None


@dataclass(frozen=True, slots=True)
class Universe:
    """The complete eligible candidate set, not just the IDs returned by a run."""

    document_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.document_ids, frozenset) or not self.document_ids:
            raise ValidationError("Universe must be a nonempty frozenset")
        for document_id in self.document_ids:
            identifier(document_id, "universe ID")

    def validate(self, prediction: Prediction) -> None:
        if prediction.gold_evidence_id not in self.document_ids:
            raise ValidationError(f"Gold ID outside the universe for query {prediction.query_id}")
        if any(c is not None and c not in self.document_ids for c in prediction.candidates):
            raise ValidationError(f"Candidate outside the universe for query {prediction.query_id}")
