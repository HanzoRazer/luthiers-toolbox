"""Hardware-free advisory-gate tests. Fixture policy is NOT physical safety evidence."""
from __future__ import annotations

import pytest
from dataclasses import replace

from app.physical_engineering.physical_engineering_proposal_v1 import (
    ActionType, AuthorityClass, ValidationResult,
    EvidenceRef, GeometryRegion, ProposedChange,
    PhysicalEngineeringProposalV1, validate_proposal,
    MAX_SINGLE_PASS_REMOVAL_MM, AdvisoryReviewContext, to_json,
    PhysicalEngineeringValidationV1,
)


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


def _good_evidence() -> tuple[EvidenceRef, ...]:
    return (
        EvidenceRef(
            ref_id="ttp-2026-10-04-mode3", kind="modal_frequency",
            value=184.6, unit="hz", uncertainty=1.8,
            source_run="ttp-run-9f3a", resolves=True,
        ),
        EvidenceRef(
            ref_id="thk-2026-10-04-R17", kind="thickness_map",
            value=2.9, unit="mm", uncertainty=0.05,
            source_run="scan-run-21b", resolves=True,
        ),
    )


def _context(**over):
    base = dict(policy_id="test-only-review-policy", policy_version="1",
                geometry_region=_region(), resolved_evidence=_good_evidence(),
                required_evidence_kinds=("modal_frequency", "thickness_map"),
                max_removal_mm=MAX_SINGLE_PASS_REMOVAL_MM)
    base.update(over)
    return AdvisoryReviewContext(**base)


def _proposal(**over) -> PhysicalEngineeringProposalV1:
    base = dict(
        schema_id="physical_engineering_proposal",
        schema_version="1.0",
        proposal_id="prop-0001",
        proposing_actor="structural-interpretation-agent",
        claimed_authority=AuthorityClass.ADVISORY_ONLY,
        geometry_region=_region(),
        proposed_change=ProposedChange(
            action=ActionType.REMOVE_MATERIAL, magnitude_mm=0.25,
            description="thin lower bout toward target stiffness",
        ),
        evidence_refs=_good_evidence(),
    )
    base.update(over)
    return PhysicalEngineeringProposalV1(**base)


# ─── Case 1: missing thickness evidence -> EVIDENCE_REQUIRED ─────────
# The anti-silent-default case. No evidence must mean refusal, NEVER a
# plausible default. (Born from the Saw-defaults / OCR-no-op failures.)
def test_missing_evidence_refuses_does_not_default():
    p = _proposal(evidence_refs=())  # agent reasoned but cited nothing
    v = validate_proposal(p, context=_context())
    assert v.result is ValidationResult.EVIDENCE_REQUIRED
    assert v.advisory_authority_granted is False
    assert "INSUFFICIENT_EVIDENCE" in v.reason_codes
    assert "provide_measured_evidence_refs" in v.required_evidence


# ─── Case 2: contradictory evidence -> EVIDENCE_REQUIRED (escalate) ──
def test_contradictory_evidence_escalates():
    p = _proposal(contradictory_evidence=("ttp_stiff_vs_thickness_near_min",))
    v = validate_proposal(p, context=_context())
    assert v.result is ValidationResult.EVIDENCE_REQUIRED
    assert v.advisory_authority_granted is False
    assert "CONTRADICTORY_EVIDENCE_PRESENT" in v.reason_codes


# ─── Case 3: clearly excessive removal -> REJECTED (not an evidence Q) ─
# Unsafe magnitude is inadmissible independent of how good the evidence is.
def test_excessive_removal_rejected():
    big = ProposedChange(
        action=ActionType.REMOVE_MATERIAL,
        magnitude_mm=MAX_SINGLE_PASS_REMOVAL_MM + 0.9,
        description="aggressive thinning",
    )
    p = _proposal(proposed_change=big)   # evidence is GOOD; magnitude is not
    v = validate_proposal(p, context=_context())
    assert v.result is ValidationResult.REJECTED
    assert v.advisory_authority_granted is False
    assert "EXCESSIVE_REMOVAL_MAGNITUDE" in v.reason_codes


# ─── Case 4: sufficient evidence, bounded change -> ADVISORY_ALLOWED ──
# The one case that reaches a human. Proves the gate is not merely a
# "refuse everything" stub — it admits a proposal confirmed by fixture context.
def test_supported_bounded_proposal_is_advisory_allowed():
    p = _proposal()  # good evidence, 0.25mm, fully specified
    v = validate_proposal(p, context=_context())
    assert v.result is ValidationResult.ADVISORY_ALLOWED
    assert v.advisory_authority_granted is True
    assert "ALL_CHECKS_PASSED" in v.reason_codes


