"""Fail-closed advisory screening gate for untrusted physical-change proposals.

ADVISORY_ALLOWED means eligible for human review only. It is not physical
admissibility, and it does not authorize manufacture, material removal, brace
modification, or measurement execution.

Evidence references are resolved by a validator-owned resolver. Geometry on
the proposal is an untrusted agent claim: this increment does not resolve it
and does not check it against an independent geometry record. PEP-MESH-SEAM-003
closes that gap.

A digest establishes integrity of artifact bytes, not trustworthiness of the
measurement. Policy numbers are test thresholds with no production engineering
authority. The gate has no numeric defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, replace
from enum import Enum
import json
import hashlib

from app.physical_engineering.errors import (
    SnapshotIntegrityError,
    ValidatorConfigurationError,
)
from app.physical_engineering.evidence import (
    EvidenceResolver,
    is_finite_number,
    text_token,
)
from app.physical_engineering.policy import ValidationPolicyV1
from app.physical_engineering.snapshot import FrozenValidationSnapshotV1, integrity_digest


VALIDATOR_VERSION = "pep-v1-harden-001"
CONTRADICTION_RULE_VERSION = "projected-remaining-thickness-1"
THICKNESS_KIND = "thickness_map"


class ActionType(str, Enum):
    REMOVE_MATERIAL = "remove_material"
    MODIFY_BRACE = "modify_brace"
    ACQUIRE_MORE_EVIDENCE = "acquire_more_evidence"


class AuthorityClass(str, Enum):
    ADVISORY_ONLY = "advisory_only"


class ValidationResult(str, Enum):
    ADVISORY_ALLOWED = "advisory_allowed"
    EVIDENCE_REQUIRED = "evidence_required"
    REJECTED = "rejected"


@dataclass(frozen=True)
class GeometryRegion:
    """Untrusted location claim. Not resolved and not independently checked."""

    object_id: str
    geometry_revision: str
    region_id: str | None = None
    coordinate_frame: str | None = None
    units: str | None = None


@dataclass(frozen=True)
class ProposedChange:
    action: ActionType
    magnitude_mm: float | None = None
    description: str = ""


@dataclass(frozen=True)
class PhysicalEngineeringProposalV1:
    """Agent-authored and untrusted. There is no field that grants authority."""

    schema_id: str
    schema_version: str
    proposal_id: str
    proposing_actor: str
    claimed_authority: AuthorityClass
    geometry_region: GeometryRegion
    proposed_change: ProposedChange
    evidence_refs: tuple[EvidenceRef, ...] = ()
    known_missing_evidence: tuple[str, ...] = ()
    contradictory_evidence: tuple[str, ...] = ()
    engineering_basis: str = ""
    requested_validation: tuple[str, ...] = ()

    def __post_init__(self):
        forbidden = {"authorized", "approved", "authority_granted", "allow"}
        leaked = forbidden & {
            item.strip().lower()
            for item in self.requested_validation
            if isinstance(item, str)
        }
        if leaked:
            raise ValueError(
                "schema invariant violated: proposal attempted to assert "
                f"authority via {leaked}; authority lives only in validation output"
            )


@dataclass(frozen=True)
class PhysicalEngineeringValidationV1:
    """A screening verdict. ``advisory_review_allowed`` is human review only."""

    schema_id: str
    schema_version: str
    proposal_id: str
    result: ValidationResult
    reason_codes: tuple[str, ...]
    required_evidence: tuple[str, ...] = ()
    checks_passed: tuple[str, ...] = ()
    checks_failed: tuple[str, ...] = ()
    advisory_review_allowed: bool = False
    proposal_sha256: str | None = None
    snapshot_sha256: str | None = None
    policy_id: str | None = None
    policy_version: str | None = None
    validator_version: str = VALIDATOR_VERSION

    def __post_init__(self):
        if type(self.advisory_review_allowed) is not bool:
            raise ValueError("advisory review flag must be a boolean")
        allowed = self.result is ValidationResult.ADVISORY_ALLOWED
        if self.advisory_review_allowed and not allowed:
            raise ValueError("only ADVISORY_ALLOWED may permit human review")


def validate_proposal(
    proposal: PhysicalEngineeringProposalV1,
    *,
    resolver: EvidenceResolver,
    policy: ValidationPolicyV1,
) -> PhysicalEngineeringValidationV1:
    """Screen one proposal. Both arguments are required; neither has a default."""
    return capture_snapshot(proposal, resolver=resolver, policy=policy).result


def capture_snapshot(
    proposal: PhysicalEngineeringProposalV1,
    *,
    resolver: EvidenceResolver,
    policy: ValidationPolicyV1,
) -> FrozenValidationSnapshotV1:
    """Run the gate and freeze every authoritative input with the verdict."""
    _require_configuration(resolver, policy)
    early = _before_resolution(proposal, policy)
    if early is not None:
        return _freeze(proposal, policy, (), "not_invoked", early)
    status, resolved = _resolve_for(proposal, resolver)
    verdict = _verdict_after_resolution(proposal, policy, status, resolved)
    stored = resolved if status == "resolved" else ()
    return _freeze(proposal, policy, stored, status, verdict)


def replay_validation(snapshot: FrozenValidationSnapshotV1) -> PhysicalEngineeringValidationV1:
    """Recompute the verdict from the snapshot. This function takes no resolver."""
    if not isinstance(snapshot, FrozenValidationSnapshotV1):
        raise SnapshotIntegrityError("replay requires a frozen snapshot")
    recomputed = _replay(snapshot).result
    identity_ok = recomputed.snapshot_sha256 == snapshot.snapshot_sha256
    if not identity_ok or recomputed != snapshot.result:
        raise SnapshotIntegrityError("frozen snapshot does not replay")
    return recomputed


def to_json(obj) -> str:
    """Stable, strict JSON. Rejects NaN and infinity rather than emitting them."""
    def encode(value):
        if isinstance(value, Enum):
            return value.value
        if hasattr(value, "__dataclass_fields__"):
            return asdict(value)
        raise TypeError(type(value))
    return json.dumps(obj, default=encode, indent=2, sort_keys=True, allow_nan=False)


def _replay(snapshot: FrozenValidationSnapshotV1) -> FrozenValidationSnapshotV1:
    early = _before_resolution(snapshot.proposal, snapshot.policy)
    if early is not None:
        return _freeze(snapshot.proposal, snapshot.policy, (), "not_invoked", early)
    status = snapshot.resolution_status
    resolved = snapshot.resolved_evidence if status == "resolved" else ()
    verdict = _verdict_after_resolution(snapshot.proposal, snapshot.policy, status, resolved)
    return _freeze(snapshot.proposal, snapshot.policy, resolved, status, verdict)



def _require_configuration(resolver, policy) -> None:
    if not callable(getattr(resolver, "resolve", None)):
        raise ValidatorConfigurationError(
            "evidence resolver is required; the gate did not execute"
        )
    if not isinstance(policy, ValidationPolicyV1) or not _policy_fields_ok(policy):
        raise ValidatorConfigurationError(
            "validation policy is required; the gate did not execute"
        )


def _policy_fields_ok(policy) -> bool:
    limits_ok = (
        is_finite_number(policy.max_test_removal_mm)
        and policy.max_test_removal_mm > 0
        and is_finite_number(policy.min_test_remaining_thickness_mm)
        and policy.min_test_remaining_thickness_mm >= 0
    )
    kinds = policy.required_evidence_kinds
    kinds_ok = (
        isinstance(kinds, tuple)
        and bool(kinds)
        and len(set(kinds)) == len(kinds)
        and all(text_token(kind) for kind in kinds)
    )
    return text_token(policy.policy_id) and text_token(policy.policy_version) and limits_ok and kinds_ok


def _freeze(proposal, policy, resolved, status, verdict) -> FrozenValidationSnapshotV1:
    code, reason, required = verdict
    preliminary = _result(proposal, policy, code, reason, required, None)
    digest = _decision_digest(proposal, policy, resolved, status, preliminary)
    final = replace(preliminary, snapshot_sha256=digest)
    return FrozenValidationSnapshotV1(
        proposal=proposal,
        resolved_evidence=tuple(resolved),
        policy=policy,
        validator_version=VALIDATOR_VERSION,
        contradiction_rule_version=CONTRADICTION_RULE_VERSION,
        resolution_status=status,
        result=final,
        snapshot_sha256=digest,
    )


def _decision_digest(proposal, policy, resolved, status, preliminary) -> str:
    payload = {
        "contradiction_rule_version": CONTRADICTION_RULE_VERSION,
        "policy": policy,
        "proposal": proposal,
        "resolution_status": status,
        "resolved_evidence": resolved,
        "result": preliminary,
        "validator_version": VALIDATOR_VERSION,
    }
    return integrity_digest(payload)


def _result(proposal, policy, code, reason, required, snapshot_sha256):
    passed = code is ValidationResult.ADVISORY_ALLOWED
    proposal_id = proposal.proposal_id if isinstance(proposal, PhysicalEngineeringProposalV1) else ""
    return PhysicalEngineeringValidationV1(
        schema_id="physical_engineering_validation",
        schema_version="1.0",
        proposal_id=proposal_id,
        result=code,
        reason_codes=(reason,),
        required_evidence=tuple(required),
        checks_passed=("advisory_screening_passed",) if passed else (),
        checks_failed=() if passed else (reason,),
        advisory_review_allowed=passed,
        proposal_sha256=_proposal_digest(proposal),
        snapshot_sha256=snapshot_sha256,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        validator_version=VALIDATOR_VERSION,
    )


def _proposal_digest(proposal):
    try:
        encoded = to_json(proposal).encode("utf-8")
    except (TypeError, ValueError, OverflowError):
        return None
    return hashlib.sha256(encoded).hexdigest()



from app.physical_engineering.screening import (  # noqa: E402
    _before_resolution,
    _resolve_for,
    _verdict_after_resolution,
)
