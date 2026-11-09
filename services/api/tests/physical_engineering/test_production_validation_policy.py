"""Selection returns one existing ValidationPolicyV1 or a typed failure."""
from __future__ import annotations

import pytest

from app.physical_engineering.policy import ValidationPolicyV1
from app.physical_engineering.production_validation_policy import (
    PolicySelection,
    select_validation_policy,
)
from app.physical_engineering.validation_policy_record_v1 import ValidationPolicyError
from app.physical_engineering.validation_policy_repository import FileValidationPolicyRepository
from .test_validation_policy_record_v1 import active_record, draft_record


def _directory(tmp_path):
    return tmp_path / "policies"


def _selection(**over) -> PolicySelection:
    base = dict(subject_id="plate-007", action="remove_material", unit="mm")
    base.update(over)
    return PolicySelection(**base)


def _store(tmp_path, *records):
    repository = FileValidationPolicyRepository(_directory(tmp_path))
    for record in records:
        repository.save(record)
    return repository


def test_no_active_policy_is_not_found(tmp_path):
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_NOT_FOUND"):
        select_validation_policy(_store(tmp_path), _selection())


def test_two_active_policies_are_ambiguous(tmp_path):
    repository = _store(
        tmp_path,
        active_record(policy_id="plate-review-a"),
        active_record(policy_id="plate-review-b", policy_revision="2"),
    )
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_AMBIGUOUS"):
        select_validation_policy(repository, _selection())


def test_draft_policy_is_not_selectable(tmp_path):
    repository = _store(tmp_path, draft_record())
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_NOT_FOUND"):
        select_validation_policy(repository, _selection())


def test_superseded_policy_is_not_selectable(tmp_path):
    repository = _store(tmp_path, active_record(status="SUPERSEDED"))
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_NOT_FOUND"):
        select_validation_policy(repository, _selection())


def test_revoked_policy_is_not_selectable(tmp_path):
    repository = _store(tmp_path, active_record(status="REVOKED"))
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_NOT_FOUND"):
        select_validation_policy(repository, _selection())


def test_one_active_policy_constructs_the_existing_dataclass(tmp_path):
    record = active_record()
    selected = select_validation_policy(_store(tmp_path, record), _selection())
    assert isinstance(selected, ValidationPolicyV1)
    assert selected.policy_id == record.policy_id
    assert selected.policy_version == record.policy_revision
    assert selected.max_test_removal_mm == 1.25
    assert selected.min_test_remaining_thickness_mm == 2.0
    assert not hasattr(selected, "advisory_review_allowed")


def test_wrong_subject_action_or_unit_is_not_selected(tmp_path):
    repository = _store(tmp_path, active_record())
    for selection in (
        _selection(subject_id="plate-999"),
        _selection(action="modify_brace"),
        _selection(unit="in"),
    ):
        with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_NOT_FOUND"):
            select_validation_policy(repository, selection)


def test_exact_revision_returns_that_active_record(tmp_path):
    record = active_record(policy_revision="2")
    repository = _store(tmp_path, active_record(), record)
    selected = select_validation_policy(
        repository,
        _selection(policy_id="plate-review", policy_revision="2"),
    )
    assert selected.policy_version == "2"
    assert selected.max_test_removal_mm == 1.25


def test_exact_draft_revision_is_not_active(tmp_path):
    repository = _store(tmp_path, draft_record())
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_NOT_ACTIVE"):
        select_validation_policy(
            repository,
            _selection(policy_id="plate-review", policy_revision="1"),
        )


def test_exact_revision_with_the_wrong_subject_is_incompatible(tmp_path):
    repository = _store(tmp_path, active_record())
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_INCOMPATIBLE"):
        select_validation_policy(
            repository,
            _selection(subject_id="other", policy_id="plate-review", policy_revision="1"),
        )


def test_partial_identity_is_refused(tmp_path):
    repository = _store(tmp_path, active_record())
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_INCOMPATIBLE"):
        select_validation_policy(repository, _selection(policy_id="plate-review"))
