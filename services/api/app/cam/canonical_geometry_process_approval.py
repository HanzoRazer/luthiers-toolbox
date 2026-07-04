"""
Canonical Geometry Process Approval

C2 geometry-origin closure (PR 1 of the process-exclusive dev order).

Keystone ruling being operationalized (PROPOSED — see ratification note below):

    Canonical geometry authority is process-derived, not artifact-derived.
    Source geometry may propose, evidence may support, and representation may
    carry geometry, but canonical body geometry exists only when the approved
    canonical process produces it after a governed approval event.

This module is the first code expression of that ruling. It defines the
process-approval record that a canonical geometry reference must be able to
point at. No artifact — spec, template, vectorizer output, IBG output,
DXF/SVG/STEP file, CAM/runtime geometry, registry entry, route name, or storage
location — becomes canonical by origin, quality, filename, format, or location.
Authority is created only by the approved canonical process following a governed
approval event.

    candidate / evidence / source geometry
      -> approved canonical process
      -> governed approval event
      -> process output
      -> canonical body geometry

If the approved process cannot handle a legitimate new case, the fix is to
extend and re-approve the process (a "process extension"). The fix is never to
grant authority to one individual artifact as an exception.

------------------------------------------------------------------------------
RATIFICATION STATUS: PROPOSED / RATIFICATION-READY.

This is additive bridge infrastructure that makes the ruling *implementable*.
It does NOT mark C2 geometry-origin closed and does NOT encode the packet as
final constitutional truth. The process id / version / approval-rule literals
below are PROPOSED PLACEHOLDERS awaiting repo-owner / governance ratification:

    canonical_process_id      = "body-geometry-canonicalization"
    canonical_process_version = "v1"
    approval_rule_id          = "c2-process-exclusive-canonical-authority-v1"

Do not treat these constants, or the presence of this module, as ratification.
------------------------------------------------------------------------------
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.governance.review_enforcement import (
    ReviewBypassAttemptError,
    ReviewDecision,
    ReviewEnforcement,
)


# ---------------------------------------------------------------------------
# Proposed placeholder vocabulary (RATIFICATION PENDING — do not treat as final)
# ---------------------------------------------------------------------------

PROPOSED_CANONICAL_PROCESS_ID = "body-geometry-canonicalization"
PROPOSED_CANONICAL_PROCESS_VERSION = "v1"
PROPOSED_APPROVAL_RULE_ID = "c2-process-exclusive-canonical-authority-v1"

# ---------------------------------------------------------------------------
# Authenticity status (C2 PR 1 — gap-1 "authenticity labeling" closure)
# ---------------------------------------------------------------------------
#
# An approval record minted through this module carries an authenticity status
# so nothing downstream can mistake an *unverified* approval for a *verified*
# one. In PR 1 there is exactly ONE legal value and it is the fail-safe default:
# UNVERIFIED_PENDING_GOVERNANCE. Verifying that an approver is actually
# *authorized* to approve canonical geometry requires an authorization anchor
# (AUTHORIZED_CANONICAL_APPROVERS) that does not exist yet — it is the PR-2 HARD
# PREREQUISITE. Until it lands, every approval produced here is unverified, and
# the record model REFUSES to be constructed with any other status (fail-safe:
# a missing/failed check can never yield "verified"). See
# docs/handoffs/CAM_7T_GEOMETRY_AUTHORITY_REFERENCES_HANDOFF.md (sequencing).
UNVERIFIED_PENDING_GOVERNANCE = "unverified_pending_governance"
_ALLOWED_AUTHENTICATION_STATES = frozenset({UNVERIFIED_PENDING_GOVERNANCE})

# Registry of approved canonical processes -> the source-geometry roles that
# each process/version is approved to cover. A record whose (process_id,
# version) pair is absent here, or whose source_geometry_role is not covered by
# that process, is NOT an artifact exception to be blessed one-off: it is a
# "process extension required" case that must go back to governance.
#
# This registry is deliberately small and PROPOSED. It is the code seam through
# which governance later ratifies additional processes/roles.
APPROVED_CANONICAL_PROCESSES: Dict[Tuple[str, str], frozenset] = {
    (PROPOSED_CANONICAL_PROCESS_ID, PROPOSED_CANONICAL_PROCESS_VERSION): frozenset(
        {
            "evidence",
            "candidate",
            "governed_evidence_candidate",
            "human_reviewed_candidate",
            "existing_canonical",
        }
    ),
}

# Tokens that describe a *representation / format / route / storage location*.
# Authority may never be inferred from these — a source_authority_state must
# describe a governed authority state, not the file format or where it was
# stored or which route carried it.
_FORBIDDEN_SOURCE_AUTHORITY_STATE_TOKENS = (
    "dxf",
    "svg",
    "step",
    "stp",
    "route",
    "storage",
    "filename",
    "format",
    "path",
    "representation",
)


class CanonicalProcessApprovalError(Exception):
    """
    Raised when a canonical process approval record cannot be created or is
    invalid. The message names the required corrective path — in particular,
    uncovered source cases must be resolved by *process extension*, never by an
    artifact-specific exception.
    """


def _is_system_actor(actor_id: str) -> bool:
    """
    A system actor is a machine actor. Repo convention (see
    ``governance/review_enforcement.py`` / ``authority_state.py``):
    ``system:<component>`` is machine, ``human:<id>`` / ``governance:<rule>``
    are not. A system actor id alone may never confer canonical authority.
    """
    return actor_id.strip().lower().startswith("system:")


def _authority_state_is_representation_derived(state: str) -> bool:
    """
    True if ``source_authority_state`` looks inferred from a format / route /
    storage location rather than a governed authority state.
    """
    normalized = state.strip().lower()
    parts = {
        part
        for part in re.split(r"[^a-z0-9]+", normalized.replace("_", " "))
        if part
    }
    return any(
        normalized == token
        or normalized.startswith(f"{token}:")
        or normalized.startswith(f"{token}/")
        or token in parts
        for token in _FORBIDDEN_SOURCE_AUTHORITY_STATE_TOKENS
    )


class CanonicalProcessApprovalRecord(BaseModel):
    """
    Record of a governed approval event that produced canonical geometry as the
    output of the approved canonical process.

    The presence of this record — not a reviewer click, a file, a route, a
    registry row, or a storage location — is what backs canonical authority.
    The approver identity is *evidence of participation in the process*, not
    authority by itself.
    """

    approval_record_id: str = Field(
        default_factory=lambda: f"canon-approval-{uuid4().hex[:12]}",
        description="Unique approval record identifier",
    )

    canonical_process_id: str = Field(
        ..., description="ID of the approved canonical process that produced the output"
    )
    canonical_process_version: str = Field(
        ..., description="Version of the approved canonical process"
    )
    governed_approval_event_id: str = Field(
        ..., description="ID of the governed approval event"
    )
    approval_rule_id: str = Field(
        ..., description="ID of the approval rule the event satisfied"
    )

    source_geometry_id: str = Field(
        ..., description="ID of the source/evidence/candidate geometry entering the process"
    )
    source_geometry_role: str = Field(
        default="evidence",
        description="Role of the source geometry (evidence, candidate, ...) — never 'authority'",
    )
    source_authority_state: str = Field(
        default="governed_evidence_candidate",
        description=(
            "Governed authority state of the source — may NOT be inferred from "
            "format (DXF/SVG/STEP), route name, or storage location"
        ),
    )

    output_geometry_id: Optional[str] = Field(
        default=None,
        description="ID of the process-output geometry that becomes canonical",
    )

    decision: Literal["approve"] = Field(
        default="approve",
        description="Only 'approve' produces canonical authority",
    )

    approver_id: str = Field(
        ..., description="Actor who participated in the governed approval (human:<id>)"
    )
    approver_role: str = Field(
        default="reviewer",
        description="Role of the approver within the process",
    )

    provenance_hash: str = Field(
        ..., description="Hash tying the output to its actual upstream geometry source"
    )
    process_inputs_hash: str = Field(
        ..., description="Hash of the process inputs at the governed approval event"
    )

    approved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the governed approval event",
    )

    notes: str = Field(default="", description="Free-form notes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    authentication: str = Field(
        default=UNVERIFIED_PENDING_GOVERNANCE,
        description=(
            "Authenticity status of this approval. PR-1: ALWAYS "
            "'unverified_pending_governance' — there is no authorized-approver "
            "anchor yet (AUTHORIZED_CANONICAL_APPROVERS is the PR-2 hard "
            "prerequisite). Fail-safe default: nothing may claim verified authority."
        ),
    )

    deterministic_approval_hash: str = Field(
        default="",
        description="Deterministic hash of the approval record (excludes timestamp)",
    )

    @model_validator(mode="after")
    def enforce_process_approval_invariants(self) -> "CanonicalProcessApprovalRecord":
        """
        Structural invariants of the ruling. These are about the *shape* of a
        valid governed approval; process-coverage ("is this process approved to
        cover this source case?") is a separate policy check in
        ``validate_canonical_process_approval_record``.
        """
        required_non_empty = {
            "canonical_process_id": self.canonical_process_id,
            "canonical_process_version": self.canonical_process_version,
            "governed_approval_event_id": self.governed_approval_event_id,
            "approval_rule_id": self.approval_rule_id,
            "source_geometry_id": self.source_geometry_id,
            "provenance_hash": self.provenance_hash,
            "process_inputs_hash": self.process_inputs_hash,
        }
        for field_name, value in required_non_empty.items():
            if not value or not str(value).strip():
                raise ValueError(
                    f"Canonical process approval requires non-empty '{field_name}' — "
                    "authority is process-derived and cannot be inferred from an "
                    "artifact, format, route, or storage location"
                )

        if self.decision != "approve":
            raise ValueError(
                "Canonical process approval record decision must be 'approve'; "
                "only a governed approve event produces canonical authority"
            )

        if _is_system_actor(self.approver_id):
            raise ValueError(
                f"System actor '{self.approver_id}' may not approve process output — "
                "a machine actor id alone never confers canonical authority"
            )

        if _authority_state_is_representation_derived(self.source_authority_state):
            raise ValueError(
                f"source_authority_state '{self.source_authority_state}' looks inferred "
                "from a format / route / storage location; authority may not be "
                "inferred from DXF/SVG/STEP, route name, or storage location"
            )

        if self.source_geometry_role.strip().lower() in {"authority", "canonical", "source_authority"}:
            raise ValueError(
                f"source_geometry_role '{self.source_geometry_role}' claims authority by "
                "role; source geometry is input/evidence, never authority by opinion alone"
            )

        # Fail-safe authenticity: PR-1 has no authorized-approver anchor, so the
        # ONLY legal status is 'unverified_pending_governance'. A record can never
        # be constructed as verified — a missing/failed authorization check
        # therefore cannot yield verified authority. PR-2 relaxes this when
        # AUTHORIZED_CANONICAL_APPROVERS lands.
        if self.authentication not in _ALLOWED_AUTHENTICATION_STATES:
            raise ValueError(
                f"authentication '{self.authentication}' is not permitted in PR-1; "
                f"the only legal value is '{UNVERIFIED_PENDING_GOVERNANCE}'. No "
                "authorized-approver anchor exists yet (AUTHORIZED_CANONICAL_APPROVERS "
                "is the PR-2 hard prerequisite); nothing may claim verified authority."
            )

        return self

    def compute_hash(self) -> str:
        """Deterministic hash of the approval record (excludes ``approved_at``)."""
        hash_input = {
            "approval_record_id": self.approval_record_id,
            "canonical_process_id": self.canonical_process_id,
            "canonical_process_version": self.canonical_process_version,
            "governed_approval_event_id": self.governed_approval_event_id,
            "approval_rule_id": self.approval_rule_id,
            "source_geometry_id": self.source_geometry_id,
            "source_geometry_role": self.source_geometry_role,
            "source_authority_state": self.source_authority_state,
            "output_geometry_id": self.output_geometry_id,
            "decision": self.decision,
            "approver_id": self.approver_id,
            "approver_role": self.approver_role,
            "provenance_hash": self.provenance_hash,
            "process_inputs_hash": self.process_inputs_hash,
            "authentication": self.authentication,
        }
        canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def process_covers_source_case(
    canonical_process_id: str,
    canonical_process_version: str,
    source_geometry_role: str,
) -> bool:
    """
    True if the given approved canonical process/version is registered as
    covering the given source-geometry role.
    """
    covered = APPROVED_CANONICAL_PROCESSES.get(
        (canonical_process_id, canonical_process_version)
    )
    if covered is None:
        return False
    return source_geometry_role.strip().lower() in covered


def is_registered_canonical_process(
    canonical_process_id: str,
    canonical_process_version: str,
) -> bool:
    """True when the process id/version pair exists in the approved registry."""
    return (
        canonical_process_id.strip(),
        canonical_process_version.strip(),
    ) in APPROVED_CANONICAL_PROCESSES


def validate_canonical_process_approval_record(
    record: CanonicalProcessApprovalRecord,
) -> Tuple[bool, Optional[str]]:
    """
    Policy-level validation of a structurally-valid approval record.

    Returns ``(is_valid, reason)``. The key policy check: the record must
    represent an output of an *approved* canonical process that is registered
    to cover this source case. An uncovered case is a "process extension
    required" outcome — never an artifact-specific exception.
    """
    if not process_covers_source_case(
        record.canonical_process_id,
        record.canonical_process_version,
        record.source_geometry_role,
    ):
        return False, (
            "process extension required: canonical process "
            f"'{record.canonical_process_id}' version "
            f"'{record.canonical_process_version}' is not approved to cover source "
            f"role '{record.source_geometry_role}'. Extend and re-approve the "
            "canonical process; do not grant an artifact-specific exception."
        )
    return True, None


def derive_governed_approval_event_id(
    approver_id: str,
    canonical_process_id: str,
    source_geometry_id: str,
    process_inputs_hash: str,
) -> str:
    """
    Produce a governed approval event id SERVER-SIDE (C2 PR 1 — gap-1 lock).

    The event id is NOT accepted from the caller. It is derived from a governed
    ``ReviewEnforcement`` review that this function runs: the approval is routed
    through ``record_review(..., APPROVE)``, which REFUSES a ``system:`` actor
    (raising ``ReviewBypassAttemptError``) — so no machine actor can manufacture
    a governed approval event, and no caller can assert a pre-chosen event id.
    The id is the sha256 of the resulting human-APPROVE ``ReviewRecord`` bound to
    the process/source/inputs, so it cannot be forged or replayed with different
    content.

    NOTE (PR-1 scope): this closes the *fabrication* vector (an id can no longer
    be supplied). It does NOT verify the approver is *authorized* to approve
    canonical geometry — that authorization anchor (AUTHORIZED_CANONICAL_APPROVERS)
    is the PR-2 HARD PREREQUISITE. Every event produced here therefore backs only
    an ``unverified_pending_governance`` approval; PR-2 slots the authorization
    check into exactly this seam.
    """
    enforcement = ReviewEnforcement()
    try:
        review = enforcement.record_review(
            reviewer_id=approver_id,
            decision=ReviewDecision.APPROVE,
            review_context={
                "canonical_process_id": canonical_process_id,
                "source_geometry_id": source_geometry_id,
            },
        )
    except ReviewBypassAttemptError as exc:
        # system: actor tried to APPROVE — cannot produce a governed event.
        raise CanonicalProcessApprovalError(
            f"governed approval event cannot be produced for approver "
            f"'{approver_id}': {exc}"
        ) from exc

    if not (
        enforcement.review_completed
        and enforcement.review_decision == ReviewDecision.APPROVE
        and review.is_human()
    ):
        raise CanonicalProcessApprovalError(
            "governed approval event requires a completed human APPROVE review; "
            f"approver '{approver_id}' did not produce one"
        )

    seed = "|".join(
        [
            review.reviewer_id,
            review.decision.value,
            review.timestamp.isoformat(),
            canonical_process_id,
            source_geometry_id,
            process_inputs_hash,
        ]
    )
    return "gae-" + hashlib.sha256(seed.encode()).hexdigest()[:16]


def create_canonical_process_approval_record(
    canonical_process_id: str,
    canonical_process_version: str,
    approval_rule_id: str,
    source_geometry_id: str,
    provenance_hash: str,
    process_inputs_hash: str,
    approver_id: str,
    source_geometry_role: str = "evidence",
    source_authority_state: str = "governed_evidence_candidate",
    approver_role: str = "reviewer",
    output_geometry_id: Optional[str] = None,
    notes: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> CanonicalProcessApprovalRecord:
    """
    Create a governed canonical-process approval record.

    The ``governed_approval_event_id`` is DERIVED SERVER-SIDE (see
    ``derive_governed_approval_event_id``) and cannot be supplied by the caller —
    this closes the fabrication vector where a plausible client-supplied event id
    was accepted as proof a governed approval occurred. The record is stamped
    ``authentication='unverified_pending_governance'`` (fail-safe default; no
    verified path exists in PR-1).

    Raises ``CanonicalProcessApprovalError`` if the approver cannot produce a
    governed approval event (e.g. a ``system:`` actor), if the record is
    structurally invalid (missing identity/provenance, format-derived authority
    state), or if the process is not approved to cover the source case (process
    extension required).
    """
    governed_approval_event_id = derive_governed_approval_event_id(
        approver_id=approver_id,
        canonical_process_id=canonical_process_id,
        source_geometry_id=source_geometry_id,
        process_inputs_hash=process_inputs_hash,
    )

    try:
        record = CanonicalProcessApprovalRecord(
            canonical_process_id=canonical_process_id,
            canonical_process_version=canonical_process_version,
            governed_approval_event_id=governed_approval_event_id,
            approval_rule_id=approval_rule_id,
            source_geometry_id=source_geometry_id,
            source_geometry_role=source_geometry_role,
            source_authority_state=source_authority_state,
            output_geometry_id=output_geometry_id,
            decision="approve",
            approver_id=approver_id,
            approver_role=approver_role,
            provenance_hash=provenance_hash,
            process_inputs_hash=process_inputs_hash,
            authentication=UNVERIFIED_PENDING_GOVERNANCE,
            notes=notes,
            metadata=metadata or {},
        )
    except ValueError as exc:
        raise CanonicalProcessApprovalError(str(exc)) from exc

    is_valid, reason = validate_canonical_process_approval_record(record)
    if not is_valid:
        raise CanonicalProcessApprovalError(reason or "invalid canonical process approval")

    record.deterministic_approval_hash = record.compute_hash()
    return record
