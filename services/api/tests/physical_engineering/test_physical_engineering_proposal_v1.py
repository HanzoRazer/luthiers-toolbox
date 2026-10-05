"""Advisory-gate tests. Fixture policy numbers are not physical safety evidence.

``TEST_MAX_REMOVAL_MM`` (0.6) and ``TEST_MIN_REMAINING_MM`` (2.5) exist only
so a test can construct a ValidationPolicyV1. They have no production
engineering authority.
"""
from __future__ import annotations

import hashlib

import pytest
from dataclasses import replace

from app.physical_engineering import (
    ActionType,
    AuthorityClass,
    EvidenceRef,
    FixtureArtifact,
    GeometryRegion,
    InMemoryEvidenceResolver,
    PhysicalEngineeringProposalV1,
    PhysicalEngineeringValidationV1,
    ProposedChange,
    ValidationPolicyV1,
    ValidationResult,
    ValidatorConfigurationError,
    to_json,
    validate_proposal,
)


# Test-policy fixture only. No production engineering authority.
TEST_MAX_REMOVAL_MM = 0.6
TEST_MIN_REMAINING_MM = 2.5


def _region(**over) -> GeometryRegion:
    base = dict(
        object_id="plate-007",
        geometry_revision="rev-3",
        region_id="lower-bout-R17",
        coordinate_frame="plate-local",
        units="mm",
    )
    base.update(over)
    return GeometryRegion(**base)


def _artifact(ref_id, kind, value, unit, **over) -> FixtureArtifact:
    raw = over.pop("artifact_bytes", f"fixture-bytes:{ref_id}".encode())
    digest = over.pop("expected_sha256", hashlib.sha256(raw).hexdigest())
    base = dict(
        ref_id=ref_id,
        kind=kind,
        value=value,
        unit=unit,
        uncertainty=0.05,
        source_run="fixture-run",
        schema_id="fixture-evidence",
        schema_version="1",
        artifact_bytes=raw,
        expected_sha256=digest,
    )
    base.update(over)
    return FixtureArtifact(**base)


def _store() -> dict[str, FixtureArtifact]:
    return {
        "ttp-2026-10-04-mode3": _artifact(
            "ttp-2026-10-04-mode3", "modal_frequency", 184.6, "hz", uncertainty=1.8,
            source_run="ttp-run-9f3a",
        ),
        "thk-2026-10-04-R17": _artifact(
            "thk-2026-10-04-R17", "thickness_map", 2.9, "mm", uncertainty=0.05,
            source_run="scan-run-21b",
        ),
    }


def _resolver(store=None):
    return InMemoryEvidenceResolver(_store() if store is None else store)


def _policy(**over):
    base = dict(
        policy_id="test-only-review-policy",
        policy_version="1",
        max_test_removal_mm=TEST_MAX_REMOVAL_MM,
        min_test_remaining_thickness_mm=TEST_MIN_REMAINING_MM,
        required_evidence_kinds=("modal_frequency", "thickness_map"),
    )
    base.update(over)
    return ValidationPolicyV1(**base)


def _refs() -> tuple[EvidenceRef, ...]:
    return (
        EvidenceRef("ttp-2026-10-04-mode3", "modal_frequency"),
        EvidenceRef("thk-2026-10-04-R17", "thickness_map"),
    )


def _proposal(**over) -> PhysicalEngineeringProposalV1:
    base = dict(
        schema_id="physical_engineering_proposal",
        schema_version="1.0",
        proposal_id="prop-0001",
        proposing_actor="structural-interpretation-agent",
        claimed_authority=AuthorityClass.ADVISORY_ONLY,
        geometry_region=_region(),
        proposed_change=ProposedChange(
            action=ActionType.REMOVE_MATERIAL,
            magnitude_mm=0.25,
            description="thin lower bout toward target stiffness",
        ),
        evidence_refs=_refs(),
    )
    base.update(over)
    return PhysicalEngineeringProposalV1(**base)


def _screen(proposal=None, **kw):
    return validate_proposal(
        _proposal() if proposal is None else proposal,
        resolver=kw.get("resolver", _resolver()),
        policy=kw.get("policy", _policy()),
    )


def test_missing_evidence_refuses_does_not_default():
    verdict = _screen(_proposal(evidence_refs=()))
    assert verdict.result is ValidationResult.EVIDENCE_REQUIRED
    assert verdict.advisory_review_allowed is False
    assert "INSUFFICIENT_EVIDENCE" in verdict.reason_codes
    assert "provide_measured_evidence_refs" in verdict.required_evidence


def test_contradictory_evidence_escalates():
    proposal = _proposal(contradictory_evidence=("ttp_stiff_vs_thickness_near_min",))
    verdict = _screen(proposal)
    assert verdict.result is ValidationResult.EVIDENCE_REQUIRED
    assert verdict.advisory_review_allowed is False
    assert "CONTRADICTORY_EVIDENCE_PRESENT" in verdict.reason_codes


