"""End-to-end commands against invented data, without providers or a GPU."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from genrag.cli import main
from genrag.io import atomic_json, atomic_jsonl


class CLITests(unittest.TestCase):
    def inputs(self, root):
        universe = root / "universe.json"
        left, right = root / "left.jsonl", root / "right.jsonl"
        atomic_json(universe, {"document_ids": ["a", "b"]})
        atomic_jsonl(left, [{"query_id": "q", "gold_evidence_id": "a", "candidates": ["b", "a"]}])
        atomic_jsonl(right, [{"query_id": "q", "gold_evidence_id": "a", "candidates": ["a", "b"]}])
        return universe, left, right

    def invoke(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main([str(a) for a in args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_score_compare_and_fusion_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            universe, left, right = self.inputs(root)
            code, stdout, _ = self.invoke(["score", left, "--universe", universe])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout)["metrics"]["mrr_at_10"], 0.5)
            code, stdout, _ = self.invoke(["compare", left, right, "--universe", universe])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout)["right"]["mrr_at_10"], 1)
            output = root / "fused.jsonl"
            code, _, err = self.invoke(
                ["fuse", left, right, "--universe", universe, "--output", output]
            )
            self.assertEqual(code, 0, err)
            self.assertTrue(output.exists())
            self.assertTrue(output.with_suffix(".jsonl.manifest.json").exists())
            self.assertEqual(self.invoke(["score", output, "--universe", universe])[0], 0)

    def test_output_cannot_overwrite_inputs_or_previous_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            universe, left, right = self.inputs(root)
            original = left.read_bytes()
            code, _, error = self.invoke(["score", left, "--universe", universe, "--output", left])
            self.assertEqual(code, 2)
            self.assertIn("overwrite", error)
            self.assertEqual(left.read_bytes(), original)
            output = root / "exists.json"
            output.write_text("prior result")
            self.assertEqual(
                self.invoke(["compare", left, right, "--universe", universe, "--output", output])[
                    0
                ],
                2,
            )
            self.assertEqual(output.read_text(), "prior result")

    def test_bad_numeric_arguments_fail_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            universe, left, right = self.inputs(root)
            code, _, error = self.invoke(
                [
                    "fuse",
                    left,
                    right,
                    "--universe",
                    universe,
                    "--right-weight",
                    "nan",
                    "--output",
                    root / "out.jsonl",
                ]
            )
            self.assertEqual(code, 2)
            self.assertNotIn("Traceback", error)

    def test_doctor_does_not_require_credentials(self):
        code, stdout, _ = self.invoke(["doctor"])
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(stdout)["provider_credentials_inspected"])


if __name__ == "__main__":
    unittest.main()
