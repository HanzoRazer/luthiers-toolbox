"""
Canonical Geometry Process Approval

C2 geometry-origin closure (PR 1 of the process-exclusive dev order).

Keystone ruling being operationalized (RATIFIED 2026-07-04 — see ratification note below):

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
RATIFICATION STATUS: RATIFIED by the repo owner (Ross Echols / HanzoRazer),
2026-07-04.

The keystone ruling wording above and the canonical-process vocabulary below are
hereby ratified as the governing C2 process-exclusive canonical-authority wording:

    canonical_process_id      = "body-geometry-canonicalization"
    canonical_process_version = "v1"
    approval_rule_id          = "c2-process-exclusive-canonical-authority-v1"

SCOPE OF THIS RATIFICATION — READ BEFORE EXTENDING. This ratifies the RULING and
its vocabulary as the working canonical identifiers. It does NOT create the
authorization anchor (AUTHORIZED_CANONICAL_APPROVERS — *who* may approve), which
remains the PR-2 HARD PREREQUISITE. Therefore the ``authentication`` fail-safe is
UNCHANGED and MUST stay so until PR-2: every approval minted here remains
``unverified_pending_governance``. Ratifying the wording is not authorizing
approvers, and this module still mints nothing that may be treated as verified
canonical authority. (Constant identifiers retain the ``PROPOSED_`` prefix for
now; dropping it is optional follow-up, not required by ratification.)
------------------------------------------------------------------------------
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.cam.canonical_geometry_process_policy import (
    ALLOWED_AUTHENTICATION_STATES,
    PROPOSED_APPROVAL_RULE_ID,
    PROPOSED_CANONICAL_PROCESS_ID,
    PROPOSED_CANONICAL_PROCESS_VERSION,
    UNVERIFIED_PENDING_GOVERNANCE,
    authority_state_is_representation_derived,
    compute_governed_approval_event_id,
    is_registered_canonical_process,
    is_system_actor,
    process_covers_source_case,
)
from app.governance.review_enforcement import (
    ReviewBypassAttemptError,
    ReviewDecision,
    ReviewEnforcement,
)


# Proposed vocabulary, process coverage, representation-token detection, and
# PR-1 authenticity constants live in canonical_geometry_process_policy.py.
class CanonicalProcessApprovalError(Exception):
    """
    Raised when a canonical process approval record cannot be created or is
    invalid. The message names the required corrective path — in particular,
    uncovered source cases must be resolved by *process extension*, never by an
    artifact-specific exception.
    """


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

    canonical_process_id: str = Field(..., description="Approved canonical process ID")
    canonical_process_version: str = Field(..., description="Canonical process version")
    governed_approval_event_id: str = Field(..., description="Governed approval event ID")
    approval_rule_id: str = Field(..., description="Approval rule ID")

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

    output_geometry_id: Optional[str] = Field(default=None, description="Process-output geometry ID")

    decision: Literal["approve"] = Field(default="approve", description="Approval decision")

    approver_id: str = Field(
        ..., description="Actor who participated in the governed approval (human:<id>)"
    )
    approver_role: str = Field(default="reviewer", description="Approver process role")

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

    deterministic_approval_hash: str = Field(default="", description="Approval content hash")

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

        if is_system_actor(self.approver_id):
            raise ValueError(
                f"System actor '{self.approver_id}' may not approve process output — "
                "a machine actor id alone never confers canonical authority"
            )

        if authority_state_is_representation_derived(self.source_authority_state):
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
        if self.authentication not in ALLOWED_AUTHENTICATION_STATES:
            raise ValueError(
                f"authentication '{self.authentication}' is not permitted in PR-1; "
                f"the only legal value is '{UNVERIFIED_PENDING_GOVERNANCE}'. No "
                "authorized-approver anchor exists yet (AUTHORIZED_CANONICAL_APPROVERS "
                "is the PR-2 hard prerequisite); nothing may claim verified authority."
            )

        expected_event_id = compute_governed_approval_event_id(
            approver_id=self.approver_id,
            canonical_process_id=self.canonical_process_id,
            canonical_process_version=self.canonical_process_version,
            approval_rule_id=self.approval_rule_id,
            source_geometry_id=self.source_geometry_id,
            provenance_hash=self.provenance_hash,
            process_inputs_hash=self.process_inputs_hash,
            decision=self.decision,
        )
        if self.governed_approval_event_id != expected_event_id:
            raise ValueError(
                "governed_approval_event_id must match the deterministic "
                "server-derived approval identity; direct construction is allowed "
                "only for rehydrating records whose id matches their process, "
                "source, provenance, inputs, approver, and decision."
            )

        if (
            self.deterministic_approval_hash
            and self.deterministic_approval_hash != self.compute_hash()
        ):
            raise ValueError(
                "deterministic_approval_hash must match approval record content; "
                "stale or caller-supplied approval hashes cannot back canonical "
                "authority."
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
    expected_event_id = compute_governed_approval_event_id(
        approver_id=record.approver_id,
        canonical_process_id=record.canonical_process_id,
        canonical_process_version=record.canonical_process_version,
        approval_rule_id=record.approval_rule_id,
        source_geometry_id=record.source_geometry_id,
        provenance_hash=record.provenance_hash,
        process_inputs_hash=record.process_inputs_hash,
        decision=record.decision,
    )
    if record.governed_approval_event_id != expected_event_id:
        return False, (
            "governed approval event id does not match the deterministic "
            "server-derived approval identity; construct new approval records "
            "through create_canonical_process_approval_record() or rehydrate only "
            "records whose governed_approval_event_id matches their process, "
            "source, provenance, inputs, approver, and decision."
        )
    expected_hash = record.compute_hash()
    if (
        record.deterministic_approval_hash
        and record.deterministic_approval_hash != expected_hash
    ):
        return False, (
            "deterministic approval hash does not match approval record content; "
            "stale or caller-supplied approval hashes cannot back canonical "
            "authority."
        )
    return True, None


def derive_governed_approval_event_id(
    approver_id: str,
    canonical_process_id: str,
    canonical_process_version: str,
    approval_rule_id: str,
    source_geometry_id: str,
    provenance_hash: str,
    process_inputs_hash: str,
) -> str:
    """
    Produce a governed approval event id SERVER-SIDE (C2 PR 1 — gap-1 lock).

    The event id is NOT accepted from the caller. It is derived from a governed
    ``ReviewEnforcement`` review that this function runs: the approval is routed
    through ``record_review(..., APPROVE)``, which REFUSES a ``system:`` actor
    (raising ``ReviewBypassAttemptError``) — so no machine actor can manufacture
    a governed approval event, and no caller can assert a pre-chosen event id.
    The id is deterministic over the logical approval identity (approver,
    process id/version, rule, source, provenance, and process inputs), so retries
    of the same request reconcile to the same id while changed content cannot
    replay the id.

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

    return compute_governed_approval_event_id(
        approver_id=review.reviewer_id,
        canonical_process_id=canonical_process_id,
        canonical_process_version=canonical_process_version,
        approval_rule_id=approval_rule_id,
        source_geometry_id=source_geometry_id,
        provenance_hash=provenance_hash,
        process_inputs_hash=process_inputs_hash,
        decision=review.decision.value,
    )


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
        canonical_process_version=canonical_process_version,
        approval_rule_id=approval_rule_id,
        source_geometry_id=source_geometry_id,
        provenance_hash=provenance_hash,
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