def test_excessive_removal_rejected():
    change = ProposedChange(
        action=ActionType.REMOVE_MATERIAL,
        magnitude_mm=TEST_MAX_REMOVAL_MM + 0.9,
        description="aggressive thinning",
    )
    verdict = _screen(_proposal(proposed_change=change))
    assert verdict.result is ValidationResult.REJECTED
    assert verdict.advisory_review_allowed is False
    assert "EXCESSIVE_REMOVAL_MAGNITUDE" in verdict.reason_codes


def test_supported_bounded_proposal_is_advisory_allowed():
    verdict = _screen()
    assert verdict.result is ValidationResult.ADVISORY_ALLOWED
    assert verdict.advisory_review_allowed is True
    assert "ALL_CHECKS_PASSED" in verdict.reason_codes


def test_acquire_more_evidence_is_admissible_without_thickness():
    ask = ProposedChange(
        action=ActionType.ACQUIRE_MORE_EVIDENCE,
        description="request thickness scan of upper bout before any removal",
    )
    verdict = _screen(_proposal(proposed_change=ask, evidence_refs=()))
    assert verdict.result is ValidationResult.ADVISORY_ALLOWED
    assert verdict.advisory_review_allowed is True


def test_proposal_cannot_self_grant_authority():
    with pytest.raises(ValueError, match="authority lives only in validation"):
        _proposal(requested_validation=("authorized",))


def test_underspecified_region_requires_evidence():
    verdict = _screen(_proposal(geometry_region=_region(region_id=None)))
    assert verdict.result is ValidationResult.EVIDENCE_REQUIRED
    assert "GEOMETRY_REGION_UNDERSPECIFIED" in verdict.reason_codes


def test_validation_is_deterministically_replayable():
    proposal = _proposal()
    assert _screen(proposal) == _screen(proposal)


@pytest.mark.parametrize(
    "magnitude",
    [-1, 0, float("nan"), float("inf"), float("-inf"), True, "0.25", 10**1000],
)
def test_invalid_removal_magnitude_rejected(magnitude):
    proposal = _proposal(proposed_change=ProposedChange(ActionType.REMOVE_MATERIAL, magnitude))
    verdict = _screen(proposal)
    assert verdict.result is ValidationResult.REJECTED
    assert verdict.advisory_review_allowed is False


def test_known_string_action_obeys_cap():
    proposal = _proposal(proposed_change=ProposedChange("remove_material", 999))
    assert _screen(proposal).result is ValidationResult.REJECTED


def test_known_enum_strings_normalized():
    proposal = _proposal(
        claimed_authority="advisory_only",
        proposed_change=ProposedChange("remove_material", 0.25),
    )
    assert _screen(proposal).result is ValidationResult.ADVISORY_ALLOWED


@pytest.mark.parametrize("action", ["execute", "", None, 12, []])
def test_unknown_actions_rejected(action):
    proposal = _proposal(proposed_change=ProposedChange(action, 0.25))
    assert _screen(proposal).result is ValidationResult.REJECTED


def test_acquisition_cannot_bypass_authority_check():
    proposal = _proposal(
        claimed_authority="authorized",
        proposed_change=ProposedChange(ActionType.ACQUIRE_MORE_EVIDENCE),
    )
    assert _screen(proposal).result is ValidationResult.REJECTED


def test_acquisition_cannot_carry_removal():
    proposal = _proposal(
        proposed_change=ProposedChange(ActionType.ACQUIRE_MORE_EVIDENCE, 0.25),
    )
    assert _screen(proposal).result is ValidationResult.REJECTED


def test_brace_modification_fails_closed():
    proposal = _proposal(proposed_change=ProposedChange(ActionType.MODIFY_BRACE, 999))
    verdict = _screen(proposal)
    assert verdict.result is ValidationResult.REJECTED
    assert verdict.reason_codes == ("ACTION_NOT_YET_GOVERNED",)
    assert verdict.advisory_review_allowed is False


def test_missing_resolver_is_not_a_proposal_verdict():
    with pytest.raises(ValidatorConfigurationError):
        validate_proposal(_proposal(), resolver=None, policy=_policy())


def test_known_missing_evidence_blocks_admission():
    proposal = _proposal(known_missing_evidence=("material_properties",))
    assert _screen(proposal).result is ValidationResult.EVIDENCE_REQUIRED


@pytest.mark.parametrize("over", [dict(ref_id=""), dict(ref_id=" "), dict(expected_kind="")])
def test_invalid_evidence_citation_cannot_hide(over):
    refs = _refs()
    proposal = _proposal(evidence_refs=(refs[0], replace(refs[1], **over)))
    assert _screen(proposal).result is ValidationResult.EVIDENCE_REQUIRED


def test_proposal_citation_cannot_carry_a_measured_value():
    assert set(EvidenceRef.__dataclass_fields__) == {"ref_id", "expected_kind"}
    with pytest.raises(TypeError):
        EvidenceRef("thk-2026-10-04-R17", "thickness_map", value=20)


