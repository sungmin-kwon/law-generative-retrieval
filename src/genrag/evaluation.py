"""Recall, truncated reciprocal rank and paired comparisons on explicit cohorts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from genrag.errors import ValidationError
from genrag.models import Prediction, Universe, positive_integer


def _table(predictions: Iterable[Prediction], universe: Universe) -> dict[str, Prediction]:
    table: dict[str, Prediction] = {}
    for prediction in predictions:
        universe.validate(prediction)
        if prediction.query_id in table:
            raise ValidationError(f"Duplicate query ID: {prediction.query_id}")
        table[prediction.query_id] = prediction
    if not table:
        raise ValidationError("Cannot evaluate an empty prediction set")
    return table


def universe_digest(universe: Universe) -> str:
    payload = json.dumps(sorted(universe.document_ids), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _select(table: dict[str, Prediction], cohort: frozenset[str] | None) -> list[Prediction]:
    if cohort is not None:
        if not cohort or not cohort <= table.keys():
            raise ValidationError("Cohort must be nonempty and completely covered by predictions")
        return [table[q] for q in sorted(cohort)]
    return list(table.values())


def evaluate(
    predictions: Iterable[Prediction],
    universe: Universe,
    *,
    cutoffs: tuple[int, ...] = (1, 5, 10),
    cohort: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Score saved positions. Misses, unknown IDs and duplicates never disappear."""
    if not cutoffs or len(set(cutoffs)) != len(cutoffs):
        raise ValidationError("Cutoffs must be nonempty and unique")
    for cutoff in cutoffs:
        positive_integer(cutoff, "cutoff")
    selected = _select(_table(predictions, universe), cohort)
    top = max(cutoffs)
    if any(p.depth < top for p in selected):
        raise ValidationError("Metric cutoff exceeds a prediction's declared retrieval depth")
    ranks = [p.gold_rank for p in selected]
    count = len(selected)
    metrics: dict[str, Any] = {
        "queries": count,
        "universe_documents": len(universe.document_ids),
        "universe_sha256": universe_digest(universe),
        "unknown_candidate_positions": sum(p.candidates.count(None) for p in selected),
        "duplicate_candidate_positions": sum(
            len([c for c in p.candidates if c is not None])
            - len({c for c in p.candidates if c is not None})
            for p in selected
        ),
        "empty_results": sum(not p.candidates for p in selected),
    }
    for cutoff in sorted(cutoffs):
        hits = sum(rank is not None and rank <= cutoff for rank in ranks)
        metrics[f"hits_at_{cutoff}"] = hits
        metrics[f"recall_at_{cutoff}"] = hits / count
    metrics[f"mrr_at_{top}"] = sum(1 / r for r in ranks if r is not None and r <= top) / count
    return metrics


def aligned(
    left: Iterable[Prediction], right: Iterable[Prediction], universe: Universe
) -> tuple[dict[str, Prediction], dict[str, Prediction]]:
    """Require full query/gold/depth parity before comparing or fusing runs."""
    a, b = _table(left, universe), _table(right, universe)
    if a.keys() != b.keys():
        raise ValidationError(
            "Prediction query coverage differs; refusing an intersection comparison"
        )
    for query_id in a:
        if a[query_id].gold_evidence_id != b[query_id].gold_evidence_id:
            raise ValidationError(f"Expected document differs for query {query_id}")
        if a[query_id].depth != b[query_id].depth:
            raise ValidationError(f"Retrieval depths differ for query {query_id}")
    return a, b


def compare(
    left: Iterable[Prediction],
    right: Iterable[Prediction],
    universe: Universe,
    *,
    cutoff: int = 10,
    cohort: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Compare exactly matched questions; union coverage is explicitly an oracle."""
    positive_integer(cutoff, "cutoff")
    a, b = aligned(left, right, universe)
    selected = _select(a, cohort)
    cutoffs = tuple(k for k in sorted({1, 5, cutoff}) if k <= cutoff)
    left_metrics = evaluate(a.values(), universe, cutoffs=cutoffs, cohort=cohort)
    right_metrics = evaluate(b.values(), universe, cutoffs=cutoffs, cohort=cohort)
    both = left_only = right_only = neither = 0
    for prediction in selected:
        lrank, rrank = prediction.gold_rank, b[prediction.query_id].gold_rank
        lhit = lrank is not None and lrank <= cutoff
        rhit = rrank is not None and rrank <= cutoff
        both += lhit and rhit
        left_only += lhit and not rhit
        right_only += rhit and not lhit
        neither += not lhit and not rhit
    return {
        "left": left_metrics,
        "right": right_metrics,
        "paired": {
            "cutoff": cutoff,
            "both_hit": both,
            "left_only_hit": left_only,
            "right_only_hit": right_only,
            "neither_hit": neither,
            "net_right_hits": right_only - left_only,
            "right_minus_left_recall": (right_only - left_only) / len(selected),
            "oracle_union_coverage": (both + left_only + right_only) / len(selected),
            "oracle_note": "Coverage across up to twice the cutoff; not achieved fused Recall@k.",
        },
    }
