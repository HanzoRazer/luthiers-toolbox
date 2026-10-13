"""Deterministic screening rules for the advisory gate.

Imported by proposal_v1 after that module has defined its types, so this
module may import those types without a cycle at call time.
"""
from __future__ import annotations

from app.physical_engineering.errors import EvidenceDigestMismatch, EvidenceNotFound
from app.physical_engineering.evidence import (
    EvidenceRef,
    ResolvedEvidence,
    is_finite_number,
    text_token,
    text_tuple,
)
from app.physical_engineering.proposal_v1 import (
    THICKNESS_KIND,
    ActionType,
    AuthorityClass,
    GeometryRegion,
    PhysicalEngineeringProposalV1,
    ProposedChange,
    ValidationResult,
)


def _resolve_for(proposal, resolver):
    if not _cites_evidence(proposal):
        return "not_invoked", ()
    return _collect(proposal.evidence_refs, resolver)


def _cites_evidence(proposal) -> bool:
    action = ActionType(proposal.proposed_change.action)
    if action is ActionType.ACQUIRE_MORE_EVIDENCE:
        return bool(proposal.evidence_refs)
    return True


def _collect(refs, resolver):
    found = []
    for ref in refs:
        try:
            found.append(resolver.resolve(ref))
        except EvidenceNotFound:
            return "not_found", ()
        except EvidenceDigestMismatch:
            return "digest_mismatch", ()
    return "resolved", tuple(found)


def _verdict_after_resolution(proposal, policy, status, resolved):
    if status == "not_found":
        return (
            ValidationResult.EVIDENCE_REQUIRED,
            "EVIDENCE_REFERENCE_NOT_FOUND",
            ("resolve_and_reconcile_evidence_refs",),
        )
    if status == "digest_mismatch":
        return (ValidationResult.REJECTED, "EVIDENCE_DIGEST_MISMATCH", ())
    return _adjudicate(proposal, resolved, policy)


def _sha256_text(value) -> bool:
    if not text_token(value) or len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value)


def _adjudicate(proposal, resolved, policy):
    failure = _resolved_identity_failure(proposal, resolved)
    if failure is not None:
        return failure
    failure = _required_kind_failure(resolved)
    if failure is not None:
        return failure
    failure = _magnitude_failure(proposal, policy)
    if failure is not None:
        return failure
    failure = _thickness_conflict(resolved, proposal.proposed_change.magnitude_mm, policy)
    if failure is not None:
        return failure
    return (ValidationResult.ADVISORY_ALLOWED, "ALL_CHECKS_PASSED", ())


def _before_resolution(proposal, _policy):
    checks = (
        lambda: _structure_failure(proposal),
        lambda: _claim_failure(proposal),
        lambda: _action_gate(proposal),
        lambda: _geometry_failure(proposal),
        lambda: _stated_evidence_failure(proposal),
    )
    for check in checks:
        failure = check()
        if failure is not None:
            return failure
    return None


def _structure_failure(proposal):
    if not isinstance(proposal, PhysicalEngineeringProposalV1):
        return (ValidationResult.REJECTED, "INVALID_PROPOSAL_TYPE", ())
    if not _identity_ok(proposal) or not _collections_ok(proposal):
        return (ValidationResult.REJECTED, "INVALID_PROPOSAL_STRUCTURE", ())
    return None


def _identity_ok(proposal) -> bool:
    return (
        proposal.schema_id == "physical_engineering_proposal"
        and proposal.schema_version == "1.0"
        and text_token(proposal.proposal_id)
        and text_token(proposal.proposing_actor)
        and isinstance(proposal.proposed_change, ProposedChange)
        and isinstance(proposal.engineering_basis, str)
    )


def _collections_ok(proposal) -> bool:
    return (
        text_tuple(proposal.known_missing_evidence)
        and text_tuple(proposal.contradictory_evidence)
        and text_tuple(proposal.requested_validation)
        and isinstance(proposal.evidence_refs, tuple)
    )


def _claim_failure(proposal):
    if proposal.claimed_authority != AuthorityClass.ADVISORY_ONLY:
        return (ValidationResult.REJECTED, "ILLEGITIMATE_AUTHORITY_CLAIM", ())
    if not isinstance(proposal.proposed_change.description, str):
        return (ValidationResult.REJECTED, "INVALID_CHANGE_DESCRIPTION", ())
    if proposal.requested_validation:
        return (ValidationResult.REJECTED, "UNSUPPORTED_REQUESTED_VALIDATION", ())
    return None


def _action_gate(proposal):
    action = _known_action(proposal)
    if action is None:
        return (ValidationResult.REJECTED, "INVALID_ACTION_TYPE", ())
    if action is ActionType.ACQUIRE_MORE_EVIDENCE:
        return (ValidationResult.ADVISORY_ALLOWED, "ACQUISITION_ALWAYS_ADMISSIBLE", ())
    if action is ActionType.MODIFY_BRACE:
        return (ValidationResult.REJECTED, "ACTION_NOT_YET_GOVERNED", ())
    return None


def _known_action(proposal):
    try:
        return ActionType(proposal.proposed_change.action)
    except (ValueError, TypeError):
        return None


def _magnitude_failure(proposal, policy):
    magnitude = proposal.proposed_change.magnitude_mm
    if magnitude is None:
        return (
            ValidationResult.EVIDENCE_REQUIRED,
            "REMOVAL_MAGNITUDE_MISSING",
            ("specify_change_magnitude_mm",),
        )
    if not is_finite_number(magnitude) or magnitude <= 0:
        return (ValidationResult.REJECTED, "REMOVAL_MAGNITUDE_INVALID", ())
    if magnitude > policy.max_test_removal_mm:
        return (ValidationResult.REJECTED, "EXCESSIVE_REMOVAL_MAGNITUDE", ())
    return None


