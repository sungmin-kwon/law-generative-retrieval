"""Offline evaluation and fusion primitives for generative retrieval."""

from genrag.evaluation import compare, evaluate
from genrag.models import Prediction, Universe
from genrag.ranking import ChunkHit, collapse_chunks, reciprocal_rank_fusion
from genrag.trie import IdentifierTrie

__version__ = "0.1.0"

__all__ = [
    "ChunkHit",
    "IdentifierTrie",
    "Prediction",
    "Universe",
    "collapse_chunks",
    "compare",
    "evaluate",
    "reciprocal_rank_fusion",
]
