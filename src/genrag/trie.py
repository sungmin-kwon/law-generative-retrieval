"""Tokenizer-independent identifier constraints for generative decoding."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from genrag.errors import ValidationError


def _token(value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValidationError("Token IDs must be nonnegative integers")


class IdentifierTrie:
    """Constrain output to registered token sequences, with an explicit EOS token.

    Tokenization, prompt-prefix removal and generation remain the caller's
    responsibility. A terminal ID can also prefix another ID, so both EOS and
    continuation tokens are allowed at that node. Invalid prefixes allow nothing.
    """

    def __init__(self, eos_token_id: int) -> None:
        _token(eos_token_id)
        self.eos_token_id = eos_token_id
        self._children: dict[int, IdentifierTrie] = {}
        self._terminal = False

    def add(self, tokens: Iterable[int]) -> None:
        values = tuple(tokens)
        if not values:
            raise ValidationError("An identifier must contain at least one token")
        for value in values:
            _token(value)
            if value == self.eos_token_id:
                raise ValidationError("Identifier tokens must not contain EOS")
        node = self
        for value in values:
            if value not in node._children:
                node._children[value] = IdentifierTrie(self.eos_token_id)
            node = node._children[value]
        node._terminal = True

    def _walk(self, tokens: Sequence[int]) -> IdentifierTrie | None:
        node = self
        for value in tokens:
            _token(value)
            if value not in node._children:
                return None
            node = node._children[value]
        return node

    def allowed_next(self, prefix: Sequence[int]) -> tuple[int, ...]:
        node = self._walk(prefix)
        if node is None:
            return ()
        allowed = set(node._children)
        if node._terminal:
            allowed.add(self.eos_token_id)
        return tuple(sorted(allowed))

    def contains(self, tokens: Sequence[int]) -> bool:
        node = self._walk(tokens)
        return node is not None and node._terminal