def _geometry_failure(proposal):
    region = proposal.geometry_region
    if not _region_complete(region):
        return (
            ValidationResult.EVIDENCE_REQUIRED,
            "GEOMETRY_REGION_UNDERSPECIFIED",
            ("specify_region_id_units_and_frame",),
        )
    if region.units != "mm":
        return (ValidationResult.REJECTED, "UNSUPPORTED_GEOMETRY_UNITS", ())
    return None


def _region_complete(region) -> bool:
    if not isinstance(region, GeometryRegion):
        return False
    names = ("object_id", "geometry_revision", "region_id", "coordinate_frame", "units")
    return all(text_token(getattr(region, name)) for name in names)


def _stated_evidence_failure(proposal):
    action = ActionType(proposal.proposed_change.action)
    if action is not ActionType.REMOVE_MATERIAL:
        return None
    return _removal_statement_failure(proposal)


def _removal_statement_failure(proposal):
    if proposal.contradictory_evidence:
        return (
            ValidationResult.EVIDENCE_REQUIRED,
            "CONTRADICTORY_EVIDENCE_PRESENT",
            ("resolve_contradiction_or_remeasure",),
        )
    if proposal.known_missing_evidence:
        return (
            ValidationResult.EVIDENCE_REQUIRED,
            "KNOWN_REQUIRED_EVIDENCE_MISSING",
            proposal.known_missing_evidence,
        )
    if not proposal.evidence_refs:
        return (
            ValidationResult.EVIDENCE_REQUIRED,
            "MISSING_REQUIRED_EVIDENCE_KIND",
            ("thickness_map", "modal_frequency"),
        )
    if not all(_ref_ok(ref) for ref in proposal.evidence_refs):
        return (
            ValidationResult.EVIDENCE_REQUIRED,
            "INVALID_EVIDENCE_METADATA",
            ("resolve_all_refs_with_finite_metrics",),
        )
    if _duplicate_refs(proposal.evidence_refs):
        return (ValidationResult.REJECTED, "DUPLICATE_EVIDENCE_REFERENCE", ())
    return None


def _duplicate_refs(refs) -> bool:
    return len({ref.ref_id for ref in refs}) != len(refs)


def _ref_ok(ref) -> bool:
    return isinstance(ref, EvidenceRef) and text_token(ref.ref_id) and text_token(ref.expected_kind)


def _resolved_identity_failure(proposal, resolved):
    if len(resolved) != len(proposal.evidence_refs):
        return (ValidationResult.REJECTED, "INVALID_EVIDENCE_VALUE", ())
    for ref, fact in zip(proposal.evidence_refs, resolved):
        failure = _one_fact_failure(ref, fact)
        if failure is not None:
            return failure
    return None


def _one_fact_failure(ref, fact):
    if not isinstance(fact, ResolvedEvidence) or fact.ref_id != ref.ref_id:
        return (ValidationResult.REJECTED, "INVALID_EVIDENCE_VALUE", ())
    if fact.kind != ref.expected_kind:
        return (ValidationResult.REJECTED, "EVIDENCE_KIND_MISMATCH", ())
    if not _trusted_value_ok(fact):
        return (ValidationResult.REJECTED, "INVALID_EVIDENCE_VALUE", ())
    if not is_finite_number(fact.uncertainty) or fact.uncertainty < 0:
        return (ValidationResult.REJECTED, "INVALID_EVIDENCE_UNCERTAINTY", ())
    return None


def _trusted_value_ok(fact) -> bool:
    return (
        is_finite_number(fact.value)
        and text_token(fact.unit)
        and text_token(fact.source_run)
        and _sha256_text(fact.artifact_sha256)
    )


_REQUIRED_KINDS = ("thickness_map", "modal_frequency")


def _required_kind_failure(resolved):
    counts: dict[str, int] = {}
    for fact in resolved:
        counts[fact.kind] = counts.get(fact.kind, 0) + 1
    if any(counts.get(kind, 0) > 1 for kind in _REQUIRED_KINDS):
        return (ValidationResult.REJECTED, "AMBIGUOUS_REQUIRED_EVIDENCE", ())
    missing = tuple(kind for kind in _REQUIRED_KINDS if counts.get(kind, 0) == 0)
    if missing:
        return (
            ValidationResult.EVIDENCE_REQUIRED,
            "MISSING_REQUIRED_EVIDENCE_KIND",
            missing,
        )
    return None


def _thickness_conflict(resolved, removal_mm, policy):
    for fact in resolved:
        if fact.kind != THICKNESS_KIND:
            continue
        failure = _one_thickness(fact, removal_mm, policy)
        if failure is not None:
            return failure
    return None


def _one_thickness(fact, removal_mm, policy):
    if fact.unit != "mm" or not is_finite_number(fact.value):
        return (ValidationResult.REJECTED, "INVALID_EVIDENCE_VALUE", ())
    # Strict <: the policy names a minimum, so equality satisfies it.
    remaining = fact.value - removal_mm
    if remaining < policy.min_test_remaining_thickness_mm:
        return (
            ValidationResult.EVIDENCE_REQUIRED,
            "THICKNESS_CONFLICT_WITH_REMOVAL",
            ("remeasure_thickness_or_reduce_removal",),
        )
    return None
