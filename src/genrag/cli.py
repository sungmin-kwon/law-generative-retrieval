"""Offline command-line interface. No command imports a model or contacts an API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from genrag import __version__
from genrag.adapters import load_cohort, load_predictions, load_universe
from genrag.errors import ValidationError
from genrag.evaluation import aligned, compare, evaluate, universe_digest
from genrag.integrity import verify_manifest
from genrag.io import atomic_json, atomic_jsonl, sha256_file
from genrag.models import Prediction
from genrag.ranking import reciprocal_rank_fusion
from genrag.release import export_public


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="genrag", description="Offline generative-retrieval evaluation and rank fusion."
    )
    result.add_argument("--version", action="version", version=f"genrag {__version__}")
    commands = result.add_subparsers(dest="command", required=True)
    for name in ["score", "compare", "fuse"]:
        command = commands.add_parser(name)
        if name == "score":
            command.add_argument("predictions", type=Path)
        else:
            command.add_argument("left", type=Path)
            command.add_argument("right", type=Path)
        command.add_argument("--universe", type=Path, required=True)
        command.add_argument("--depth", type=int, default=10)
        command.add_argument("--cohort", type=Path)
        command.add_argument("--output", type=Path, required=name == "fuse")
        if name == "fuse":
            command.add_argument("--left-weight", type=float, default=1.0)
            command.add_argument("--right-weight", type=float, default=1.0)
            command.add_argument("--rrf-constant", type=int, default=60)
    commands.add_parser("doctor", help="Show portable runtime capabilities; no secret inspection")
    verify = commands.add_parser("verify", help="Verify a portable artifact manifest")
    verify.add_argument("manifest", type=Path)
    export = commands.add_parser("export-public", help="Create an allowlisted public source tree")
    export.add_argument("--source", type=Path, default=Path.cwd())
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--forbid-text", action="append", default=[])
    return result


def _protect_outputs(outputs: list[Path], inputs: list[Path]) -> None:
    resolved = [p.resolve() for p in outputs]
    if len(set(resolved)) != len(resolved) or set(resolved) & {p.resolve() for p in inputs}:
        raise ValidationError("Output would overwrite an input or another output")
    if any(p.exists() for p in outputs):
        raise ValidationError("Output already exists; choose a new path to preserve prior results")


def _emit(report: dict[str, Any], output: Path | None = None) -> None:
    if output is not None:
        atomic_json(output, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))


def _run(args: argparse.Namespace) -> None:
    if args.command == "doctor":
        _emit(
            {
                "version": __version__,
                "python": sys.version.split()[0],
                "runtime_dependencies": [],
                "network_calls": False,
                "gpu_required": False,
                "provider_credentials_inspected": False,
            }
        )
        return
    if args.command == "verify":
        _emit(verify_manifest(args.manifest))
        return
    if args.command == "export-public":
        _emit(export_public(args.source, args.output, forbidden_terms=tuple(args.forbid_text)))
        return
    universe = load_universe(args.universe)
    cohort = load_cohort(args.cohort) if args.cohort else None
    inputs = [args.universe] + ([args.cohort] if args.cohort else [])
    cutoffs = tuple(k for k in sorted({1, 5, args.depth}) if k <= args.depth)
    if args.command == "score":
        inputs.append(args.predictions)
        predictions = load_predictions(args.predictions, depth=args.depth)
        report = {
            "schema_version": "genrag.evaluation.v1",
            "metrics": evaluate(predictions, universe, cutoffs=cutoffs, cohort=cohort),
        }
    else:
        inputs.extend([args.left, args.right])
        left = load_predictions(args.left, depth=args.depth)
        right = load_predictions(args.right, depth=args.depth)
        if args.command == "compare":
            report = {
                "schema_version": "genrag.comparison.v1",
                **compare(left, right, universe, cutoff=args.depth, cohort=cohort),
            }
        else:
            a, b = aligned(left, right, universe)
            if cohort is not None and (not cohort or not cohort <= a.keys()):
                raise ValidationError("Cohort is not completely covered")
            fused = []
            for query_id in sorted(cohort if cohort is not None else a):
                candidates = reciprocal_rank_fusion(
                    {"left": a[query_id].candidates, "right": b[query_id].candidates},
                    weights={"left": args.left_weight, "right": args.right_weight},
                    constant=args.rrf_constant,
                    limit=args.depth,
                )
                fused.append(
                    Prediction(query_id, a[query_id].gold_evidence_id, candidates, args.depth)
                )
            sidecar = args.output.with_suffix(args.output.suffix + ".manifest.json")
            _protect_outputs([args.output, sidecar], inputs)
            atomic_jsonl(
                args.output,
                (
                    {
                        "query_id": p.query_id,
                        "gold_evidence_id": p.gold_evidence_id,
                        "candidates": list(p.candidates),
                        "depth": p.depth,
                        "gold_rank": p.gold_rank,
                    }
                    for p in fused
                ),
            )
            report = {
                "schema_version": "genrag.fusion.v1",
                "metrics": evaluate(fused, universe, cutoffs=cutoffs),
                "weights": {"left": args.left_weight, "right": args.right_weight},
                "rrf_constant": args.rrf_constant,
                "inputs": {str(p): sha256_file(p) for p in inputs},
                "predictions_sha256": sha256_file(args.output),
                "universe_sha256": universe_digest(universe),
            }
            _emit(report, sidecar)
            return
    report["inputs"] = {str(p): sha256_file(p) for p in inputs}
    if args.output is not None:
        _protect_outputs([args.output], inputs)
    _emit(report, args.output)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        _run(args)
    except (ValidationError, OSError, UnicodeError) as error:
        if isinstance(error, UnicodeError):
            message = "Input is not valid UTF-8 text"
        elif isinstance(error, OSError):
            message = f"File operation failed: {error.strerror or type(error).__name__}"
        else:
            message = str(error)
        print(f"genrag: {message}", file=sys.stderr)
        return 2
    return 0
