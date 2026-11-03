"""Identifier prefix, terminal and invalid-token decoding constraints."""

import unittest

from genrag import IdentifierTrie
from genrag.errors import ValidationError


class TrieTests(unittest.TestCase):
    def test_prefix_tree_only_admits_registered_continuations(self):
        trie = IdentifierTrie(99)
        trie.add([1, 2, 3])
        trie.add([1, 4])
        self.assertEqual(trie.allowed_next([]), (1,))
        self.assertEqual(trie.allowed_next([1]), (2, 4))
        self.assertEqual(trie.allowed_next([1, 2, 3]), (99,))
        self.assertTrue(trie.contains([1, 4]))
        self.assertFalse(trie.contains([1, 2]))

    def test_terminal_identifier_can_prefix_another_identifier(self):
        trie = IdentifierTrie(9)
        trie.add([1])
        trie.add([1, 2])
        self.assertEqual(trie.allowed_next([1]), (2, 9))

    def test_invalid_prefix_does_not_fall_back_to_unconstrained_output(self):
        trie = IdentifierTrie(9)
        trie.add([1, 2])
        self.assertEqual(trie.allowed_next([7]), ())
        self.assertFalse(trie.contains([7]))

    def test_empty_and_eos_containing_ids_are_rejected_without_partial_mutation(self):
        trie = IdentifierTrie(9)
        for tokens in [[], [1, 9], [1, True], [1, -1]]:
            with self.assertRaises(ValidationError):
                trie.add(tokens)
        self.assertEqual(trie.allowed_next([]), ())

    def test_duplicate_insert_is_idempotent(self):
        trie = IdentifierTrie(0)
        trie.add([1, 2])
        trie.add([1, 2])
        self.assertEqual(trie.allowed_next([1]), (2,))


if __name__ == "__main__":
    unittest.main()
