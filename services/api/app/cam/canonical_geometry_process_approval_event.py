"""
Canonical Geometry Process Approval — Governed Event Derivation

Server-side derivation of the governed approval event id for C2 process-exclusive
canonical geometry authority (PR 1 — gap-1 lock). This is split out of
``canonical_geometry_process_approval.py`` to keep that module within the
file-size budget; the approval-record module re-exports
``CanonicalProcessApprovalError`` and ``derive_governed_approval_event_id`` from
here, so importers of the approval module are unaffected.

The event id is NOT accepted from the caller — it is derived from a governed
``ReviewEnforcement`` review that refuses ``system:`` actors — which is why this
concern (the review-enforcement bridge) is cohesive enough to live on its own.
"""

from __future__ import annotations

from app.cam.canonical_geometry_process_policy import (
    compute_governed_approval_event_id,
)
from app.governance.review_enforcement import (
    ReviewBypassAttemptError,
    ReviewDecision,
    ReviewEnforcement,
)


class CanonicalProcessApprovalError(Exception):
    """
    Raised when a canonical process approval record cannot be created or is
    invalid. The message names the required corrective path — in particular,
    uncovered source cases must be resolved by *process extension*, never by an
    artifact-specific exception.
    """


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

    NOTE: this closes the *fabrication* vector (an id can no longer be supplied)
    and rejects ``system:`` actors, but it does NOT itself decide whether the
    approver is *authorized*. Authorization is applied ONCE by
    ``create_canonical_process_approval_record`` via
    ``is_authorized_canonical_approver`` (the AUTHORIZED_CANONICAL_APPROVERS
    anchor), which stamps ``verified_governed_process`` only for an allowlisted
    approver and otherwise preserves the ``unverified_pending_governance`` baseline.
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
