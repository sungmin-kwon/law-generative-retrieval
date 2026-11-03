"""Malformed input, capture-depth selection and portable-manifest boundaries."""

import tempfile
import unittest
from pathlib import Path

from genrag.adapters import load_predictions, load_universe
from genrag.errors import ValidationError
from genrag.integrity import verify_manifest
from genrag.io import atomic_json, atomic_jsonl, iter_jsonl, read_json, sha256_file


class IOTests(unittest.TestCase):
    def test_unicode_atomic_roundtrip_and_partial_write_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            atomic_json(path, {"query": "새로운 검색 질문"})
            self.assertEqual(read_json(path)["query"], "새로운 검색 질문")
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                atomic_json(path, {"invalid": float("nan")})
            self.assertEqual(path.read_bytes(), before)

    def test_malformed_payload_is_not_echoed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            path.write_text("sensitive-payload:invalid\n", encoding="utf-8")
            with self.assertRaises(ValidationError) as caught:
                list(iter_jsonl(path))
            self.assertNotIn("sensitive-payload", str(caught.exception))

    def test_duplicate_keys_arrays_and_nonfinite_json_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            for payload in ['{"a":1,"a":2}', "[]", '{"a":NaN}']:
                path.write_text(payload + "\n", encoding="utf-8")
                with self.assertRaises(ValidationError):
                    list(iter_jsonl(path))

    def test_capture_selects_one_depth_and_preserves_unknown_rank(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.jsonl"
            atomic_jsonl(
                path,
                [
                    {
                        "query_id": "q",
                        "gold_evidence_id": "a",
                        "requested_depth": 5,
                        "documents": [{"evidence_id": "a", "rank": 1}],
                        "gold_rank": 1,
                    },
                    {
                        "query_id": "q",
                        "gold_evidence_id": "a",
                        "requested_depth": 10,
                        "documents": [
                            {"evidence_id": None, "rank": 1},
                            {"evidence_id": "a", "rank": 2},
                        ],
                        "gold_rank": 2,
                    },
                ],
            )
            self.assertEqual(load_predictions(path, depth=5)[0].gold_rank, 1)
            self.assertEqual(load_predictions(path, depth=10)[0].gold_rank, 2)

    def test_duplicate_queries_and_inconsistent_saved_ranks_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.jsonl"
            row = {"query_id": "q", "gold_evidence_id": "a", "candidates": ["a"]}
            atomic_jsonl(path, [row, row])
            with self.assertRaisesRegex(ValidationError, "Duplicate"):
                load_predictions(path)
            atomic_jsonl(path, [{**row, "gold_rank": 2}])
            with self.assertRaisesRegex(ValidationError, "disagrees"):
                load_predictions(path)

    def test_universe_duplicate_ids_are_not_silently_collapsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "universe.json"
            atomic_json(path, {"document_ids": ["a", "a"]})
            with self.assertRaisesRegex(ValidationError, "Duplicate"):
                load_universe(path)

    def test_manifest_hash_and_path_escape_are_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.txt"
            data.write_text("bound input")
            manifest = root / "manifest.json"
            item = {"path": "data.txt", "sha256": sha256_file(data)}
            atomic_json(
                manifest, {"schema_version": "genrag.artifacts.v1", "artifacts": {"data": item}}
            )
            self.assertEqual(verify_manifest(manifest)["artifacts_verified"], 1)
            data.write_text("changed")
            with self.assertRaisesRegex(ValidationError, "changed"):
                verify_manifest(manifest)
            item["path"] = "../outside.txt"
            atomic_json(
                manifest, {"schema_version": "genrag.artifacts.v1", "artifacts": {"data": item}}
            )
            with self.assertRaisesRegex(ValidationError, "escapes"):
                verify_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
