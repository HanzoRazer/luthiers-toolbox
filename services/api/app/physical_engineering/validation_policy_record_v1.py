"""LTB-local validation policy record. This is not a Mesh standard.

The record stores owner-supplied values and a separate approval. It does not
choose those values, and it does not authorize manufacture. Only an ``ACTIVE``
record with an approval digest over its canonical payload can be selected.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.physical_engineering.evidence import text_token
from app.physical_engineering.evidence_artifact_v1 import (
    EvidenceRecordError,
    _require_evidence_id,
    _require_time,
    _stamp,
)
from app.physical_engineering.evidence_serialization import payload_digest


SCHEMA_ID = "ltb_validation_policy"
SCHEMA_VERSION = "1.0"
REQUIRED_VALUE_UNIT = "mm"
_DIGEST = r"0123456789abcdef"
_VALUE_NAMES = (
    "max_test_removal_mm",
    "min_test_remaining_thickness_mm",
)


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


class ValidationPolicyError(RuntimeError):
    """The policy record cannot be stored or selected. No verdict was produced."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        message = code if detail == "" else f"{code}:{detail}"
        super().__init__(message)


@dataclass(frozen=True)
class PolicyApplicability:
    subject_id: str
    action: str


@dataclass(frozen=True)
class PolicyValues:
    """Decimal strings. Units are explicit. There is no numeric default."""

    max_test_removal_mm: str
    max_test_removal_unit: str
    min_test_remaining_thickness_mm: str
    min_test_remaining_thickness_unit: str


@dataclass(frozen=True)
class PolicyProvenance:
    source_type: str
    source_id: str
    recorded_by: str


@dataclass(frozen=True)
class PolicyApproval:
    approved_by: str
    approved_at: str
    approval_basis_refs: tuple[str, ...]
    approved_payload_digest: str


@dataclass(frozen=True)
class LtbValidationPolicyRecordV1:
    schema_id: str
    schema_version: str
    policy_id: str
    policy_revision: str
    status: str
    applicability: PolicyApplicability
    policy_values: PolicyValues
    provenance: PolicyProvenance
    approval: PolicyApproval | None
    payload_digest: str

    def __post_init__(self) -> None:
        _require_schema(self)
        _require_identity(self)
        _require_status(self.status)
        _require_applicability(self.applicability)
        _require_values(self.policy_values)
        _require_provenance(self.provenance)
        _require_digest_match(self)
        _require_approval_state(self)


def digest_fields(record: LtbValidationPolicyRecordV1) -> dict[str, object]:
    """Canonical payload. Approval is outside this digest."""
    fields = record_fields(record)
    fields.pop("approval")
    fields.pop("payload_digest")
    return fields


def record_fields(record: LtbValidationPolicyRecordV1) -> dict[str, object]:
    approval = None if record.approval is None else _approval_fields(record.approval)
    return {
        "schema_id": record.schema_id,
        "schema_version": record.schema_version,
        "policy_id": record.policy_id,
        "policy_revision": record.policy_revision,
        "status": record.status,
        "applicability": {
            "action": record.applicability.action,
            "subject_id": record.applicability.subject_id,
        },
        "policy_values": {
            "max_test_removal_mm": record.policy_values.max_test_removal_mm,
            "max_test_removal_unit": record.policy_values.max_test_removal_unit,
            "min_test_remaining_thickness_mm": record.policy_values.min_test_remaining_thickness_mm,
            "min_test_remaining_thickness_unit": (
                record.policy_values.min_test_remaining_thickness_unit
            ),
        },
        "provenance": {
            "recorded_by": record.provenance.recorded_by,
            "source_id": record.provenance.source_id,
            "source_type": record.provenance.source_type,
        },
        "approval": approval,
        "payload_digest": record.payload_digest,
    }


