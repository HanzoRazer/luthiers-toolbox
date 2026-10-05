"""Validator-owned evidence. Proposals carry references; this module resolves them.

A digest establishes integrity of artifact bytes. It does not establish that
the measurement those bytes describe is trustworthy.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Mapping, Protocol

from app.physical_engineering.errors import (
    EvidenceDigestMismatch,
    EvidenceNotFound,
    ValidatorConfigurationError,
)


def text_token(value: object) -> bool:
    """True for a non-blank string with no leading or trailing space."""
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def text_tuple(value: object) -> bool:
    return isinstance(value, tuple) and all(text_token(item) for item in value)


def is_finite_number(value: object) -> bool:
    """True for finite int/float values. Booleans, strings, NaN, and infinities are not."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


@dataclass(frozen=True)
class EvidenceRef:
    """An untrusted citation. It carries no measured value and no authority."""

    ref_id: str
    expected_kind: str


@dataclass(frozen=True)
class ResolvedEvidence:
    """A fact returned by the trusted resolver after it recomputed the digest."""

    ref_id: str
    kind: str
    value: float | None
    unit: str | None
    uncertainty: float | None
    source_run: str
    schema_id: str
    schema_version: str
    artifact_sha256: str


@dataclass(frozen=True)
class FixtureArtifact:
    """Opaque bytes plus the metadata the fixture store claims for them.

    ``expected_sha256`` is what the store says the bytes hash to. The resolver
    recomputes SHA-256 and does not trust this field on its own.
    """

    ref_id: str
    kind: str
    value: float | None
    unit: str | None
    uncertainty: float | None
    source_run: str
    schema_id: str
    schema_version: str
    artifact_bytes: bytes
    expected_sha256: str


class EvidenceResolver(Protocol):
    """Validator-owned lookup. Implementations must recompute the artifact digest."""

    def resolve(self, ref: EvidenceRef) -> ResolvedEvidence:
        """Return the trusted fact, or raise ``EvidenceNotFound`` / ``EvidenceDigestMismatch``."""


class InMemoryEvidenceResolver:
    """Fixture-backed resolver. It reads the store on every call.

    Passing a ``dict`` keeps that mapping live, so a test can change the store
    after a snapshot is captured. Replay must not observe that change.
    """

    def __init__(self, artifacts: Mapping[str, FixtureArtifact] | tuple[FixtureArtifact, ...]):
        if isinstance(artifacts, dict):
            self._artifacts = artifacts
            return
        store: dict[str, FixtureArtifact] = {}
        for artifact in artifacts:
            if artifact.ref_id in store:
                raise ValidatorConfigurationError(
                    f"duplicate fixture ref_id {artifact.ref_id!r}"
                )
            store[artifact.ref_id] = artifact
        self._artifacts = store

    def resolve(self, ref: EvidenceRef) -> ResolvedEvidence:
        artifact = self._artifacts.get(ref.ref_id)
        if artifact is None:
            raise EvidenceNotFound(ref.ref_id)
        digest = hashlib.sha256(artifact.artifact_bytes).hexdigest()
        if digest != artifact.expected_sha256:
            raise EvidenceDigestMismatch(ref.ref_id)
        return ResolvedEvidence(
            ref_id=artifact.ref_id,
            kind=artifact.kind,
            value=artifact.value,
            unit=artifact.unit,
            uncertainty=artifact.uncertainty,
            source_run=artifact.source_run,
            schema_id=artifact.schema_id,
            schema_version=artifact.schema_version,
            artifact_sha256=digest,
        )
