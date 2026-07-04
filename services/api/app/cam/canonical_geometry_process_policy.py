"""
Canonical geometry process policy helpers.

C2 PR-1 keeps the process vocabulary, coverage registry, and governed approval
event identity separate from the approval-record model so the model module stays
small and the proposed governance vocabulary is easy to ratify or replace.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Dict, Tuple


# Proposed placeholder vocabulary (RATIFICATION PENDING - do not treat as final)
PROPOSED_CANONICAL_PROCESS_ID = "body-geometry-canonicalization"
PROPOSED_CANONICAL_PROCESS_VERSION = "v1"
PROPOSED_APPROVAL_RULE_ID = "c2-process-exclusive-canonical-authority-v1"

# Authenticity status (C2 PR 1 - gap-1 "authenticity labeling" closure).
# PR-1 has no authorized-approver anchor, so this is the only legal status.
UNVERIFIED_PENDING_GOVERNANCE = "unverified_pending_governance"
ALLOWED_AUTHENTICATION_STATES = frozenset({UNVERIFIED_PENDING_GOVERNANCE})


# Registry of approved canonical processes -> the source-geometry roles that
# each process/version is approved to cover. This registry is deliberately small
# and PROPOSED; legitimate uncovered cases require process extension.
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
