"""A selected fixture policy passes through the harness unchanged.

The numbers below are the existing test-policy fixture. They are not an
owner-approved production policy, and no production module contains them.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.physical_engineering import beginner_proposal_harness as harness
from app.physical_engineering.beginner_proposal_harness import (
    BeginnerProposalRequest,
    run_beginner_proposal,
)
from app.physical_engineering.production_validation_policy import (
    PolicySelection,
    select_validation_policy,
)
from app.physical_engineering.validation_policy_record_v1 import ValidationPolicyError
from app.physical_engineering.validation_policy_repository import FileValidationPolicyRepository
from .test_physical_engineering_proposal_v1 import _policy, _refs, _resolver
from .test_validation_policy_record_v1 import active_record


API_ROOT = Path(__file__).resolve().parents[2]
PHYSICAL_ENGINEERING_ROOT = API_ROOT / "app" / "physical_engineering"
CLIENT_ROOT = API_ROOT.parents[1] / "packages" / "client"


def _store(tmp_path):
    repository = FileValidationPolicyRepository(tmp_path / "policies")
    repository.save(
        active_record(
            policy_id="test-only-review-policy",
            policy_revision="1",
            max_test_removal_mm="0.6",
            min_test_remaining_thickness_mm="2.5",
        )
    )
    return repository


def _request(**over) -> BeginnerProposalRequest:
    base = dict(
        workflow_id="beginner-remove-material-001",
        proposal_id="prop-policy-0001",
        subject_id="plate-007",
        subject_revision="rev-3",
        user_goal="ask whether a small lower-bout thinning can be reviewed",
        action="remove_material",
        claimed_authority="advisory_only",
        magnitude_mm=0.25,
        region_id="lower-bout-R17",
        coordinate_frame="plate-local",
        units="mm",
        evidence_refs=_refs(),
    )
    base.update(over)
    return BeginnerProposalRequest(**base)


def _selected(tmp_path):
    return select_validation_policy(
        _store(tmp_path),
        PolicySelection(subject_id="plate-007", action="remove_material", unit="mm"),
    )


def test_loaded_policy_equals_the_existing_test_fixture(tmp_path):
    assert _selected(tmp_path) == _policy()


def test_loaded_policy_calls_the_validator_once(tmp_path, monkeypatch):
    calls = []
    real = harness.validate_proposal

    def _wrapped(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(harness, "validate_proposal", _wrapped)
    result = run_beginner_proposal(
        _request(), resolver=_resolver(), policy=_selected(tmp_path)
    )
    assert calls == [1]
    assert result.status == "advisory_allowed"
    assert "manufacturing" not in " ".join(result.guidance_lines)


def test_missing_evidence_stays_evidence_required(tmp_path):
    result = run_beginner_proposal(
        _request(evidence_refs=()),
        resolver=_resolver(),
        policy=_selected(tmp_path),
    )
    assert result.status == "evidence_required"
    assert result.validation.advisory_review_allowed is False


def test_policy_limit_stays_rejected(tmp_path):
    result = run_beginner_proposal(
        _request(magnitude_mm=0.7),
        resolver=_resolver(),
        policy=_selected(tmp_path),
    )
    assert result.status == "rejected"


def test_missing_policy_does_not_call_the_validator(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        harness,
        "validate_proposal",
        lambda *args, **kwargs: calls.append(1),
    )
    repository = FileValidationPolicyRepository(tmp_path / "policies")
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_NOT_FOUND"):
        select_validation_policy(
            repository,
            PolicySelection(subject_id="plate-007", action="remove_material", unit="mm"),
        )
    assert calls == []


def test_malformed_policy_does_not_call_the_validator(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        harness,
        "validate_proposal",
        lambda *args, **kwargs: calls.append(1),
    )
    directory = tmp_path / "policies"
    repository = FileValidationPolicyRepository(directory)
    (directory / "notes.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValidationPolicyError, match="VALIDATION_POLICY_MALFORMED"):
        select_validation_policy(
            repository,
            PolicySelection(subject_id="plate-007", action="remove_material", unit="mm"),
        )
    assert calls == []


def test_new_modules_do_not_add_a_route_or_a_threshold_literal():
    root = PHYSICAL_ENGINEERING_ROOT
    names = (
        "validation_policy_record_v1.py",
        "validation_policy_serialization.py",
        "validation_policy_repository.py",
        "production_validation_policy.py",
    )
    constructors = []
    for name in names:
        source = (root / name).read_text(encoding="utf-8")
        assert "0.6" not in source
        assert "2.5" not in source
        assert "APIRouter" not in source
        assert "fastapi" not in source
        assert "manufacturing_authority" not in source
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "ValidationPolicyV1":
                constructors.append(name)
    assert constructors == ["production_validation_policy.py"]


def test_gate_and_harness_modules_were_not_rewired():
    root = PHYSICAL_ENGINEERING_ROOT
    for name in ("proposal_v1.py", "beginner_proposal_harness.py"):
        source = (root / name).read_text(encoding="utf-8")
        assert "select_validation_policy" not in source
        assert "FileValidationPolicyRepository" not in source
    client = CLIENT_ROOT
    for path in client.rglob("*"):
        if "node_modules" in path.parts or path.suffix not in {".vue", ".ts", ".js"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert "select_validation_policy" not in text
        assert "validation_policy_record_v1" not in text