def make_validation_policy_record(
    *,
    policy_id: str,
    policy_revision: str,
    status: str,
    subject_id: str,
    action: str,
    max_test_removal_mm: str,
    max_test_removal_unit: str,
    min_test_remaining_thickness_mm: str,
    min_test_remaining_thickness_unit: str,
    source_type: str,
    source_id: str,
    recorded_by: str,
    approved_by: str | None = None,
    approved_at: datetime | None = None,
    approval_basis_refs: tuple[str, ...] | None = None,
    approved_payload_digest: str | None = None,
) -> LtbValidationPolicyRecordV1:
    """Build a record. Approval is supplied by the caller, or omitted for a draft."""
    _require_status(status)
    applicability, values, provenance = _parts(
        subject_id,
        action,
        max_test_removal_mm,
        max_test_removal_unit,
        min_test_remaining_thickness_mm,
        min_test_remaining_thickness_unit,
        source_type,
        source_id,
        recorded_by,
    )
    digest = payload_digest(
        _unsigned_fields(
            policy_id,
            policy_revision,
            status,
            applicability,
            values,
            provenance,
        )
    )
    approval = _approval_from_parts(
        status,
        approved_by,
        approved_at,
        approval_basis_refs,
        approved_payload_digest,
    )
    return LtbValidationPolicyRecordV1(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        policy_id=policy_id,
        policy_revision=policy_revision,
        status=status,
        applicability=applicability,
        policy_values=values,
        provenance=provenance,
        approval=approval,
        payload_digest=digest,
    )


def _parts(
    subject_id,
    action,
    max_test_removal_mm,
    max_test_removal_unit,
    min_test_remaining_thickness_mm,
    min_test_remaining_thickness_unit,
    source_type,
    source_id,
    recorded_by,
):
    return (
        PolicyApplicability(subject_id, action),
        PolicyValues(
            max_test_removal_mm,
            max_test_removal_unit,
            min_test_remaining_thickness_mm,
            min_test_remaining_thickness_unit,
        ),
        PolicyProvenance(source_type, source_id, recorded_by),
    )


def _approval_from_parts(status, approved_by, approved_at, refs, approved_digest):
    supplied = (approved_by, approved_at, refs, approved_digest)
    if all(part is None for part in supplied):
        if status != PolicyStatus.DRAFT.value:
            raise ValidationPolicyError("VALIDATION_POLICY_NOT_APPROVED", status)
        return None
    if any(part is None for part in supplied):
        raise ValidationPolicyError("VALIDATION_POLICY_NOT_APPROVED", "approval")
    if status == PolicyStatus.DRAFT.value:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "draft approval")
    return PolicyApproval(
        approved_by=approved_by,
        approved_at=_approved_stamp(approved_at),
        approval_basis_refs=refs,
        approved_payload_digest=approved_digest,
    )


def _approved_stamp(value: datetime) -> str:
    try:
        return _stamp(value, "approved_at")
    except EvidenceRecordError:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "approved_at") from None


def _unsigned_fields(policy_id, policy_revision, status, applicability, values, provenance):
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "policy_id": policy_id,
        "policy_revision": policy_revision,
        "status": status,
        "applicability": {
            "action": applicability.action,
            "subject_id": applicability.subject_id,
        },
        "policy_values": {
            "max_test_removal_mm": values.max_test_removal_mm,
            "max_test_removal_unit": values.max_test_removal_unit,
            "min_test_remaining_thickness_mm": values.min_test_remaining_thickness_mm,
            "min_test_remaining_thickness_unit": values.min_test_remaining_thickness_unit,
        },
        "provenance": {
            "recorded_by": provenance.recorded_by,
            "source_id": provenance.source_id,
            "source_type": provenance.source_type,
        },
    }


def _approval_fields(approval: PolicyApproval) -> dict[str, object]:
    return {
        "approval_basis_refs": list(approval.approval_basis_refs),
        "approved_at": approval.approved_at,
        "approved_by": approval.approved_by,
        "approved_payload_digest": approval.approved_payload_digest,
    }


