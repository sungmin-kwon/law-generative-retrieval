"""Normalize saved model predictions and component captures without calling providers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from genrag.errors import ValidationError
from genrag.io import iter_jsonl, read_json
from genrag.models import Prediction, Universe, identifier, positive_integer


def _candidate(value: Any, position: int) -> str | None:
    if value is None or isinstance(value, str):
        return value
    if not isinstance(value, dict):
        raise ValidationError("Candidate must be an ID, null or candidate object")
    if "rank" in value and (type(value["rank"]) is not int or value["rank"] != position):
        raise ValidationError("Candidate ranks must match their saved positions")
    if "evidence_id" in value:
        return value["evidence_id"]
    if "text" in value:
        return value["text"]
    raise ValidationError("Candidate object requires evidence_id or text")


def load_predictions(path: Path, *, depth: int = 10) -> tuple[Prediction, ...]:
    """Read a single depth from candidates[] or documents[] JSONL.

    A capture may contain both depth 5 and depth 10. These are separate rankings,
    never silently pooled. Empty rankings remain in the evaluation denominator.
    """
    positive_integer(depth, "depth")
    result: list[Prediction] = []
    seen: set[str] = set()
    for row in iter_jsonl(path):
        requested = row.get("requested_depth", row.get("depth", depth))
        positive_integer(requested, "saved retrieval depth")
        if requested != depth:
            continue
        query_id = identifier(row.get("query_id"), "query_id")
        if query_id in seen:
            raise ValidationError(f"Duplicate query ID at depth {depth}: {query_id}")
        seen.add(query_id)
        gold = identifier(row.get("gold_evidence_id", row.get("evidence_id")), "gold ID")
        if "candidates" in row and "documents" in row:
            raise ValidationError("Ambiguous row: both candidates and documents are present")
        values = row.get("candidates", row.get("documents"))
        if not isinstance(values, list):
            raise ValidationError("Prediction requires a candidates or documents list")
        prediction = Prediction(
            query_id, gold, tuple(_candidate(v, i) for i, v in enumerate(values, 1)), depth
        )
        if "gold_rank" in row:
            rank = row["gold_rank"]
            if rank is not None and (type(rank) is not int or rank <= 0):
                raise ValidationError("Saved gold rank must be null or a positive integer")
            if rank != prediction.gold_rank:
                raise ValidationError(f"Saved gold rank disagrees with candidates: {query_id}")
        result.append(prediction)
    if not result:
        raise ValidationError(f"No prediction rows at requested depth {depth}")
    return tuple(result)


def load_universe(path: Path) -> Universe:
    value = read_json(path)
    if not isinstance(value, dict) or not isinstance(value.get("document_ids"), list):
        raise ValidationError("Universe JSON requires a document_ids list")
    ids = value["document_ids"]
    for item in ids:
        identifier(item, "universe ID")
    if len(ids) != len(set(ids)):
        raise ValidationError("Duplicate document ID in universe")
    return Universe(frozenset(ids))


def load_cohort(path: Path) -> frozenset[str]:
    value = read_json(path)
    if not isinstance(value, dict) or not isinstance(value.get("query_ids"), list):
        raise ValidationError("Cohort JSON requires a query_ids list")
    ids = value["query_ids"]
    for item in ids:
        identifier(item, "cohort query ID")
    if not ids or len(ids) != len(set(ids)):
        raise ValidationError("Cohort must be nonempty with unique query IDs")
    return frozenset(ids)