# ─── Case 5: agent requests more measurement -> ADVISORY_ALLOWED ─────
# A well-formed request permits human review, not measurement execution.
def test_acquire_more_evidence_is_always_admissible():
    ask = ProposedChange(
        action=ActionType.ACQUIRE_MORE_EVIDENCE,
        description="request thickness scan of upper bout before any removal",
    )
    p = _proposal(proposed_change=ask, evidence_refs=())  # no evidence needed to ASK
    v = validate_proposal(p, context=_context())
    assert v.result is ValidationResult.ADVISORY_ALLOWED
    assert v.advisory_authority_granted is True


# ─── Invariant: the proposal cannot smuggle an authority grant ───────
def test_proposal_cannot_self_grant_authority():
    with pytest.raises(ValueError, match="authority lives only in validation"):
        _proposal(requested_validation=("authorized",))


# ─── Invariant: a geometry region must be unambiguous ────────────────
def test_underspecified_region_requires_evidence():
    p = _proposal(geometry_region=_region(region_id=None))
    v = validate_proposal(p, context=_context())
    assert v.result is ValidationResult.EVIDENCE_REQUIRED
    assert "GEOMETRY_REGION_UNDERSPECIFIED" in v.reason_codes


# ─── Independent replay: validation depends only on proposal+evidence ─
# Running the gate twice on the same proposal yields an identical verdict,
# with no reference to the proposing agent. This is the "independently
# replayable" property the grant's central claim rests on.
def test_validation_is_deterministically_replayable():
    p = _proposal()
    v1 = validate_proposal(p, context=_context())
    v2 = validate_proposal(p, context=_context())
    assert v1 == v2


@pytest.mark.parametrize("magnitude", [-1, 0, float("nan"), float("inf"),
                                       float("-inf"), True, "0.25", 10**1000])
def test_invalid_removal_magnitude_rejected(magnitude):
    p = _proposal(proposed_change=ProposedChange(ActionType.REMOVE_MATERIAL, magnitude))
    v = validate_proposal(p, context=_context())
    assert v.result is ValidationResult.REJECTED
    assert not v.advisory_authority_granted


def test_known_string_action_obeys_cap():
    p = _proposal(proposed_change=ProposedChange("remove_material", 999))
    assert validate_proposal(p, context=_context()).result is ValidationResult.REJECTED


def test_known_enum_strings_normalized():
    p = _proposal(claimed_authority="advisory_only",
                  proposed_change=ProposedChange("remove_material", .25))
    assert validate_proposal(p, context=_context()).result is ValidationResult.ADVISORY_ALLOWED


@pytest.mark.parametrize("action", ["execute", "", None, 12, []])
def test_unknown_actions_rejected(action):
    p = _proposal(proposed_change=ProposedChange(action, .25))
    assert validate_proposal(p, context=_context()).result is ValidationResult.REJECTED


def test_acquisition_cannot_bypass_authority_check():
    p = _proposal(claimed_authority="authorized",
                  proposed_change=ProposedChange(ActionType.ACQUIRE_MORE_EVIDENCE))
    assert validate_proposal(p).result is ValidationResult.REJECTED


def test_acquisition_cannot_carry_removal():
    p = _proposal(proposed_change=ProposedChange(ActionType.ACQUIRE_MORE_EVIDENCE, .25))
    assert validate_proposal(p).result is ValidationResult.REJECTED


def test_brace_modification_refused_without_implemented_policy():
    p = _proposal(proposed_change=ProposedChange(ActionType.MODIFY_BRACE, 999))
    assert validate_proposal(p, context=_context()).result is ValidationResult.REJECTED


def test_self_claimed_evidence_is_not_independent_context():
    v = validate_proposal(_proposal())
    assert v.result is ValidationResult.EVIDENCE_REQUIRED
    assert "INDEPENDENT_REVIEW_CONTEXT_REQUIRED" in v.reason_codes


def test_known_missing_evidence_blocks_admission():
    p = _proposal(known_missing_evidence=("material_properties",))
    assert validate_proposal(p, context=_context()).result is ValidationResult.EVIDENCE_REQUIRED


@pytest.mark.parametrize("over", [dict(value=None), dict(value=float("nan")),
    dict(uncertainty=-1), dict(uncertainty=float("inf")), dict(source_run=""),
    dict(ref_id=" "), dict(unit=None), dict(resolves=False), dict(resolves=1)])
