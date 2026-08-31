"""Contract tests: models, enums, serialization, request validation."""

from __future__ import annotations

import pytest

from tools.grounding_agent.models import (
    ActiveLane,
    ClaimReason,
    ClaimResult,
    ClaimType,
    ClaimVerdict,
    Confidence,
    CrossRepoPolicy,
    EvidenceClass,
    EvidenceLane,
    EvidenceMode,
    GroundingClaim,
    GroundingReport,
    GroundingRequest,
    GroundingStatus,
    MalformedRequestError,
)


def _lane_dict():
    return {
        "project": "Luthiers-Toolbox-Consolidation-Lab",
        "active_repository": "HanzoRazer/luthiers-toolbox",
        "active_program": "RMOS-CONVERGE",
        "active_order": "RMOS-CONVERGE-001B-B2",
        "active_state": "IMPLEMENTATION",
        "cross_repo_policy": "EVIDENCE_ONLY",
    }


def test_active_lane_round_trip():
    lane = ActiveLane.from_dict(_lane_dict())
    assert lane.cross_repo_policy is CrossRepoPolicy.EVIDENCE_ONLY
    assert lane.to_dict() == _lane_dict()


def test_active_lane_missing_field():
    bad = _lane_dict()
    del bad["active_order"]
    with pytest.raises(MalformedRequestError):
        ActiveLane.from_dict(bad)


def test_active_lane_bad_policy():
    bad = _lane_dict()
    bad["cross_repo_policy"] = "WHATEVER"
    with pytest.raises(MalformedRequestError):
        ActiveLane.from_dict(bad)


def test_claim_from_dict_typed_fields():
    claim = GroundingClaim.from_dict(
        {
            "claim_id": "C-1",
            "type": "repo_head",
            "repository": "HanzoRazer/luthiers-toolbox",
            "ref": "main",
            "expected_sha": "abcdef1",
            "material": True,
        }
    )
    assert claim.type is ClaimType.REPO_HEAD
    assert claim.ref == "main"
    assert claim.material is True


def test_claim_bare_boolean_expected_normalized():
    claim = GroundingClaim.from_dict(
        {"claim_id": "C-2", "type": "file_exists", "ref": "main", "path": "x.py", "expected": True}
    )
    assert claim.expected == {"exists": True}


def test_claim_unknown_type_rejected():
    with pytest.raises(MalformedRequestError):
        GroundingClaim.from_dict({"claim_id": "C-3", "type": "not_a_type"})


def test_claim_non_bool_material_rejected():
    with pytest.raises(MalformedRequestError):
        GroundingClaim.from_dict({"claim_id": "C-4", "type": "worktree_clean", "material": "yes"})


def test_request_round_trip():
    payload = {
        "schema_version": "grounding_request_v0.1",
        "active_lane": _lane_dict(),
        "claims": [
            {"claim_id": "C-1", "type": "worktree_clean", "material": False},
        ],
    }
    request = GroundingRequest.from_dict(payload)
    assert request.to_dict() == payload


def test_request_requires_claims():
    with pytest.raises(MalformedRequestError):
        GroundingRequest.from_dict({"active_lane": _lane_dict(), "claims": []})


def test_request_rejects_duplicate_claim_ids():
    payload = {
        "active_lane": _lane_dict(),
        "claims": [
            {"claim_id": "DUP", "type": "worktree_clean"},
            {"claim_id": "DUP", "type": "worktree_clean"},
        ],
    }
    with pytest.raises(MalformedRequestError):
        GroundingRequest.from_dict(payload)


def test_claim_result_serialization_has_no_forbidden_fields():
    result = ClaimResult(
        claim_id="C-9",
        type=ClaimType.PR_STATE,
        material=True,
        verdict=ClaimVerdict.MISMATCH,
        evidence_class=EvidenceClass.GITHUB_STATE,
        confidence=Confidence.HIGH,
        message="Expected merged=true; observed merged=false.",
    )
    out = result.to_dict()
    for forbidden in ("recommended_fix", "next_action", "suggested_branch", "patch", "reasoning"):
        assert forbidden not in out
    assert out["message"]


def test_report_serialization_shape():
    report = GroundingReport(
        status=GroundingStatus.STALE,
        decision=None,  # type: ignore[arg-type]
        active_lane={},
        claims=[],
    )
    # decision is required by the enum in practice; set it explicitly here.
    from tools.grounding_agent.models import ExecutionDecision

    report.decision = ExecutionDecision.STOP
    out = report.to_dict()
    assert out["schema_version"] == "grounding_report_v0.1"
    assert out["status"] == "STALE"
    assert out["decision"] == "STOP"
    assert set(["claims", "material_divergences", "blocked_checks", "summary"]).issubset(out)


def test_input_contract_evidence_class_exists():
    # D5 requires an INPUT_CONTRACT evidence class for active-lane checks.
    assert EvidenceClass.INPUT_CONTRACT.value == "INPUT_CONTRACT"


# --- v0.2 contract (GROUNDING-AGENT-002) ---------------------------------


def test_handoff_provenance_claim_type_exists():
    assert ClaimType.HANDOFF_PROVENANCE.value == "handoff_provenance"


def test_claim_reason_controlled_vocabulary():
    assert ClaimReason.HANDOFF_LANE_CONFLICT.value == "HANDOFF_LANE_CONFLICT"


def test_evidence_lane_round_trip():
    payload = {"repository": "HanzoRazer/vectorizer-sandbox", "mode": "EVIDENCE_ONLY"}
    lane = EvidenceLane.from_dict(payload)
    assert lane.mode is EvidenceMode.EVIDENCE_ONLY
    assert lane.to_dict() == payload


def test_evidence_lane_bad_mode_rejected():
    with pytest.raises(MalformedRequestError):
        EvidenceLane.from_dict({"repository": "x/y", "mode": "WRITE"})


def test_request_without_evidence_lanes_serializes_as_v01():
    # v0.1 compatibility: evidence_lanes omitted entirely when empty.
    payload = {
        "schema_version": "grounding_request_v0.1",
        "active_lane": _lane_dict(),
        "claims": [{"claim_id": "C-1", "type": "worktree_clean", "material": False}],
    }
    out = GroundingRequest.from_dict(payload).to_dict()
    assert "evidence_lanes" not in out
    assert out == payload


def test_request_with_evidence_lanes_round_trip():
    payload = {
        "schema_version": "grounding_request_v0.1",
        "active_lane": _lane_dict(),
        "evidence_lanes": [
            {"repository": "HanzoRazer/vectorizer-sandbox", "mode": "EVIDENCE_ONLY"}
        ],
        "claims": [{"claim_id": "C-1", "type": "worktree_clean", "material": False}],
    }
    request = GroundingRequest.from_dict(payload)
    assert len(request.evidence_lanes) == 1
    out = request.to_dict()
    assert out["evidence_lanes"] == payload["evidence_lanes"]


def test_claim_result_reason_serialization():
    # Omitted when None (v0.1 unchanged); present when set.
    base = dict(
        claim_id="C-1", type=ClaimType.HANDOFF_PROVENANCE, material=True,
        verdict=ClaimVerdict.MATCH, evidence_class=EvidenceClass.INPUT_CONTRACT,
        confidence=Confidence.HIGH,
    )
    assert "reason" not in ClaimResult(**base).to_dict()
    with_reason = ClaimResult(**base, reason=ClaimReason.HANDOFF_LANE_CONFLICT).to_dict()
    assert with_reason["reason"] == "HANDOFF_LANE_CONFLICT"
