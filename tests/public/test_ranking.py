"""Fusion invariants and regression coverage for lower-scoring extra chunks."""

import unittest

from genrag import ChunkHit, collapse_chunks, reciprocal_rank_fusion
from genrag.embeddings import EmbeddingSpec, validate_embedding
from genrag.errors import ValidationError


class RankingTests(unittest.TestCase):
    def test_adding_a_lower_scoring_chunk_cannot_demote_its_document(self):
        original = [ChunkHit("a", 0.9, "summary"), ChunkHit("b", 0.8, "detail")]
        expanded = original + [ChunkHit("a", 0.1, "detail")]
        self.assertEqual(collapse_chunks(original), collapse_chunks(expanded))
        self.assertEqual(collapse_chunks(expanded)[0].document_id, "a")

    def test_aggregation_is_independent_of_input_order(self):
        hits = [ChunkHit("b", 1, "z"), ChunkHit("a", 1, "y"), ChunkHit("a", 1, "x")]
        self.assertEqual(collapse_chunks(hits), collapse_chunks(reversed(hits)))
        self.assertEqual(collapse_chunks(hits)[0].chunk_id, "x")

    def test_nonfinite_scores_are_rejected(self):
        for value in [float("nan"), float("inf"), True]:
            with self.assertRaises(ValidationError):
                ChunkHit("a", value)

    def test_duplicate_channel_votes_are_not_counted_twice(self):
        result = reciprocal_rank_fusion({"x": ["a", "a", "b"], "y": ["b"]})
        self.assertEqual(result, ("b", "a"))

    def test_unknowns_consume_rank_without_receiving_votes(self):
        self.assertEqual(reciprocal_rank_fusion({"x": [None, "a"], "y": ["b"]}), ("b", "a"))

    def test_ties_are_stable_across_channel_order(self):
        a = reciprocal_rank_fusion({"x": ["b", "a"], "y": ["a", "b"]})
        b = reciprocal_rank_fusion({"y": ["a", "b"], "x": ["b", "a"]})
        self.assertEqual(a, b)
        self.assertEqual(a, ("a", "b"))

    def test_weights_are_explicit_finite_and_cover_channels(self):
        for weights in [{}, {"x": -1}, {"x": float("nan")}, {"x": 0}]:
            with self.assertRaises(ValidationError):
                reciprocal_rank_fusion({"x": ["a"]}, weights=weights)
        self.assertEqual(
            reciprocal_rank_fusion({"x": ["a"], "y": ["b"]}, weights={"x": 1, "y": 0}),
            ("a",),
        )

    def test_embedding_spec_never_silently_truncates_or_normalizes(self):
        spec = EmbeddingSpec("explicit-model", 2)
        self.assertEqual(validate_embedding([3, 4], spec), (3.0, 4.0))
        for vector in [[1], [0, 0], [float("nan"), 1], [True, 1]]:
            with self.assertRaises(ValidationError):
                validate_embedding(vector, spec)


if __name__ == "__main__":
    unittest.main()
