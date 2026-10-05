"""Deterministic advisory screening of untrusted physical-change proposals.

No result authorizes manufacture, material removal, brace modification, or
measurement execution. ADVISORY_ALLOWED means eligible for human review only.
The caller must obtain review context from an independent, trusted service;
Python dataclasses and hashes do not authenticate that service or its evidence.
This reference implementation contains no validated guitar structural model.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional
import json
import math
import hashlib


# ─────────────────────────────────────────────────────────────────────
# Vocabulary — deliberately tiny. Do not generalize in v1.
# Restricting the action set makes unsafe authority-leakage easy to detect.
# ─────────────────────────────────────────────────────────────────────

class ActionType(str, Enum):
    REMOVE_MATERIAL = "remove_material"
    MODIFY_BRACE = "modify_brace"
    ACQUIRE_MORE_EVIDENCE = "acquire_more_evidence"


class AuthorityClass(str, Enum):
    # What an agent is ALLOWED to claim. The only legitimate claim in v1.
    ADVISORY_ONLY = "advisory_only"


class ValidationResult(str, Enum):
    ADVISORY_ALLOWED = "advisory_allowed"   # supported, bounded -> human review
    EVIDENCE_REQUIRED = "evidence_required"  # insufficient/contradictory -> escalate
    REJECTED = "rejected"                    # inadmissible (e.g. unsafe magnitude)


# ─────────────────────────────────────────────────────────────────────
# Evidence — the load-bearing concept. A proposal with no RESOLVABLE
# evidence is structurally inadmissible. evidence_refs is why the thesis
# is testable: references must be compared with independent resolver output.
# ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EvidenceRef:
    """A pointer to a measured fact with provenance. Must RESOLVE to be valid."""
    ref_id: str                      # e.g. "ttp-run-2026-10-04-mode3"
    kind: str                        # "modal_frequency" | "thickness_map" | "density" | ...
    value: Optional[float] = None
    unit: Optional[str] = None
    uncertainty: Optional[float] = None   # None = unquantified = treated as missing
    source_run: Optional[str] = None      # provenance; None = unprovenanced = invalid
    resolves: bool = True                 # in production: does the ref actually dereference?


@dataclass(frozen=True)
class GeometryRegion:
    """Where, exactly. Ambiguity here is refusal, not a guess."""
    object_id: str
    geometry_revision: str
    region_id: Optional[str] = None       # None = unspecified region = inadmissible
    coordinate_frame: Optional[str] = None
    units: Optional[str] = None


@dataclass(frozen=True)
class ProposedChange:
    action: ActionType
    magnitude_mm: Optional[float] = None  # for REMOVE_MATERIAL; None ok for ACQUIRE_*
    description: str = ""


# ─────────────────────────────────────────────────────────────────────
# The proposal: AGENT-GENERATED, UNTRUSTED.
# Note what is ABSENT: there is no `authorized` field. The agent cannot
# write its own approval state. That absence is a schema invariant.
# ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PhysicalEngineeringProposalV1:
    schema_id: str
    schema_version: str
    proposal_id: str
    proposing_actor: str
    claimed_authority: AuthorityClass        # a CLAIM. adjudicated, never granted here.
    geometry_region: GeometryRegion
    proposed_change: ProposedChange
    evidence_refs: tuple[EvidenceRef, ...] = ()
    known_missing_evidence: tuple[str, ...] = ()
    contradictory_evidence: tuple[str, ...] = ()
    engineering_basis: str = ""
    requested_validation: tuple[str, ...] = ()
    # Intentionally NO `authorized` / `approved` field. See module docstring.

    def __post_init__(self):
        # Hard schema invariant: a proposal may not smuggle an authority grant.
        forbidden = {"authorized", "approved", "authority_granted", "allow"}
        leaked = forbidden & {v.strip().lower() for v in self.requested_validation if isinstance(v, str)}
        if leaked:
            raise ValueError(
                f"schema invariant violated: proposal attempted to assert "
                f"authority via {leaked}; authority lives only in validation output"
            )


# ─────────────────────────────────────────────────────────────────────
# The validation: DETERMINISTIC, SEPARATELY SPECIFIED.
# These outputs permit human review only; they are not manufacturing authority.
# ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PhysicalEngineeringValidationV1:
    schema_id: str
    schema_version: str
    proposal_id: str                 # ties back to exactly one proposal
    result: ValidationResult
    reason_codes: tuple[str, ...]
    required_evidence: tuple[str, ...] = ()
    checks_passed: tuple[str, ...] = ()
    checks_failed: tuple[str, ...] = ()
    # Human-review flag only. Never an authorization to execute an operation.
    advisory_authority_granted: bool = False
    proposal_sha256: Optional[str] = None
    context_sha256: Optional[str] = None

    def __post_init__(self):
        if type(self.advisory_authority_granted) is not bool:
            raise ValueError("advisory grant must be a boolean")
        if self.advisory_authority_granted and self.result is not ValidationResult.ADVISORY_ALLOWED:
            raise ValueError("only ADVISORY_ALLOWED may grant human review")


# ─────────────────────────────────────────────────────────────────────
# Frozen requirement set. Each check CAN fail (proven by a fixture).
# No check substitutes a default for a missing fact.
# ─────────────────────────────────────────────────────────────────────

# Legacy fixture value only. NOT a validated physical safety limit, and never
# used as a default by the validator. Retained for import compatibility.
MAX_SINGLE_PASS_REMOVAL_MM = 0.6


@dataclass(frozen=True)
class AdvisoryReviewContext:
    """Externally supplied snapshot, bound to one exact geometry revision.

    required_evidence_kinds and max_removal_mm are explicit REVIEW policy,
    not a guarantee of structural safety. resolved_evidence must come from a
    trusted resolver, not from copying the proposing agent's evidence_refs.
    """
    policy_id: str
    policy_version: str
    geometry_region: GeometryRegion
    resolved_evidence: tuple[EvidenceRef, ...]
    required_evidence_kinds: tuple[str, ...]
    max_removal_mm: float


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _strings(value):
    return isinstance(value, tuple) and all(_text(v) for v in value)


def _geometry(value):
    return isinstance(value, GeometryRegion) and all(
        _text(getattr(value, name)) for name in
        ("object_id", "geometry_revision", "region_id", "coordinate_frame", "units")
    )


def _evidence(value):
    return (isinstance(value, EvidenceRef)
            and all(_text(v) for v in (value.ref_id, value.kind, value.unit, value.source_run))
            and _number(value.value) and _number(value.uncertainty)
            and value.uncertainty >= 0 and value.resolves is True)


def _context(value):
    return (isinstance(value, AdvisoryReviewContext)
            and _text(value.policy_id) and _text(value.policy_version)
            and _geometry(value.geometry_region) and value.geometry_region.units == "mm"
            and isinstance(value.resolved_evidence, tuple)
            and all(_evidence(e) for e in value.resolved_evidence)
            and len({e.ref_id for e in value.resolved_evidence}) == len(value.resolved_evidence)
            and _strings(value.required_evidence_kinds) and bool(value.required_evidence_kinds)
            and len(set(value.required_evidence_kinds)) == len(value.required_evidence_kinds)
            and _number(value.max_removal_mm) and value.max_removal_mm > 0)


def _digest(value):
    return hashlib.sha256(to_json(value).encode("utf-8")).hexdigest()


def validate_proposal(p: PhysicalEngineeringProposalV1, *,
                      context: Optional[AdvisoryReviewContext] = None
                      ) -> PhysicalEngineeringValidationV1:
    """Fail-closed advisory gate; no I/O and no fabrication of missing facts.

    Known enum strings are normalized explicitly. Unknown actions never fall
    through. Physical proposals require independent evidence/policy snapshots.
    Replaying requires the exact proposal, context, and validator version.
    """
    def verdict(result, reason, required=()):
        try:
            proposal_digest = _digest(p)
        except (ValueError, TypeError, OverflowError):
            proposal_digest = None
        return PhysicalEngineeringValidationV1(
            "physical_engineering_validation", "1.0",
            p.proposal_id if isinstance(p, PhysicalEngineeringProposalV1) else "",
            result, (reason,), required_evidence=required,
            checks_passed=("advisory_screening_passed",) if result is ValidationResult.ADVISORY_ALLOWED else (),
            checks_failed=(reason,) if result is not ValidationResult.ADVISORY_ALLOWED else (),
            advisory_authority_granted=result is ValidationResult.ADVISORY_ALLOWED,
            proposal_sha256=proposal_digest,
            context_sha256=_digest(context) if _context(context) else None,
        )

    reject = ValidationResult.REJECTED
    need = ValidationResult.EVIDENCE_REQUIRED
    allow = ValidationResult.ADVISORY_ALLOWED
    if not isinstance(p, PhysicalEngineeringProposalV1):
        return verdict(reject, "INVALID_PROPOSAL_TYPE")
    if (p.schema_id != "physical_engineering_proposal" or p.schema_version != "1.0"
            or not _text(p.proposal_id) or not _text(p.proposing_actor)
            or not isinstance(p.proposed_change, ProposedChange)
            or not isinstance(p.engineering_basis, str)
            or not _strings(p.known_missing_evidence)
            or not _strings(p.contradictory_evidence)
            or not _strings(p.requested_validation)):
        return verdict(reject, "INVALID_PROPOSAL_STRUCTURE")
    if p.claimed_authority != AuthorityClass.ADVISORY_ONLY:
        return verdict(reject, "ILLEGITIMATE_AUTHORITY_CLAIM")
    try:
        action = ActionType(p.proposed_change.action)
    except (ValueError, TypeError):
        return verdict(reject, "UNSUPPORTED_ACTION")
    if not isinstance(p.proposed_change.description, str):
        return verdict(reject, "INVALID_CHANGE_DESCRIPTION")
    # No discretionary request may silently become an executed check.
    if p.requested_validation:
        return verdict(reject, "UNSUPPORTED_REQUESTED_VALIDATION")
    if action is ActionType.MODIFY_BRACE:
        return verdict(reject, "BRACE_REVIEW_POLICY_NOT_IMPLEMENTED")
    mag = p.proposed_change.magnitude_mm
    if action is ActionType.REMOVE_MATERIAL:
        if mag is not None and (not _number(mag) or mag <= 0):
            return verdict(reject, "INVALID_REMOVAL_MAGNITUDE")
        if context is not None and not _context(context):
            return verdict(reject, "INVALID_REVIEW_CONTEXT")
        # Explicit review cap precedes missing evidence checks.
        if mag is not None and context is not None and mag > context.max_removal_mm:
            return verdict(reject, "EXCESSIVE_REMOVAL_MAGNITUDE")
    elif mag is not None:
        return verdict(reject, "ACQUISITION_CANNOT_REQUEST_REMOVAL")
    if not _geometry(p.geometry_region):
        return verdict(need, "GEOMETRY_REGION_UNDERSPECIFIED", ("specify_region_id_units_and_frame",))
    if p.geometry_region.units != "mm":
        return verdict(reject, "UNSUPPORTED_GEOMETRY_UNITS")
    if action is ActionType.ACQUIRE_MORE_EVIDENCE:
        return verdict(allow, "ACQUISITION_REQUEST_FOR_HUMAN_REVIEW")
    if mag is None:
        return verdict(need, "REMOVAL_MAGNITUDE_MISSING", ("specify_change_magnitude_mm",))
    if p.contradictory_evidence:
        return verdict(need, "CONTRADICTORY_EVIDENCE_PRESENT", ("resolve_contradiction_or_remeasure",))
    if p.known_missing_evidence:
        return verdict(need, "KNOWN_MISSING_EVIDENCE", p.known_missing_evidence)
    if not isinstance(p.evidence_refs, tuple) or not p.evidence_refs:
        return verdict(need, "INSUFFICIENT_EVIDENCE", ("provide_measured_evidence_refs",))
    if not all(_evidence(e) for e in p.evidence_refs):
        return verdict(need, "INVALID_EVIDENCE_METADATA", ("resolve_all_refs_with_finite_metrics",))
    if len({e.ref_id for e in p.evidence_refs}) != len(p.evidence_refs):
        return verdict(reject, "DUPLICATE_EVIDENCE_REFERENCE")
    if context is None:
        return verdict(need, "INDEPENDENT_REVIEW_CONTEXT_REQUIRED", ("provide_trusted_evidence_and_review_policy",))
    if p.geometry_region != context.geometry_region:
        return verdict(reject, "EVIDENCE_GEOMETRY_MISMATCH")
    registry = {e.ref_id: e for e in context.resolved_evidence}
    if any(registry.get(e.ref_id) != e for e in p.evidence_refs):
        return verdict(need, "EVIDENCE_NOT_INDEPENDENTLY_CONFIRMED", ("resolve_and_reconcile_evidence_refs",))
    kinds = {e.kind for e in p.evidence_refs}
    missing = tuple(k for k in context.required_evidence_kinds if k not in kinds)
    if missing:
        return verdict(need, "REQUIRED_EVIDENCE_KIND_MISSING", missing)
    return verdict(allow, "ALL_CHECKS_PASSED")


def to_json(obj) -> str:
    """Stable, strict JSON; rejects NaN and infinity rather than emitting them."""
    def encode(value):
        if isinstance(value, Enum):
            return value.value
        if hasattr(value, "__dataclass_fields__"):
            return asdict(value)
        raise TypeError(type(value))
    return json.dumps(obj, default=encode, indent=2, sort_keys=True, allow_nan=False)
