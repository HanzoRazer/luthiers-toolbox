"""Beginner proposal harness. Status strings are the gate's own names.

Policy numbers used here come from the existing proposal-gate fixtures.
This module does not define a second removal limit or a second result map.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.physical_engineering import (
    AuthorityClass,
    EvidenceRef,
    ValidationResult,
    to_json,
    validate_proposal,
)
from app.physical_engineering import beginner_proposal_harness as harness
from app.physical_engineering.beginner_proposal_harness import (
    BeginnerProposalHarnessError,
    BeginnerProposalRequest,
    run_beginner_proposal,
)
from .test_physical_engineering_proposal_v1 import (
    TEST_MAX_REMOVAL_MM,
    _policy,
    _refs,
    _resolver,
)


def _request(**over) -> BeginnerProposalRequest:
    base = dict(
        workflow_id="beginner-remove-material-001",
        proposal_id="prop-beginner-0001",
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
        known_missing_evidence=(),
        contradictory_evidence=(),
    )
    base.update(over)
    return BeginnerProposalRequest(**base)


def _run(**over):
    return run_beginner_proposal(
        _request(**over),
        resolver=_resolver(),
        policy=_policy(),
    )


def test_complete_request_copies_advisory_allowed():
    result = _run()
    assert result.status == "advisory_allowed"
    assert result.status == result.validation.result.value
    assert result.validation.result is ValidationResult.ADVISORY_ALLOWED
    assert result.validation.advisory_review_allowed is True
    assert result.proposal.claimed_authority == AuthorityClass.ADVISORY_ONLY
    assert result.explanations == result.validation.reason_codes
    assert result.required_evidence == result.validation.required_evidence
    assert result.guidance_lines[0] == "result=advisory_allowed"
    assert result.provenance.construction == "new"
    assert result.provenance.recovered_historical_code is False
    assert result.provenance.grounding_agent == "not_used"
    assert result.provenance.result_owner == "validate_proposal"
    assert result.provenance.order == "LTB-MVS-BEGINNER-PROPOSAL-HARNESS-001"
    again = validate_proposal(
        result.proposal, resolver=_resolver(), policy=_policy()
    )
    assert result.validation == again


def test_no_evidence_refs_copies_evidence_required():
    result = _run(evidence_refs=())
    assert result.status == "evidence_required"
    assert "MISSING_REQUIRED_EVIDENCE_KIND" in result.explanations
    assert result.explanations == result.validation.reason_codes
    assert "thickness_map" in result.required_evidence
    assert "modal_frequency" in result.required_evidence
    assert result.validation.advisory_review_allowed is False


def test_unknown_evidence_ref_copies_evidence_required():
    refs = (
        EvidenceRef("missing-thickness", "thickness_map"),
        EvidenceRef("ttp-2026-10-04-mode3", "modal_frequency"),
    )
    result = _run(evidence_refs=refs)
    assert result.status == "evidence_required"
    assert result.explanations == ("EVIDENCE_REFERENCE_NOT_FOUND",)
    assert result.status == result.validation.result.value


def test_contradictory_evidence_copies_evidence_required():
    result = _run(contradictory_evidence=("ttp_stiff_vs_thickness_near_min",))
    assert result.status == "evidence_required"
    assert "CONTRADICTORY_EVIDENCE_PRESENT" in result.explanations
    assert result.validation.advisory_review_allowed is False


def test_magnitude_above_caller_policy_copies_rejected():
    result = _run(magnitude_mm=TEST_MAX_REMOVAL_MM + 0.9)
    assert result.status == "rejected"
    assert "EXCESSIVE_REMOVAL_MAGNITUDE" in result.explanations
    assert result.proposal.proposed_change.magnitude_mm == TEST_MAX_REMOVAL_MM + 0.9


def test_unknown_action_copies_rejected():
    result = _run(action="sand_the_top")
    assert result.status == "rejected"
    assert result.explanations == ("INVALID_ACTION_TYPE",)
    assert result.proposal.proposed_change.action == "sand_the_top"


def test_user_goal_is_not_parsed_into_a_magnitude():
    goal = "please remove 5 mm from the lower bout"
    result = _run(user_goal=goal, magnitude_mm=None, evidence_refs=_refs())
    assert result.proposal.proposed_change.magnitude_mm is None
    assert result.proposal.proposed_change.description == goal
    assert result.proposal.engineering_basis == goal
    assert result.status == "evidence_required"
    assert "REMOVAL_MAGNITUDE_MISSING" in result.explanations


def test_non_advisory_claim_is_forwarded_and_rejected():
    result = _run(claimed_authority="manufacturing_authority")
    assert result.proposal.claimed_authority == "manufacturing_authority"
    assert result.proposal.claimed_authority != AuthorityClass.ADVISORY_ONLY
    assert result.status == "rejected"
    assert result.explanations == ("ILLEGITIMATE_AUTHORITY_CLAIM",)


def test_duplicate_evidence_ref_copies_rejected():
    modal, thickness = _refs()
    result = _run(evidence_refs=(thickness, thickness, modal))
    assert result.status == "rejected"
    assert result.explanations == ("DUPLICATE_EVIDENCE_REFERENCE",)


def test_same_inputs_are_byte_stable():
    first = to_json(_run())
    second = to_json(_run())
    assert first == second
    assert "advisory_allowed" in first
    assert "PROPOSAL_READY" not in first


def test_blank_workflow_id_does_not_call_the_validator(monkeypatch):
    calls = []

    def _boom(*_args, **_kwargs):
        calls.append(1)
        raise AssertionError("validate_proposal was called")

    monkeypatch.setattr(harness, "validate_proposal", _boom)
    with pytest.raises(BeginnerProposalHarnessError, match="workflow_id"):
        run_beginner_proposal(
            _request(workflow_id=" "),
            resolver=_resolver(),
            policy=_policy(),
        )
    assert calls == []


def test_missing_policy_does_not_call_the_validator(monkeypatch):
    calls = []
    monkeypatch.setattr(
        harness,
        "validate_proposal",
        lambda *_a, **_k: calls.append(1),
    )
    with pytest.raises(BeginnerProposalHarnessError, match="policy"):
        run_beginner_proposal(_request(), resolver=_resolver(), policy=None)
    assert calls == []


def test_validate_proposal_is_called_once(monkeypatch):
    calls = {"n": 0}
    real = harness.validate_proposal

    def _wrapped(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(harness, "validate_proposal", _wrapped)
    result = _run()
    assert calls["n"] == 1
    assert result.status == result.validation.result.value


def _imports_and_classes(source: str):
    tree = ast.parse(source)
    imported: list[str] = []
    defined: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.ClassDef):
            defined.append(node.name)
    return " ".join(imported), defined


def test_harness_imports_stay_on_the_proposal_seam():
    source = Path(harness.__file__).read_text(encoding="utf-8")
    blob, defined = _imports_and_classes(source)
    found = [
        name
        for name in (
            "tools.grounding_agent",
            "grounding_agent",
            "archive",
            "cam",
            "dxf",
            "gcode",
        )
        if name in blob
    ]
    assert found == []
    assert "PhysicalEngineeringProposalV1" not in defined
    assert "ValidationPolicyV1" not in defined
    assert "ValidationResult" not in defined


def test_harness_source_records_new_construction_without_a_second_map():
    source = Path(harness.__file__).read_text(encoding="utf-8")
    assert "PROPOSAL_READY" not in source
    assert "0.6" not in source
    assert "2.5" not in source
    assert "New construction" in source
    assert "LTB-MVS-BEGINNER-PROPOSAL-HARNESS-001" in source