def test_unknown_reference_requires_evidence():
    refs = (EvidenceRef("ttp-2026-10-04-mode3", "modal_frequency"), EvidenceRef("fabricated", "thickness_map"))
    verdict = _screen(_proposal(evidence_refs=refs))
    assert verdict.result is ValidationResult.EVIDENCE_REQUIRED
    assert verdict.reason_codes == ("EVIDENCE_REFERENCE_NOT_FOUND",)


def test_required_evidence_kind_not_replaced_by_any_one_ref():
    proposal = _proposal(evidence_refs=(_refs()[0],))
    verdict = _screen(proposal)
    assert verdict.required_evidence == ("thickness_map",)
    assert verdict.advisory_review_allowed is False


def test_duplicate_reference_rejected():
    ref = _refs()[0]
    verdict = _screen(_proposal(evidence_refs=(ref, ref)))
    assert verdict.result is ValidationResult.REJECTED


@pytest.mark.parametrize(
    "field",
    ["object_id", "geometry_revision", "region_id", "coordinate_frame", "units"],
)
def test_all_geometry_identifiers_required(field):
    proposal = _proposal(geometry_region=_region(**{field: " "}))
    assert _screen(proposal).result is ValidationResult.EVIDENCE_REQUIRED


def test_units_not_silently_converted():
    proposal = _proposal(geometry_region=_region(units="inch"))
    assert _screen(proposal).result is ValidationResult.REJECTED


def test_geometry_revision_is_an_untrusted_claim():
    """A different revision is not independently checked. PEP-MESH-SEAM-003 closes that."""
    proposal = _proposal(geometry_region=_region(geometry_revision="rev-4"))
    verdict = _screen(proposal)
    assert verdict.result is ValidationResult.ADVISORY_ALLOWED
    assert verdict.advisory_review_allowed is True


@pytest.mark.parametrize(
    "over",
    [
        dict(max_test_removal_mm=float("nan")),
        dict(max_test_removal_mm=-1),
        dict(max_test_removal_mm=True),
        dict(policy_id=""),
        dict(required_evidence_kinds=()),
        dict(required_evidence_kinds=("thickness_map", "thickness_map")),
        dict(min_test_remaining_thickness_mm=float("nan")),
        dict(min_test_remaining_thickness_mm=-0.1),
    ],
)
def test_malformed_policy_refuses_to_execute(over):
    with pytest.raises(ValidatorConfigurationError):
        _screen(policy=_policy(**over))


def test_duplicate_fixture_ref_is_a_configuration_error():
    artifact = _store()["ttp-2026-10-04-mode3"]
    with pytest.raises(ValidatorConfigurationError):
        InMemoryEvidenceResolver((artifact, artifact))


def test_excessive_review_magnitude_rejected_even_without_evidence():
    proposal = _proposal(
        evidence_refs=(),
        proposed_change=ProposedChange(ActionType.REMOVE_MATERIAL, 0.7),
    )
    assert _screen(proposal).result is ValidationResult.REJECTED


@pytest.mark.parametrize(
    "over",
    [
        dict(schema_id="unknown"),
        dict(schema_version="2.0"),
        dict(proposal_id=""),
        dict(proposing_actor=" "),
        dict(known_missing_evidence=["thickness"]),
    ],
)
def test_invalid_proposal_structure(over):
    assert _screen(_proposal(**over)).result is ValidationResult.REJECTED


def test_unknown_requested_checks_not_silently_ignored():
    proposal = _proposal(requested_validation=("finite_element_safety",))
    assert _screen(proposal).result is ValidationResult.REJECTED


def test_authority_smuggling_normalized():
    with pytest.raises(ValueError):
        _proposal(requested_validation=(" AUTHORIZED ",))


def test_rejected_result_cannot_claim_review_grant():
    with pytest.raises(ValueError):
        PhysicalEngineeringValidationV1(
            "physical_engineering_validation",
            "1.0",
            "p",
            ValidationResult.REJECTED,
            ("failed",),
            advisory_review_allowed=True,
        )


def test_nan_not_serializable_as_json():
    proposal = _proposal(proposed_change=ProposedChange(ActionType.REMOVE_MATERIAL, float("nan")))
    with pytest.raises(ValueError):
        to_json(proposal)


def test_result_bound_to_proposal_content_and_policy():
    proposal = _proposal()
    first = _screen(proposal)
    changed = _screen(replace(proposal, engineering_basis="changed"))
    policy_changed = _screen(proposal, policy=_policy(policy_version="2"))
    assert first.proposal_sha256 != changed.proposal_sha256
    assert first.snapshot_sha256 != policy_changed.snapshot_sha256
    assert first.policy_version == "1"
    assert policy_changed.policy_version == "2"
    assert to_json(first) == to_json(_screen(proposal))


def test_wrong_top_level_type_returns_rejection():
    verdict = validate_proposal({}, resolver=_resolver(), policy=_policy())
    assert verdict.result is ValidationResult.REJECTED
    assert verdict.reason_codes == ("INVALID_PROPOSAL_TYPE",)