def test_invalid_evidence_cannot_hide_behind_valid_ref(over):
    refs = _good_evidence()
    p = _proposal(evidence_refs=(refs[0], replace(refs[1], **over)))
    assert validate_proposal(p, context=_context()).result is ValidationResult.EVIDENCE_REQUIRED


def test_forged_value_not_confirmed_by_registry():
    refs = _good_evidence()
    p = _proposal(evidence_refs=(refs[0], replace(refs[1], value=20)))
    v = validate_proposal(p, context=_context())
    assert "EVIDENCE_NOT_INDEPENDENTLY_CONFIRMED" in v.reason_codes


def test_unknown_reference_not_confirmed():
    p = _proposal(evidence_refs=(_good_evidence()[0], replace(_good_evidence()[1], ref_id="fabricated")))
    assert validate_proposal(p, context=_context()).result is ValidationResult.EVIDENCE_REQUIRED


def test_required_evidence_kind_not_replaced_by_any_one_ref():
    p = _proposal(evidence_refs=(_good_evidence()[0],))
    v = validate_proposal(p, context=_context())
    assert v.required_evidence == ("thickness_map",)
    assert not v.advisory_authority_granted


def test_duplicate_reference_rejected():
    ref = _good_evidence()[0]
    assert validate_proposal(_proposal(evidence_refs=(ref, ref)), context=_context()).result is ValidationResult.REJECTED


@pytest.mark.parametrize("field", ["object_id", "geometry_revision", "region_id", "coordinate_frame", "units"])
def test_all_geometry_identifiers_required(field):
    p = _proposal(geometry_region=_region(**{field: " "}))
    assert validate_proposal(p, context=_context()).result is ValidationResult.EVIDENCE_REQUIRED


def test_units_not_silently_converted():
    p = _proposal(geometry_region=_region(units="inch"))
    assert validate_proposal(p, context=_context()).result is ValidationResult.REJECTED


def test_geometry_revision_mismatch():
    p = _proposal(geometry_region=_region(geometry_revision="rev-4"))
    assert validate_proposal(p, context=_context()).result is ValidationResult.REJECTED


@pytest.mark.parametrize("over", [dict(max_removal_mm=float("nan")), dict(max_removal_mm=-1),
    dict(max_removal_mm=True), dict(policy_id=""), dict(required_evidence_kinds=()),
    dict(resolved_evidence=(_good_evidence()[0], _good_evidence()[0]))])
def test_malformed_external_policy_rejected(over):
    assert validate_proposal(_proposal(), context=_context(**over)).result is ValidationResult.REJECTED


def test_excessive_review_magnitude_rejected_even_without_evidence():
    p = _proposal(evidence_refs=(), proposed_change=ProposedChange(ActionType.REMOVE_MATERIAL, .7))
    assert validate_proposal(p, context=_context()).result is ValidationResult.REJECTED


@pytest.mark.parametrize("over", [dict(schema_id="unknown"), dict(schema_version="2.0"),
    dict(proposal_id=""), dict(proposing_actor=" "), dict(known_missing_evidence=["thickness"])])
def test_invalid_proposal_structure(over):
    assert validate_proposal(_proposal(**over), context=_context()).result is ValidationResult.REJECTED


def test_unknown_requested_checks_not_silently_ignored():
    p = _proposal(requested_validation=("finite_element_safety",))
    assert validate_proposal(p, context=_context()).result is ValidationResult.REJECTED


def test_authority_smuggling_normalized():
    with pytest.raises(ValueError):
        _proposal(requested_validation=(" AUTHORIZED ",))


def test_rejected_result_cannot_claim_review_grant():
    with pytest.raises(ValueError):
        PhysicalEngineeringValidationV1("physical_engineering_validation", "1.0", "p",
                                        ValidationResult.REJECTED, ("failed",), advisory_authority_granted=True)


def test_nan_not_serializable_as_json():
    with pytest.raises(ValueError):
        to_json(_proposal(proposed_change=ProposedChange(ActionType.REMOVE_MATERIAL, float("nan"))))


def test_result_bound_to_proposal_content_and_context():
    p = _proposal()
    first = validate_proposal(p, context=_context())
    changed = validate_proposal(replace(p, engineering_basis="changed"), context=_context())
    policy_changed = validate_proposal(p, context=_context(policy_version="2"))
    assert first.proposal_sha256 != changed.proposal_sha256
    assert first.context_sha256 != policy_changed.context_sha256
    assert to_json(first) == to_json(validate_proposal(p, context=_context()))


def test_wrong_top_level_type_returns_rejection():
    assert validate_proposal({}).result is ValidationResult.REJECTED
