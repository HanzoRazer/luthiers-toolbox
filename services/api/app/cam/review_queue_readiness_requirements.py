"""
Review queue architecture readiness — canonical requirement registry.

The four requirements below are the **ratified initial production requirement set**.

Authority: owner ruling, ratified from the historical 8F assessment. The ratification
applies to the *requirement set* only — the historical TD-2 implementation shape
(caller-supplied booleans, in-memory assessment registry, ``POST /readiness``) is retired
and must not be reintroduced.

One historical finding was **not** carried forward. 8F recorded a missing-timestamp gap;
that gap has since closed — ``ReviewQueueItem`` now declares ``created_at``. The
requirement is retained so the property stays checked, but it is expected to evaluate
SATISFIED. A requirement set that still described a closed gap would report confidently
wrong results, which is worse than reporting nothing.
"""

from __future__ import annotations

from typing import Tuple

from .review_queue_readiness import (
    ReadinessRequirement,
    ReadinessSeverity,
    VerificationMode,
)

AUTHORITY = "Owner ruling ratified from the historical 8F assessment"

# Evidence kinds. The evidence adapter emits these; requirements match on them.
EVIDENCE_DURABLE_PERSISTENCE = "durable_persistence_adapter"
EVIDENCE_ATTRIBUTABLE_IDENTITY = "attributable_identity_binding"
EVIDENCE_CREATION_TIMESTAMP = "creation_timestamp_field"
EVIDENCE_NOTIFICATION_DELIVERY = "notification_delivery_mechanism"


REQUIREMENTS: Tuple[ReadinessRequirement, ...] = (
    ReadinessRequirement(
        requirement_id="RQR-001-PERSISTENCE",
        title="Review queue survives process restart",
        description=(
            "The review queue must declare a durable persistence adapter. A module-level "
            "in-memory index is not persistence: its contents are lost on restart, so any "
            "review state it holds is not operationally dependable."
        ),
        severity=ReadinessSeverity.BLOCKING,
        evidence_kind=EVIDENCE_DURABLE_PERSISTENCE,
        verification_mode=VerificationMode.STATIC,
        authority_source=AUTHORITY,
    ),
    ReadinessRequirement(
        requirement_id="RQR-002-IDENTITY",
        title="Review actors are authenticated or attributable",
        description=(
            "Review assignment and decisions must bind to an attributable actor. A bare "
            "free-text role string names nobody: it cannot be traced to an account and "
            "provides no provenance for a decision."
        ),
        severity=ReadinessSeverity.BLOCKING,
        evidence_kind=EVIDENCE_ATTRIBUTABLE_IDENTITY,
        verification_mode=VerificationMode.HYBRID,
        authority_source=AUTHORITY,
        runtime_validation_note=(
            "Static inspection can show whether an identity binding is declared. It cannot "
            "show that authentication is enforced on the request path — that requires "
            "runtime evidence."
        ),
    ),
    ReadinessRequirement(
        requirement_id="RQR-003-TIMESTAMPS",
        title="Review records carry creation timestamps",
        description=(
            "Queue items and decision records must declare a creation timestamp, without "
            "which staleness and ordering cannot be computed. NOTE: 8F recorded this as a "
            "gap in 2026-05. It has since closed — this requirement is expected to be "
            "SATISFIED and is retained to keep the property checked, not to re-report a "
            "closed gap."
        ),
        severity=ReadinessSeverity.BLOCKING,
        evidence_kind=EVIDENCE_CREATION_TIMESTAMP,
        verification_mode=VerificationMode.STATIC,
        authority_source=AUTHORITY,
    ),
    ReadinessRequirement(
        requirement_id="RQR-004-NOTIFICATION",
        title="Queue changes are communicated externally",
        description=(
            "The subsystem must declare a notification or delivery mechanism, so a queued "
            "review can reach the person expected to act on it. Without one, the queue is "
            "a passive store that must be polled to be useful."
        ),
        severity=ReadinessSeverity.WARNING,
        evidence_kind=EVIDENCE_NOTIFICATION_DELIVERY,
        verification_mode=VerificationMode.STATIC,
        authority_source=AUTHORITY,
    ),
)


def get_requirements() -> Tuple[ReadinessRequirement, ...]:
    """Return the ratified requirement set.

    Deliberately returns the frozen module constant rather than reading configuration:
    the requirement set is ratified policy, not a runtime input. Nothing a caller supplies
    can add, remove, or weaken a requirement.
    """
    return REQUIREMENTS
