"""End-to-end Korean corpus illustration and installed-resource behavior."""

import contextlib
import io
import json
import tempfile
import unittest
from unittest.mock import patch

from genrag.cli import main
from genrag.demo import load_korean_sample, render_korean_demo, run_korean_demo
from genrag.errors import ValidationError


class KoreanDemoTests(unittest.TestCase):
    def test_worked_example_fuses_ranks_and_resolves_a_korean_ruling(self):
        report = run_korean_demo()
        self.assertTrue(report["official_rulings"])
        self.assertEqual(report["stages"]["dense"]["gold_rank"], 2)
        self.assertEqual(report["stages"]["hybrid"]["gold_rank"], 3)
        self.assertEqual(report["stages"]["hybrid_plus_gr"]["gold_rank"], 1)
        self.assertEqual(
            report["selected_document"]["evidence_id"], "NTS-INTERP-VALUEADDTAX-0063027"
        )
        self.assertIn("반품", report["selected_document"]["title"])
        self.assertEqual(report["network_calls"], 0)
        self.assertFalse(report["gpu_used"])

    def test_resource_loading_is_independent_of_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.chdir(temporary):
            self.assertEqual(run_korean_demo()["corpus_documents"], 4)

    def test_training_wordings_differ_from_the_example_question(self):
        report = run_korean_demo()
        question = report["question"]["query"]
        self.assertEqual(len(report["training_pair_examples"]), 4)
        self.assertTrue(all(p["query"] != question for p in report["training_pair_examples"]))
        self.assertEqual(report["trie_example"]["allowed_next_characters"], ["I", "V"])

    def test_unregistered_candidate_is_rejected(self):
        fixture = load_korean_sample()
        fixture["sample_rankings"]["generative"][0] = "NTS-INTERP-MISSING-9999999"
        with patch("genrag.demo.load_korean_sample", return_value=fixture):
            with self.assertRaisesRegex(ValidationError, "universe"):
                run_korean_demo()

    def test_unlabelled_corpus_cannot_be_presented_as_official(self):
        fixture = load_korean_sample()
        fixture["official_rulings"] = False
        with patch("genrag.demo.load_korean_sample", return_value=fixture):
            with self.assertRaisesRegex(ValidationError, "official-ruling"):
                run_korean_demo()

    def test_missing_or_mismatched_official_sources_are_rejected(self):
        for url in [
            "",
            "https://example.org/ruling",
            "https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=0",
        ]:
            with self.subTest(url=url):
                fixture = load_korean_sample()
                fixture["documents"][0]["provenance"]["source_url"] = url
                with patch("genrag.demo.load_korean_sample", return_value=fixture):
                    with self.assertRaisesRegex(ValidationError, "source attribution"):
                        run_korean_demo()

    def test_human_and_json_cli_present_the_same_example(self):
        report = run_korean_demo()
        self.assertIn(report["question"]["query"], render_korean_demo(report))
        self.assertIn(
            report["selected_document"]["provenance"]["source_url"], render_korean_demo(report)
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["demo-ko", "--json"])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue()), report)


if __name__ == "__main__":
    unittest.main()
