"""Failures of the screening gate itself, distinct from a proposal verdict."""


class ValidatorConfigurationError(RuntimeError):
    """The gate was not configured, so it did not execute and produced no verdict."""


class EvidenceNotFound(LookupError):
    """The cited reference is absent from the trusted evidence store."""


class EvidenceDigestMismatch(ValueError):
    """Recomputed SHA-256 of the artifact bytes does not match the store.

    A matching digest establishes integrity of those bytes. It does not
    establish that the measurement is trustworthy.
    """


class SnapshotIntegrityError(RuntimeError):
    """A frozen snapshot does not replay to the verdict it records."""
