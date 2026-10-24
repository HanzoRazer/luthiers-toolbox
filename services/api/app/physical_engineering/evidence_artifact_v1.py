"""LTB-local stored evidence. This is not a Physical Engineering Mesh schema.

The record binds a quantity to a subject, revision, and region and carries
the provenance needed to name where it came from. It has no approval field
and it grants no engineering or manufacturing authority.

``evidence_kind`` and ``uncertainty`` are explicit because the existing
``ResolvedEvidence`` protocol consumes them. They are not inferred.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re

from app.physical_engineering.evidence import text_token
from app.physical_engineering.evidence_serialization import payload_digest


SCHEMA_ID = "ltb_stored_evidence_artifact"
SCHEMA_VERSION = "1.0"

_EVIDENCE_ID = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9_-])?$")
_WINDOWS_RESERVED_NAMES = {
    "aux",
    "clock$",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "con",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
    "nul",
    "prn",
}
_UNIT = re.compile(r"^[a-z][a-z0-9_]*$")
_DECIMAL = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")
_SIGNED_DECIMAL = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")


class EvidenceType(str, Enum):
    MEASURED = "MEASURED"
    CALCULATED = "CALCULATED"
    IMPORTED_SOURCE = "IMPORTED_SOURCE"
    HUMAN_OBSERVED = "HUMAN_OBSERVED"


class EvidenceRecordError(ValueError):
    """The record cannot be stored. Nothing was written."""


@dataclass(frozen=True)
class EvidenceProvenance:
    source_type: str
    source_id: str
    operator_or_process: str

    def __post_init__(self) -> None:
        for name in ("source_type", "source_id", "operator_or_process"):
            if not text_token(getattr(self, name)):
                raise EvidenceRecordError(f"provenance {name} is required")


@dataclass(frozen=True)
class LtbStoredEvidenceArtifactV1:
    schema_id: str
    schema_version: str
    evidence_id: str
    evidence_type: str
    evidence_kind: str
    subject_id: str
    subject_revision: str
    region_id: str
    coordinate_frame: str
    quantity_name: str
    quantity_value: str
    unit: str
    uncertainty: str
    observed_at: str
    recorded_at: str
    provenance: EvidenceProvenance
    payload_digest: str
    supersedes_evidence_id: str | None = None

    def __post_init__(self) -> None:
        _require_schema(self)
        _require_identity(self)
        _require_quantity(self)
        _require_time(self.observed_at, "observed_at")
        _require_time(self.recorded_at, "recorded_at")
        if not isinstance(self.provenance, EvidenceProvenance):
            raise EvidenceRecordError("provenance is required")
        if self.supersedes_evidence_id is not None:
            _require_evidence_id(self.supersedes_evidence_id, "supersedes_evidence_id")
            if self.supersedes_evidence_id == self.evidence_id:
                raise EvidenceRecordError("a record cannot supersede itself")
        if payload_digest(record_fields(self)) != self.payload_digest:
            raise EvidenceRecordError("DIGEST_MISMATCH")


def record_fields(record: LtbStoredEvidenceArtifactV1) -> dict[str, object]:
    provenance = record.provenance
    return {
        "schema_id": record.schema_id,
        "schema_version": record.schema_version,
        "evidence_id": record.evidence_id,
        "evidence_type": record.evidence_type,
        "evidence_kind": record.evidence_kind,
        "subject_id": record.subject_id,
        "subject_revision": record.subject_revision,
        "region_id": record.region_id,
        "coordinate_frame": record.coordinate_frame,
        "quantity_name": record.quantity_name,
        "quantity_value": record.quantity_value,
        "unit": record.unit,
        "uncertainty": record.uncertainty,
        "observed_at": record.observed_at,
        "recorded_at": record.recorded_at,
        "provenance": {
            "operator_or_process": provenance.operator_or_process,
            "source_id": provenance.source_id,
            "source_type": provenance.source_type,
        },
        "payload_digest": record.payload_digest,
        "supersedes_evidence_id": record.supersedes_evidence_id,
    }


def make_evidence_artifact(
    *,
    evidence_id: str,
    evidence_type: str,
    evidence_kind: str,
    subject_id: str,
    subject_revision: str,
    region_id: str,
    coordinate_frame: str,
    quantity_name: str,
    quantity_value: str,
    unit: str,
    uncertainty: str,
    observed_at: datetime,
    recorded_at: datetime,
    provenance: EvidenceProvenance,
    supersedes_evidence_id: str | None = None,
) -> LtbStoredEvidenceArtifactV1:
    """Build a record and attach the digest of its canonical payload."""
    fields = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "evidence_kind": evidence_kind,
        "subject_id": subject_id,
        "subject_revision": subject_revision,
        "region_id": region_id,
        "coordinate_frame": coordinate_frame,
        "quantity_name": quantity_name,
        "quantity_value": quantity_value,
        "unit": unit,
        "uncertainty": uncertainty,
        "observed_at": _stamp(observed_at, "observed_at"),
        "recorded_at": _stamp(recorded_at, "recorded_at"),
        "provenance": {
            "operator_or_process": provenance.operator_or_process,
            "source_id": provenance.source_id,
            "source_type": provenance.source_type,
        },
        "supersedes_evidence_id": supersedes_evidence_id,
    }
    fields["payload_digest"] = payload_digest(fields)
    return LtbStoredEvidenceArtifactV1(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        evidence_id=evidence_id,
        evidence_type=evidence_type,
        evidence_kind=evidence_kind,
        subject_id=subject_id,
        subject_revision=subject_revision,
        region_id=region_id,
        coordinate_frame=coordinate_frame,
        quantity_name=quantity_name,
        quantity_value=quantity_value,
        unit=unit,
        uncertainty=uncertainty,
        observed_at=fields["observed_at"],
        recorded_at=fields["recorded_at"],
        provenance=provenance,
        payload_digest=fields["payload_digest"],
        supersedes_evidence_id=supersedes_evidence_id,
    )


def _require_schema(record: LtbStoredEvidenceArtifactV1) -> None:
    if record.schema_id != SCHEMA_ID or record.schema_version != SCHEMA_VERSION:
        raise EvidenceRecordError("schema identity is not the LTB evidence record")
    try:
        EvidenceType(record.evidence_type)
    except ValueError:
        raise EvidenceRecordError("unknown evidence type") from None


def _require_identity(record: LtbStoredEvidenceArtifactV1) -> None:
    _require_evidence_id(record.evidence_id, "evidence_id")
    for name in (
        "evidence_kind",
        "subject_id",
        "subject_revision",
        "region_id",
        "coordinate_frame",
        "quantity_name",
    ):
        if not text_token(getattr(record, name)):
            raise EvidenceRecordError(f"{name} is required")
    if not _UNIT.fullmatch(record.unit):
        raise EvidenceRecordError("unit must be an explicit lowercase identifier")


def _require_quantity(record: LtbStoredEvidenceArtifactV1) -> None:
    if not _SIGNED_DECIMAL.fullmatch(record.quantity_value):
        raise EvidenceRecordError("quantity value must be a finite decimal string")
    if not _DECIMAL.fullmatch(record.uncertainty):
        raise EvidenceRecordError("uncertainty must be a finite decimal string")


def _require_evidence_id(value: str, name: str) -> None:
    valid = isinstance(value, str) and _EVIDENCE_ID.fullmatch(value) is not None
    reserved = valid and value.split(".", 1)[0] in _WINDOWS_RESERVED_NAMES
    if not valid or reserved:
        raise EvidenceRecordError(f"{name} is required")


def _require_time(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise EvidenceRecordError(f"{name} must be timezone-aware")
    if value.endswith("Z"):
        parsed = value[:-1] + "+00:00"
    else:
        parsed = value
    try:
        stamp = datetime.fromisoformat(parsed)
    except ValueError:
        raise EvidenceRecordError(f"{name} must be timezone-aware") from None
    if stamp.tzinfo is None or stamp.tzinfo.utcoffset(stamp) is None:
        raise EvidenceRecordError(f"{name} must be timezone-aware")


def _stamp(value: datetime, name: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise EvidenceRecordError(f"{name} must be timezone-aware")
    if value.tzinfo.utcoffset(value) is None:
        raise EvidenceRecordError(f"{name} must be timezone-aware")
    return value.isoformat()
