"""Expected input and provenance errors, safe to present without payloads."""


class ValidationError(ValueError):
    """An input violates the declared evaluation or publication contract."""
