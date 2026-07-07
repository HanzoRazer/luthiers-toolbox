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
its vocabulary as the working canonical identifiers. The authorization anchor
(AUTHORIZED_CANONICAL_APPROVERS — *who* may approve) now EXISTS in
``canonical_geometry_process_policy.py`` but ships EMPTY and FAIL-CLOSED: it
declares the ratified process/version/rule and its allowed roles, yet carries NO
approver ids. Therefore the ``authentication`` fail-safe is behaviourally
UNCHANGED — with an empty allowlist every approval minted here still resolves to
``unverified_pending_governance``. Adding the first approver id (which unlocks
``verified_governed_process``) is a SEPARATE repo-owner-ratified commit, not this
one. (Constant identifiers retain the ``PROPOSED_`` prefix for now; dropping it is
optional follow-up, not required by ratification.)
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
    VERIFIED_GOVERNED_PROCESS,
    authority_state_is_representation_derived,
    compute_governed_approval_event_id,
    is_authorized_canonical_approver,
    is_registered_canonical_process,
    is_system_actor,
    process_covers_source_case,
)

# The governed-event derivation and the CanonicalProcessApprovalError are split
# into a sibling module to keep this file within the file-size budget; they are
# re-exported here so importers of this module are unaffected. (Proposed
# vocabulary, process coverage, representation-token detection, and PR-1
# authenticity constants live in canonical_geometry_process_policy.py.)
from app.cam.canonical_geometry_process_approval_event import (
    CanonicalProcessApprovalError,
    derive_governed_approval_event_id,
)

__all__ = [
    "CanonicalProcessApprovalError",
    "CanonicalProcessApprovalRecord",
    "derive_governed_approval_event_id",
    "validate_canonical_process_approval_record",
    "create_canonical_process_approval_record",
]


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
            "Authenticity status of this approval. Fail-safe default: "
            "'unverified_pending_governance'. 'verified_governed_process' is legal "
            "ONLY when this record's approver clears the AUTHORIZED_CANONICAL_APPROVERS "
            "anchor — the model validator re-checks authorization for the verified "
            "state, so it can neither be hand-set nor rehydrated for an unauthorized "
            "approver. The anchor ships EMPTY (fail-closed), so absent a ratified "
            "approver id every record still resolves to unverified_pending_governance."
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

        # Fail-safe authenticity: only a ratified authentication state is legal.
        # The verified state is minted solely by the authorization anchor
        # (AUTHORIZED_CANONICAL_APPROVERS) at record creation; any other value
        # (e.g. a hand-set 'verified') is refused, so a missing/failed
        # authorization check can never yield verified authority.
        if self.authentication not in ALLOWED_AUTHENTICATION_STATES:
            raise ValueError(
                f"authentication '{self.authentication}' is not a permitted "
                "authenticity state; legal values are "
                f"{sorted(ALLOWED_AUTHENTICATION_STATES)}. The verified state is "
                "minted only by AUTHORIZED_CANONICAL_APPROVERS at record creation; "
                "nothing else may claim verified authority."
            )

        # Provenance-lock the verified state. Membership in the allowed set is not
        # enough: 'verified_governed_process' is legal ONLY when this record's own
        # approver/process/version/rule/role actually clears the authorization
        # anchor. The check is routed through the SAME helper the factory uses to
        # mint, so mint-time and validation-time semantics can never diverge. This
        # binds the strong state to recomputable provenance, so a directly-
        # constructed or rehydrated record cannot assert verified authority the
        # anchor would not grant (fail-closed: an unknown, unmatched, or later-
        # revoked approver is refused rather than trusted).
        if self.authentication == VERIFIED_GOVERNED_PROCESS:
            authorized, authorization_reason = is_authorized_canonical_approver(
                canonical_process_id=self.canonical_process_id,
                canonical_process_version=self.canonical_process_version,
                approval_rule_id=self.approval_rule_id,
                approver_id=self.approver_id,
                approver_role=self.approver_role,
            )
            if not authorized:
                detail = authorization_reason or (
                    "approver is not on the ratified authorization anchor"
                )
                raise ValueError(
                    "authentication 'verified_governed_process' is not authorized "
                    f"for this record: {detail}. The verified state is minted solely "
                    "for an allowlisted approver via AUTHORIZED_CANONICAL_APPROVERS; "
                    "it cannot be hand-set on, or rehydrated into, a record whose "
                    "approver is not authorized."
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
    # Defense-in-depth: the model validator already provenance-locks the verified
    # state at construction, so a record in hand cannot legally carry an
    # unauthorized 'verified_governed_process'. Re-assert it here so the reference-
    # creation gate (create_process_approved_canonical_geometry_reference calls
    # this) stays correct even if the model validator is ever weakened.
    if record.authentication == VERIFIED_GOVERNED_PROCESS:
        authorized, authorization_reason = is_authorized_canonical_approver(
            canonical_process_id=record.canonical_process_id,
            canonical_process_version=record.canonical_process_version,
            approval_rule_id=record.approval_rule_id,
            approver_id=record.approver_id,
            approver_role=record.approver_role,
        )
        if not authorized:
            detail = authorization_reason or (
                "approver is not on the ratified authorization anchor"
            )
            return False, (
                "verified_governed_process authentication is not authorized for this "
                f"record: {detail}; only an allowlisted approver via "
                "AUTHORIZED_CANONICAL_APPROVERS may back verified canonical authority."
            )
    return True, None


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
    was accepted as proof a governed approval occurred.

    Authentication is decided HERE, once, via the authorization anchor
    (``is_authorized_canonical_approver``): an approver on the ratified
    ``AUTHORIZED_CANONICAL_APPROVERS`` allowlist for this process/version/rule and
    role mints ``authentication='verified_governed_process'``; every other case
    (empty/unmatched allowlist) preserves the ``'unverified_pending_governance'``
    fail-safe baseline. The anchor ships EMPTY and fail-closed, so absent a
    ratified approver id this path is behaviour-preserving (all records unverified).

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

    # SINGLE authorization decision — made here, on the approval record. The
    # reference inherits this authentication state; it is never re-decided
    # downstream. Fail-closed: an unconfigured or unmatched approver keeps the
    # UNVERIFIED_PENDING_GOVERNANCE baseline (a soft outcome, not an error). The
    # unauthorized `reason` is available at this creation seam (approver identity
    # is known here); it is intentionally NOT surfaced as a reference-validation
    # warning, so the ratified baseline stays green.
    authorized, _authorization_reason = is_authorized_canonical_approver(
        canonical_process_id=canonical_process_id,
        canonical_process_version=canonical_process_version,
        approval_rule_id=approval_rule_id,
        approver_id=approver_id,
        approver_role=approver_role,
    )
    authentication = (
        VERIFIED_GOVERNED_PROCESS if authorized else UNVERIFIED_PENDING_GOVERNANCE
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
            authentication=authentication,
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
