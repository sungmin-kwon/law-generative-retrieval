"""Check published specification integrity and dataset-count reconciliation."""

import json
import unittest
from pathlib import Path

from genrag.io import sha256_file

ROOT = Path(__file__).resolve().parents[2]


class DatasetSpecificationTests(unittest.TestCase):
    def metadata(self):
        return json.loads((ROOT / "dataset_specs/provenance.json").read_text(encoding="utf-8"))

    def test_copied_specifications_match_their_bundled_hashes(self):
        metadata = self.metadata()
        for stage in metadata["specifications"].values():
            for kind in ["prompt", "schema"]:
                item = stage[kind]
                path = ROOT / "dataset_specs" / item["path"]
                self.assertEqual(sha256_file(path), item["bundled_sha256"])
                if item["transformation"] == "none":
                    self.assertEqual(item["original_sha256"], item["bundled_sha256"])

    def test_release_counts_reconcile_without_distributing_data(self):
        metadata = self.metadata()
        self.assertFalse(metadata["data_distributed"])
        counts = metadata["final_consolidation"]
        self.assertEqual(
            counts["base_rows_preserved"] + counts["addition_rows_retained"],
            counts["final_training_rows"],
        )
        self.assertEqual(
            counts["addition_rows_omitted"] + counts["addition_rows_retained"],
            counts["accepted_addition_candidates"],
        )
        self.assertEqual(sum(counts["omission_reasons"].values()), counts["addition_rows_omitted"])
        self.assertEqual(counts["candidate_universe_rulings"] - counts["training_rulings"], 2)

    def test_bundled_schemas_use_neutral_ids_and_are_reference_free(self):
        for path in (ROOT / "dataset_specs/schemas").glob("*.json"):
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(schema["$id"].startswith("urn:genrag:"))
            self.assertNotIn('"$ref"', json.dumps(schema))


if __name__ == "__main__":
    unittest.main()
