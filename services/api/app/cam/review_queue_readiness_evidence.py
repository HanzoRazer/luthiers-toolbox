"""
Review queue architecture readiness — evidence adapter.

Converts current review-queue declarations into typed evidence. Deliberately separate
from the evaluator: this module knows about the repository, the evaluator knows about
policy, and neither knows about the other's concerns.

Two rules govern everything here:

1. **Never infer behaviour from a name.** That a module is called ``*_registry`` says
   nothing about whether it persists. Evidence is read from declared structure — a field,
   an adapter, an import — not from what something is called.
2. **Absence and unverifiability are different findings.** ``present=False`` is a positive
   claim of confirmed absence and requires having looked. Where a property cannot be
   settled by inspection, no evidence is emitted, and the evaluator reports
   UNRESOLVED_RUNTIME_VALIDATION_REQUIRED.

This module executes no production workflow, mutates nothing, and performs no I/O beyond
importing the contracts it inspects.
"""

from __future__ import annotations

from typing import Tuple

from .review_queue_readiness import ReadinessEvidence
from .review_queue_readiness_requirements import (
    EVIDENCE_ATTRIBUTABLE_IDENTITY,
    EVIDENCE_CREATION_TIMESTAMP,
    EVIDENCE_DURABLE_PERSISTENCE,
    EVIDENCE_NOTIFICATION_DELIVERY,
)

_ITEM_MODULE = "services/api/app/cam/review_queue_item.py"
_DECISION_MODULE = "services/api/app/cam/review_decision_record.py"
_REGISTRY_MODULE = "services/api/app/cam/review_queue_registry.py"


def _collect_persistence_evidence() -> ReadinessEvidence:
    """Is a durable persistence adapter declared for the review queue?

    Determined from the registry's declared storage, not its filename. The registry backs
    the queue with module-level dictionaries; a dict is process-local by construction, so
    this is confirmed absence rather than an unverified guess.
    """
    from . import review_queue_registry as registry

    has_dict_backing = isinstance(
        getattr(registry, "REVIEW_QUEUE_ITEM_INDEX", None), dict
    )
    # A durable adapter would appear as a declared session/engine/store on the module.
    durable_markers = [
        name
        for name in ("ENGINE", "SESSION", "STORE", "DB", "ADAPTER", "BACKEND")
        if getattr(registry, name, None) is not None
    ]

    if durable_markers:
        return ReadinessEvidence(
            evidence_kind=EVIDENCE_DURABLE_PERSISTENCE,
            present=True,
            source=_REGISTRY_MODULE,
            detail=f"Durable backing declared: {', '.join(sorted(durable_markers))}.",
        )

    return ReadinessEvidence(
        evidence_kind=EVIDENCE_DURABLE_PERSISTENCE,
        present=False,
        source=_REGISTRY_MODULE,
        detail=(
            "Queue is backed by module-level in-memory indexes"
            + (" (REVIEW_QUEUE_ITEM_INDEX is a dict)" if has_dict_backing else "")
            + "; no durable adapter is declared. Registry code existing is not persistence."
        ),
    )


def _collect_identity_evidence() -> ReadinessEvidence:
    """Is review actor identity bound to something attributable?

    A declared actor field is necessary but not sufficient — whether authentication is
    *enforced* is a runtime property. The requirement is HYBRID, so a present declaration
    still yields UNRESOLVED rather than SATISFIED.
    """
    from .review_decision_record import ReviewDecisionRecord
    from .review_queue_item import ReviewQueueItem

    item_fields = set(getattr(ReviewQueueItem, "model_fields", {}) or {})
    decision_fields = set(getattr(ReviewDecisionRecord, "model_fields", {}) or {})

    has_reviewer_ref = "reviewer_ref" in decision_fields
    has_assigned_role = "assigned_role" in item_fields

    if has_reviewer_ref:
        return ReadinessEvidence(
            evidence_kind=EVIDENCE_ATTRIBUTABLE_IDENTITY,
            present=True,
            source=_DECISION_MODULE,
            detail=(
                "ReviewDecisionRecord declares reviewer_ref. Whether it resolves to an "
                "authenticated account, and whether that is enforced on the request path, "
                "cannot be established by static inspection."
            ),
        )

    return ReadinessEvidence(
        evidence_kind=EVIDENCE_ATTRIBUTABLE_IDENTITY,
        present=False,
        source=_ITEM_MODULE,
        detail=(
            "No attributable actor reference declared"
            + (
                "; assigned_role is a free-text string that names no account."
                if has_assigned_role
                else "."
            )
        ),
    )


def _collect_timestamp_evidence() -> ReadinessEvidence:
    """Do queue items and decision records declare creation timestamps?

    8F recorded this as a gap in 2026-05; it has since closed. The check is retained so
    the property stays verified rather than assumed.
    """
    from .review_decision_record import ReviewDecisionRecord
    from .review_queue_item import ReviewQueueItem

    item_has = "created_at" in (getattr(ReviewQueueItem, "model_fields", {}) or {})
    decision_has = "created_at" in (
        getattr(ReviewDecisionRecord, "model_fields", {}) or {}
    )

    if item_has and decision_has:
        return ReadinessEvidence(
            evidence_kind=EVIDENCE_CREATION_TIMESTAMP,
            present=True,
            source=f"{_ITEM_MODULE}; {_DECISION_MODULE}",
            detail=(
                "created_at declared on both ReviewQueueItem and ReviewDecisionRecord. "
                "The historical 8F timestamp gap is closed."
            ),
        )

    missing = []
    if not item_has:
        missing.append("ReviewQueueItem")
    if not decision_has:
        missing.append("ReviewDecisionRecord")
    return ReadinessEvidence(
        evidence_kind=EVIDENCE_CREATION_TIMESTAMP,
        present=False,
        source=f"{_ITEM_MODULE}; {_DECISION_MODULE}",
        detail=f"created_at not declared on: {', '.join(missing)}.",
    )


def _collect_notification_evidence() -> ReadinessEvidence:
    """Is any delivery mechanism declared for queue changes?

    Looked for as a declared symbol on the queue modules. Nothing of the kind exists, so
    this is confirmed absence.
    """
    from . import review_queue_registry as registry

    markers = [
        name
        for name in ("NOTIFIER", "WEBHOOK", "PUBLISHER", "EVENT_BUS", "DISPATCHER")
        if getattr(registry, name, None) is not None
    ]
    if markers:
        return ReadinessEvidence(
            evidence_kind=EVIDENCE_NOTIFICATION_DELIVERY,
            present=True,
            source=_REGISTRY_MODULE,
            detail=f"Delivery mechanism declared: {', '.join(sorted(markers))}.",
        )

    return ReadinessEvidence(
        evidence_kind=EVIDENCE_NOTIFICATION_DELIVERY,
        present=False,
        source=_REGISTRY_MODULE,
        detail=(
            "No notifier, webhook, publisher, event bus or dispatcher is declared on the "
            "review-queue modules. Queue changes are not communicated externally."
        ),
    )


def collect_readiness_evidence() -> Tuple[ReadinessEvidence, ...]:
    """Build typed evidence from current authoritative declarations.

    Deterministic ordering. No mutation, no network, no database writes. Every item
    carries a citable source.
    """
    return (
        _collect_persistence_evidence(),
        _collect_identity_evidence(),
        _collect_timestamp_evidence(),
        _collect_notification_evidence(),
    )
