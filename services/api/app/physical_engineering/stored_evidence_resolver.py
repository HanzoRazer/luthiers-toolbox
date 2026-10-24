"""Production evidence resolver for the existing ``EvidenceResolver`` protocol.

``resolve`` receives one citation. Applicability is bound when the resolver is
constructed, because the protocol does not pass the proposal. A resolved fact
is a stored record whose bytes, subject, revision, region, and unit match that
binding. It is not a review verdict and it is not a manufacturing permission.

Age-based staleness is not decided here. A record is inactive when a later
record names it in ``supersedes_evidence_id``. Two active values for the same
subject, revision, region, quantity, and unit are reported as
``MULTIPLE_VALUES_REQUIRE_POLICY``. No numeric tolerance is applied.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.physical_engineering.errors import EvidenceNotFound, EvidenceResolutionError
from app.physical_engineering.evidence import EvidenceRef, ResolvedEvidence, text_token
from app.physical_engineering.evidence_artifact_v1 import LtbStoredEvidenceArtifactV1
from app.physical_engineering.evidence_repository import EvidenceRepository
from app.physical_engineering.stored_evidence_repository import EvidenceRepositoryError


class StoredEvidenceResolutionError(EvidenceResolutionError):
    """A citation failed for a reason the proposal gate does not translate.

    ``EvidenceNotFound`` and ``EvidenceDigestMismatch`` stay the gate's own
    types. Every other code propagates, so it cannot become ``advisory_allowed``.
    """

    def __init__(self, code: str, evidence_id: str):
        self.code = code
        super().__init__(f"{code}:{evidence_id}")


@dataclass(frozen=True)
class ApplicabilityContext:
    """Caller-supplied binding. The resolver does not fill these fields."""

    subject_id: str
    subject_revision: str
    region_id: str
    coordinate_frame: str
    unit_by_kind: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        for name in ("subject_id", "subject_revision", "region_id", "coordinate_frame"):
            if not text_token(getattr(self, name)):
                raise StoredEvidenceResolutionError("MALFORMED", name)
        if not isinstance(self.unit_by_kind, tuple):
            raise StoredEvidenceResolutionError("MALFORMED", "unit_by_kind")
        for kind, unit in self.unit_by_kind:
            if not text_token(kind) or not text_token(unit):
                raise StoredEvidenceResolutionError("MALFORMED", "unit_by_kind")


class StoredEvidenceResolver:
    def __init__(self, repository: EvidenceRepository, applicability: ApplicabilityContext):
        if repository is None or not isinstance(applicability, ApplicabilityContext):
            raise StoredEvidenceResolutionError("MALFORMED", "resolver")
        self._repository = repository
        self._applicability = applicability
        self._units = dict(applicability.unit_by_kind)

    def resolve(self, ref: EvidenceRef) -> ResolvedEvidence:
        if not isinstance(ref, EvidenceRef) or not text_token(ref.ref_id):
            raise StoredEvidenceResolutionError("MALFORMED", "evidence_ref")
        try:
            record = self._repository.get(ref.ref_id)
        except EvidenceNotFound:
            raise
        except EvidenceRepositoryError as exc:
            raise StoredEvidenceResolutionError("MALFORMED", ref.ref_id) from exc
        self._require_applicable(record)
        return _fact(record)

    def _require_applicable(self, record: LtbStoredEvidenceArtifactV1) -> None:
        context = self._applicability
        _match(record.subject_id, context.subject_id, "SUBJECT_MISMATCH", record.evidence_id)
        _match(
            record.subject_revision,
            context.subject_revision,
            "REVISION_MISMATCH",
            record.evidence_id,
        )
        if (
            record.region_id != context.region_id
            or record.coordinate_frame != context.coordinate_frame
        ):
            raise StoredEvidenceResolutionError("REGION_MISMATCH", record.evidence_id)
        expected = self._units.get(record.evidence_kind)
        if expected is None or record.unit != expected:
            raise StoredEvidenceResolutionError("UNIT_MISMATCH", record.evidence_id)
        if _is_superseded(self._repository, record):
            raise StoredEvidenceResolutionError("SUPERSEDED", record.evidence_id)
        if _has_other_value(self._repository, record):
            raise StoredEvidenceResolutionError(
                "MULTIPLE_VALUES_REQUIRE_POLICY", record.evidence_id
            )


def duplicate_reference_ids(refs: tuple[EvidenceRef, ...]) -> tuple[str, ...]:
    """Ids cited more than once. The proposal gate rejects these before resolve."""
    seen: set[str] = set()
    duplicates: list[str] = []
    for ref in refs:
        if ref.ref_id in seen and ref.ref_id not in duplicates:
            duplicates.append(ref.ref_id)
        seen.add(ref.ref_id)
    return tuple(duplicates)


def _match(actual: str, expected: str, code: str, evidence_id: str) -> None:
    if actual != expected:
        raise StoredEvidenceResolutionError(code, evidence_id)


def _fact(record: LtbStoredEvidenceArtifactV1) -> ResolvedEvidence:
    return ResolvedEvidence(
        ref_id=record.evidence_id,
        kind=record.evidence_kind,
        value=float(record.quantity_value),
        unit=record.unit,
        uncertainty=float(record.uncertainty),
        source_run=record.provenance.source_id,
        artifact_sha256=record.payload_digest,
    )


def _is_superseded(repository: EvidenceRepository, record: LtbStoredEvidenceArtifactV1) -> bool:
    for other in repository.list_for_subject(record.subject_id, record.subject_revision):
        if other.supersedes_evidence_id == record.evidence_id:
            return True
    return False


def _has_other_value(repository: EvidenceRepository, record: LtbStoredEvidenceArtifactV1) -> bool:
    for other in repository.list_for_subject(record.subject_id, record.subject_revision):
        if other.evidence_id == record.evidence_id or _is_superseded(repository, other):
            continue
        if _same_quantity(record, other) and other.quantity_value != record.quantity_value:
            return True
    return False


def _same_quantity(
    record: LtbStoredEvidenceArtifactV1, other: LtbStoredEvidenceArtifactV1
) -> bool:
    return (
        other.region_id == record.region_id
        and other.coordinate_frame == record.coordinate_frame
        and other.quantity_name == record.quantity_name
        and other.unit == record.unit
    )
