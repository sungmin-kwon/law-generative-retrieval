"""Analytic metric fixtures and evaluation-contract invariants."""

import unittest

from genrag import Prediction, Universe, compare, evaluate
from genrag.errors import ValidationError


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.universe = Universe(frozenset({"a", "b", "c", "d"}))

    def test_unknowns_duplicates_and_empty_results_keep_their_positions(self):
        rows = [Prediction("q1", "a", (None, "b", "b", "a")), Prediction("q2", "c", ())]
        report = evaluate(rows, self.universe)
        self.assertEqual(report["recall_at_1"], 0)
        self.assertEqual(report["recall_at_5"], 0.5)
        self.assertEqual(report["mrr_at_10"], 0.125)
        self.assertEqual(report["unknown_candidate_positions"], 1)
        self.assertEqual(report["duplicate_candidate_positions"], 1)
        self.assertEqual(report["empty_results"], 1)

    def test_mrr_is_truncated_at_the_reported_cutoff(self):
        row = Prediction("q", "a", ("b", "c", "d", "b", "c", "a"))
        self.assertEqual(evaluate([row], self.universe, cutoffs=(1, 5))["mrr_at_5"], 0)
        self.assertAlmostEqual(evaluate([row], self.universe)["mrr_at_10"], 1 / 6)

    def test_depth_five_does_not_support_recall_ten(self):
        with self.assertRaisesRegex(ValidationError, "cutoff"):
            evaluate([Prediction("q", "a", ("a",), depth=5)], self.universe)

    def test_outside_universe_is_rejected_instead_of_filtered(self):
        for row in [Prediction("q", "unknown", ()), Prediction("q", "a", ("unknown",))]:
            with self.assertRaisesRegex(ValidationError, "universe"):
                evaluate([row], self.universe)

    def test_empty_and_duplicate_queries_are_rejected(self):
        row = Prediction("q", "a", ("a",))
        for rows in [[], [row, row]]:
            with self.assertRaises(ValidationError):
                evaluate(rows, self.universe)

    def test_fixed_cohort_requires_complete_coverage(self):
        rows = [Prediction("q1", "a", ("a",)), Prediction("q2", "b", ())]
        self.assertEqual(evaluate(rows, self.universe, cohort=frozenset({"q1"}))["queries"], 1)
        with self.assertRaisesRegex(ValidationError, "Cohort"):
            evaluate(rows, self.universe, cohort=frozenset({"missing"}))

    def test_comparison_does_not_silently_intersect_runs(self):
        a = [Prediction("q1", "a", ("a",))]
        with self.assertRaisesRegex(ValidationError, "coverage"):
            compare(a, [Prediction("q2", "a", ("a",))], self.universe)
        with self.assertRaisesRegex(ValidationError, "Expected document"):
            compare(a, [Prediction("q1", "b", ("a",))], self.universe)
        with self.assertRaisesRegex(ValidationError, "depth"):
            compare(a, [Prediction("q1", "a", ("a",), depth=5)], self.universe)

    def test_paired_transitions_reconcile_with_metric_difference(self):
        a = [Prediction("q1", "a", ("a",)), Prediction("q2", "b", ()), Prediction("q3", "c", ())]
        b = [
            Prediction("q1", "a", ()),
            Prediction("q2", "b", ("b",)),
            Prediction("q3", "c", ("c",)),
        ]
        report = compare(a, b, self.universe)
        self.assertEqual(report["paired"]["left_only_hit"], 1)
        self.assertEqual(report["paired"]["right_only_hit"], 2)
        self.assertEqual(report["paired"]["net_right_hits"], 1)
        self.assertAlmostEqual(report["paired"]["right_minus_left_recall"], 1 / 3)
        self.assertEqual(report["paired"]["oracle_union_coverage"], 1)

    def test_cutoffs_and_record_types_are_strict(self):
        row = Prediction("q", "a", ())
        for cutoffs in [(), (1, 1), (True,), (0,)]:
            with self.assertRaises(ValidationError):
                evaluate([row], self.universe, cutoffs=cutoffs)
        with self.assertRaises(ValidationError):
            Prediction("q", "a", ["a"])
        with self.assertRaises(ValidationError):
            Prediction(" q ", "a", ())


if __name__ == "__main__":
    unittest.main()
