"""Select one approved active policy and construct ``ValidationPolicyV1``.

Selection does not invent thresholds. Zero matches and several matches both
fail closed. The constructed object is the existing validator policy. It
grants human-review eligibility only when the validator says so, and it does
not authorize manufacture.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.physical_engineering.evidence import is_finite_number, text_token
from app.physical_engineering.policy import ValidationPolicyV1
from app.physical_engineering.validation_policy_record_v1 import (
    REQUIRED_VALUE_UNIT,
    PolicyStatus,
    LtbValidationPolicyRecordV1,
    ValidationPolicyError,
)
from app.physical_engineering.validation_policy_repository import (
    FileValidationPolicyRepository,
)


@dataclass(frozen=True)
class PolicySelection:
    """Caller-supplied match. Omitted identity means the single active match."""

    subject_id: str
    action: str
    unit: str
    policy_id: str | None = None
    policy_revision: str | None = None

    def __post_init__(self) -> None:
        if not text_token(self.subject_id) or not text_token(self.action):
            raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "selection")
        if not text_token(self.unit):
            raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "unit")


def select_validation_policy(
    repository: FileValidationPolicyRepository,
    selection: PolicySelection,
) -> ValidationPolicyV1:
    if not isinstance(repository, FileValidationPolicyRepository):
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "repository")
    if not isinstance(selection, PolicySelection):
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "selection")
    if selection.policy_id is None and selection.policy_revision is None:
        return _as_policy(_one_active(repository, selection))
    if selection.policy_id is None or selection.policy_revision is None:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "policy identity")
    record = repository.get(selection.policy_id, selection.policy_revision)
    _require_active(record)
    _require_applicable(record, selection)
    return _as_policy(record)


def _one_active(repository, selection: PolicySelection) -> LtbValidationPolicyRecordV1:
    matches = [
        record
        for record in repository.list_records()
        if record.status == PolicyStatus.ACTIVE.value and _matches(record, selection)
    ]
    matches.sort(key=lambda record: (record.policy_id, record.policy_revision))
    if not matches:
        raise ValidationPolicyError("VALIDATION_POLICY_NOT_FOUND", selection.subject_id)
    if len(matches) > 1:
        names = ",".join(f"{record.policy_id}@{record.policy_revision}" for record in matches)
        raise ValidationPolicyError("VALIDATION_POLICY_AMBIGUOUS", names)
    _require_active(matches[0])
    return matches[0]


def _require_active(record: LtbValidationPolicyRecordV1) -> None:
    if record.status != PolicyStatus.ACTIVE.value:
        raise ValidationPolicyError("VALIDATION_POLICY_NOT_ACTIVE", record.policy_id)
    if record.approval is None:
        raise ValidationPolicyError("VALIDATION_POLICY_NOT_APPROVED", record.policy_id)


def _require_applicable(record: LtbValidationPolicyRecordV1, selection: PolicySelection) -> None:
    if not _matches(record, selection):
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", record.policy_id)


def _matches(record: LtbValidationPolicyRecordV1, selection: PolicySelection) -> bool:
    values = record.policy_values
    return (
        record.applicability.subject_id == selection.subject_id
        and record.applicability.action == selection.action
        and values.max_test_removal_unit == selection.unit
        and values.min_test_remaining_thickness_unit == selection.unit
    )


def _as_policy(record: LtbValidationPolicyRecordV1) -> ValidationPolicyV1:
    if record.policy_values.max_test_removal_unit != REQUIRED_VALUE_UNIT:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "unit")
    if record.policy_values.min_test_remaining_thickness_unit != REQUIRED_VALUE_UNIT:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "unit")
    return ValidationPolicyV1(
        policy_id=record.policy_id,
        policy_version=record.policy_revision,
        max_test_removal_mm=_number(record.policy_values.max_test_removal_mm),
        min_test_remaining_thickness_mm=_number(
            record.policy_values.min_test_remaining_thickness_mm
        ),
    )


def _number(value: str) -> float:
    try:
        number = float(value)
    except OverflowError:
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "policy_values") from None
    if not is_finite_number(number):
        raise ValidationPolicyError("VALIDATION_POLICY_INCOMPATIBLE", "policy_values")
    return number