def _require_schema(record: LtbValidationPolicyRecordV1) -> None:
    if record.schema_id != SCHEMA_ID or record.schema_version != SCHEMA_VERSION:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "schema")


def _require_identity(record: LtbValidationPolicyRecordV1) -> None:
    _identifier(record.policy_id, "policy_id")
    _identifier(record.policy_revision, "policy_revision")


def _require_status(status: str) -> None:
    try:
        PolicyStatus(status)
    except ValueError:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "status") from None


def _require_applicability(applicability: PolicyApplicability) -> None:
    if not isinstance(applicability, PolicyApplicability):
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "applicability")
    if not text_token(applicability.subject_id) or not text_token(applicability.action):
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "applicability")


def _require_values(values: PolicyValues) -> None:
    if not isinstance(values, PolicyValues):
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "policy_values")
    _quantity(values.max_test_removal_mm, "max_test_removal_mm", allow_zero=False)
    _quantity(
        values.min_test_remaining_thickness_mm,
        "min_test_remaining_thickness_mm",
        allow_zero=True,
    )
    _unit(values.max_test_removal_unit, "max_test_removal_unit")
    _unit(values.min_test_remaining_thickness_unit, "min_test_remaining_thickness_unit")


def _require_provenance(provenance: PolicyProvenance) -> None:
    if not isinstance(provenance, PolicyProvenance):
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "provenance")
    for name in ("source_type", "source_id", "recorded_by"):
        if not text_token(getattr(provenance, name)):
            raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", name)


def _require_digest_match(record: LtbValidationPolicyRecordV1) -> None:
    if payload_digest(digest_fields(record)) != record.payload_digest:
        raise ValidationPolicyError("VALIDATION_POLICY_DIGEST_MISMATCH", record.policy_id)


def _require_approval_state(record: LtbValidationPolicyRecordV1) -> None:
    if record.status == PolicyStatus.DRAFT.value:
        if record.approval is not None:
            raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "draft approval")
        return
    if record.approval is None:
        raise ValidationPolicyError("VALIDATION_POLICY_NOT_APPROVED", record.policy_id)
    _require_approval(record.approval, record.payload_digest)


def _require_approval(approval: PolicyApproval, digest: str) -> None:
    if not isinstance(approval, PolicyApproval):
        raise ValidationPolicyError("VALIDATION_POLICY_NOT_APPROVED", "approval")
    if not text_token(approval.approved_by):
        raise ValidationPolicyError("VALIDATION_POLICY_NOT_APPROVED", "approved_by")
    _time(approval.approved_at, "approved_at")
    _basis(approval.approval_basis_refs)
    if approval.approved_payload_digest != digest or not _hex_digest(digest):
        raise ValidationPolicyError("VALIDATION_POLICY_DIGEST_MISMATCH", "approval")


def _basis(refs: tuple[str, ...]) -> None:
    if not isinstance(refs, tuple) or not refs:
        raise ValidationPolicyError("VALIDATION_POLICY_NOT_APPROVED", "approval_basis_refs")
    if any(not text_token(item) for item in refs):
        raise ValidationPolicyError("VALIDATION_POLICY_NOT_APPROVED", "approval_basis_refs")


def _quantity(value: str, name: str, *, allow_zero: bool) -> None:
    from decimal import Decimal
    from app.physical_engineering.evidence_artifact_v1 import _DECIMAL

    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", name)
    number = Decimal(value)
    if number < 0 or (number == 0 and not allow_zero):
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", name)


def _unit(value: str, name: str) -> None:
    if value != REQUIRED_VALUE_UNIT:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", name)


def _identifier(value: str, name: str) -> None:
    try:
        _require_evidence_id(value, name)
    except EvidenceRecordError:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", name) from None


def _time(value: str, name: str) -> None:
    try:
        _require_time(value, name)
    except EvidenceRecordError:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", name) from None


def _hex_digest(value: str) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in _DIGEST for char in value)
