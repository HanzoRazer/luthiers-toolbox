"""
Canonical geometry process policy helpers.

C2 PR-1 keeps the process vocabulary, coverage registry, and governed approval
event identity separate from the approval-record model so the model module stays
small and the ratified governance vocabulary is easy to extend or supersede.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Dict, Optional, Tuple


# Ratified vocabulary (repo owner, 2026-07-04) — governing C2 canonical-process
# names. Identifier names retain the PROPOSED_ prefix for now; dropping it is
# optional follow-up, not required by ratification.
PROPOSED_CANONICAL_PROCESS_ID = "body-geometry-canonicalization"
PROPOSED_CANONICAL_PROCESS_VERSION = "v1"
PROPOSED_APPROVAL_RULE_ID = "c2-process-exclusive-canonical-authority-v1"

# Authenticity status.
#   UNVERIFIED_PENDING_GOVERNANCE — fail-safe default: a governed approval whose
#     approver is not (yet) on the ratified authorization anchor. This remains
#     the baseline/transition state and is NOT a warning by itself.
#   VERIFIED_GOVERNED_PROCESS — a governed approval by an approver authorized for
#     the canonical process/version/rule via AUTHORIZED_CANONICAL_APPROVERS.
UNVERIFIED_PENDING_GOVERNANCE = "unverified_pending_governance"
VERIFIED_GOVERNED_PROCESS = "verified_governed_process"
ALLOWED_AUTHENTICATION_STATES = frozenset(
    {UNVERIFIED_PENDING_GOVERNANCE, VERIFIED_GOVERNED_PROCESS}
)


# Registry of approved canonical processes -> the source-geometry roles that
# each process/version is approved to cover. This registry is deliberately small
# and RATIFIED (2026-07-04); legitimate uncovered cases require process extension.
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


def is_system_actor(actor_id: str) -> bool:
    """True when an actor id is a machine actor under repo convention."""
    return actor_id.strip().lower().startswith("system:")


def authority_state_is_representation_derived(state: str) -> bool:
    """True when authority state appears inferred from format/route/storage."""
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


def process_covers_source_case(
    canonical_process_id: str,
    canonical_process_version: str,
    source_geometry_role: str,
) -> bool:
    """True when a process/version is registered to cover a source role."""
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
    """True when the process id/version pair exists in the proposed registry."""
    return (
        canonical_process_id.strip(),
        canonical_process_version.strip(),
    ) in APPROVED_CANONICAL_PROCESSES


# ---------------------------------------------------------------------------
# Authorization anchor — WHO may turn a governed process approval into VERIFIED
# canonical authority (AUTHORIZED_CANONICAL_APPROVERS).
# ---------------------------------------------------------------------------
# Keyed by (canonical_process_id, canonical_process_version) -> approval_rule_id
# -> {"roles": <allowed approver roles>, "approvers": <allowed approver ids>}.
#
# RATIFICATION: this anchor ships EMPTY and FAIL-CLOSED. The process/version/rule
# and its allowed roles are declared so the shape is reviewable, but the approver
# id allowlist is EMPTY — so NOTHING mints VERIFIED_GOVERNED_PROCESS until a
# SEPARATE repo-owner-ratified commit adds the first approver id. A missing anchor
# entry, an unknown rule, a role mismatch, or an approver id absent from the
# allowlist all fail closed to UNVERIFIED_PENDING_GOVERNANCE. Keyed on the ratified
# constants (no forked literals); the rule is the ratified PROPOSED_APPROVAL_RULE_ID.
AUTHORIZED_CANONICAL_APPROVERS: Dict[Tuple[str, str], Dict[str, Dict[str, frozenset]]] = {
    (PROPOSED_CANONICAL_PROCESS_ID, PROPOSED_CANONICAL_PROCESS_VERSION): {
        PROPOSED_APPROVAL_RULE_ID: {
            "roles": frozenset({"reviewer", "owner"}),
            "approvers": frozenset(),  # EMPTY — fail-closed until owner ratifies
        },
    },
}


def is_authorized_canonical_approver(
    *,
    canonical_process_id: str,
    canonical_process_version: str,
    approval_rule_id: str,
    approver_id: str,
    approver_role: str,
) -> Tuple[bool, Optional[str]]:
    """
    Decide whether an approver is authorized to mint VERIFIED canonical authority
    for a canonical process/version under a given approval rule.

    Returns ``(is_authorized, reason)``. Fail-closed: any lookup miss, role
    mismatch, or absent approver id returns ``(False, reason)`` so an unconfigured
    or unmatched approver can never silently produce verified authority. A
    ``system:`` actor is never authorized regardless of the allowlist.

    Authorization requires BOTH an allowed role AND an explicit approver-id
    allowlist match — a role alone is never sufficient (a human actor id alone is
    not authority).
    """
    if is_system_actor(approver_id):
        return False, (
            f"approver '{approver_id}' is a system actor and can never hold "
            "canonical approval authority"
        )

    rules = AUTHORIZED_CANONICAL_APPROVERS.get(
        (canonical_process_id.strip(), canonical_process_version.strip())
    )
    if not rules:
        return False, (
            "no canonical approval authorization anchor for process "
            f"'{canonical_process_id}' version '{canonical_process_version}'; "
            "approval remains unverified_pending_governance"
        )

    rule = rules.get(approval_rule_id.strip())
    if not rule:
        return False, (
            f"approval rule '{approval_rule_id}' is not anchored for process "
            f"'{canonical_process_id}' version '{canonical_process_version}'; "
            "approval remains unverified_pending_governance"
        )

    allowed_roles = {r.strip().lower() for r in rule.get("roles", frozenset())}
    if approver_role.strip().lower() not in allowed_roles:
        return False, (
            f"approver role '{approver_role}' is not authorized for rule "
            f"'{approval_rule_id}'; approval remains unverified_pending_governance"
        )

    if approver_id.strip() not in rule.get("approvers", frozenset()):
        return False, (
            f"approver '{approver_id}' is not on the ratified allowlist for rule "
            f"'{approval_rule_id}'; approval remains unverified_pending_governance"
        )

    return True, None


def compute_governed_approval_event_id(
    *,
    approver_id: str,
    canonical_process_id: str,
    canonical_process_version: str,
    approval_rule_id: str,
    source_geometry_id: str,
    provenance_hash: str,
    process_inputs_hash: str,
    decision: str = "approve",
) -> str:
    """
    Deterministic event id for a logical canonical-process approval.

    Runtime timestamp and storage identity are deliberately excluded so retries
    of the same approval reconcile, while changed approval content cannot replay
    the id.
    """
    seed_payload = {
        "approver_id": approver_id,
        "decision": decision,
        "canonical_process_id": canonical_process_id,
        "canonical_process_version": canonical_process_version,
        "approval_rule_id": approval_rule_id,
        "source_geometry_id": source_geometry_id,
        "provenance_hash": provenance_hash,
        "process_inputs_hash": process_inputs_hash,
    }
    canonical = json.dumps(seed_payload, sort_keys=True, separators=(",", ":"))
    return "gae-" + hashlib.sha256(canonical.encode()).hexdigest()[:16]
