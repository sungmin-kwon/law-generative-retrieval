"""A runnable retrieval illustration using four attributed official Korean rulings."""

from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any
from urllib.parse import parse_qs, urlsplit

from genrag.errors import ValidationError
from genrag.models import Prediction, Universe
from genrag.ranking import reciprocal_rank_fusion
from genrag.trie import IdentifierTrie


def load_korean_sample() -> dict[str, Any]:
    """Load package data independently of the current working directory."""
    resource = files("genrag").joinpath("data/korean_tax_rulings.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def run_korean_demo() -> dict[str, Any]:
    """Validate sample IDs, fuse actual ranks and resolve the selected official ruling.

    The input channel rankings are illustrative fixtures, not model inference.
    Character-code tokens demonstrate trie mechanics, not a model's tokenizer.
    """
    data = load_korean_sample()
    if (
        data.get("schema_version") != "genrag.korean-tax-rulings.v1"
        or data.get("official_rulings") is not True
    ):
        raise ValidationError("The demo requires the attributed official-ruling sample")
    documents = {d["evidence_id"]: d for d in data["documents"]}
    if len(documents) != len(data["documents"]) or not all(
        re.fullmatch(r"NTS-INTERP-[A-Z]+-\d{7}", evidence_id) for evidence_id in documents
    ):
        raise ValidationError("Sample documents require unique registered NTS identifiers")
    for document in documents.values():
        provenance = document.get("provenance", {})
        url = urlsplit(provenance.get("source_url", ""))
        if (
            url.scheme != "https"
            or url.netloc != "taxlaw.nts.go.kr"
            or url.path != "/qt/USEQTA002P.do"
            or not re.fullmatch(r"\d{18}", provenance.get("source_id", ""))
            or parse_qs(url.query).get("ntstDcmId") != [provenance.get("source_id")]
            or not provenance.get("official_document_number")
            or not provenance.get("publisher")
            or not provenance.get("issued_on")
        ):
            raise ValidationError("Each official sample requires consistent NTS source attribution")
    universe = Universe(frozenset(documents))
    question = data["example_query"]
    channels = {name: tuple(values) for name, values in data["sample_rankings"].items()}
    if set(channels) != {"dense", "bm25", "generative"}:
        raise ValidationError("Demo requires dense, bm25 and generative sample channels")
    depth = 3
    for candidates in channels.values():
        universe.validate(
            Prediction(question["query_id"], question["gold_evidence_id"], candidates, depth)
        )
    for pair in data["training_pair_examples"]:
        if pair["evidence_id"] not in documents or pair["query"] == question["query"]:
            raise ValidationError("Training examples must resolve and differ from the query")

    trie = IdentifierTrie(eos_token_id=0)
    for evidence_id in documents:
        trie.add(tuple(map(ord, evidence_id)))
    if not all(trie.contains(tuple(map(ord, value))) for value in channels["generative"]):
        raise ValidationError("A sample generated identifier is outside the registered trie")

    hybrid = reciprocal_rank_fusion(
        {name: channels[name] for name in ["dense", "bm25"]}, limit=depth
    )
    augmented = reciprocal_rank_fusion(channels, limit=depth)
    rankings = {**channels, "hybrid": hybrid, "hybrid_plus_gr": augmented}
    stages = {}
    for name, candidates in rankings.items():
        prediction = Prediction(
            question["query_id"], question["gold_evidence_id"], candidates, depth
        )
        universe.validate(prediction)
        stages[name] = {
            "gold_rank": prediction.gold_rank,
            "candidates": [
                {"rank": rank, "evidence_id": value, "title": documents[value]["title"]}
                for rank, value in enumerate(candidates, 1)
            ],
        }
    return {
        "official_rulings": True,
        "notice": data["notice"],
        "ranking_source": data["ranking_source"],
        "question_source": data["question_source"],
        "rights": data["rights"],
        "question": question,
        "training_pair_examples": data["training_pair_examples"],
        "corpus_documents": len(documents),
        "trie_example": {
            "tokenization": "Unicode character codes for illustration; not a model tokenizer",
            "prefix": "NTS-INTERP-",
            "allowed_next_characters": [
                chr(value) for value in trie.allowed_next(tuple(map(ord, "NTS-INTERP-")))
            ],
        },
        "stages": stages,
        "selected_document": documents[augmented[0]],
        "network_calls": 0,
        "gpu_used": False,
        "interpretation": "A worked example of the retrieval flow, not a retrieval benchmark.",
    }


def render_korean_demo(report: dict[str, Any]) -> str:
    """Render the worked example with Korean question/title content."""
    lines = [
        "Korean tax-ruling retrieval: four official rulings, illustrative rankings",
        report["notice"],
        report["ranking_source"],
        report["question_source"],
        "",
        f"Question: {report['question']['query']}",
        f"Expected ruling: {report['question']['gold_evidence_id']}",
        "",
        "Training-pair illustrations for that ruling:",
    ]
    for pair in report["training_pair_examples"]:
        lines.append(f"  [{pair['query_role']}] {pair['query']}")
    for name in ["dense", "bm25", "hybrid", "generative", "hybrid_plus_gr"]:
        stage = report["stages"][name]
        lines.extend(["", f"{name}: expected ruling at rank {stage['gold_rank']}"])
        for candidate in stage["candidates"]:
            lines.append(
                f"  {candidate['rank']}. {candidate['evidence_id']} — {candidate['title']}"
            )
    selected = report["selected_document"]
    provenance = selected["provenance"]
    excerpt = selected["official_excerpt"]
    lines.extend(
        [
            "",
            "Selected official ruling:",
            selected["title"],
            f"{provenance['publisher']} · {provenance['official_document_number']} · "
            f"{provenance['issued_on']}",
            f"Source: {provenance['source_url']}",
            "Project-authored summary:",
            selected["summary"],
            f"Short official excerpt ({excerpt['section']}): {excerpt['text']}",
            f"Excerpt context: {excerpt['context']}",
        ]
    )
    lines.extend(["", report["interpretation"], "No model inference, paid API call or GPU work."])
    return "\n".join(lines)
