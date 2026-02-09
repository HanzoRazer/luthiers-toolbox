"""
Saw Lab Batch Learning Router

Learning event endpoints extracted from batch_router.py:
  - Learning event listing & approval
  - Learning overrides resolve & apply
  - Apply flag status
  - Executions with learning info

Mounted at: /api/saw/batch
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.saw_lab.store import (
    get_artifact,
    query_all_accepted_learning_events,
    query_executions_with_learning,
    query_learning_events_by_execution,
)

router = APIRouter(prefix="/api/saw/batch", tags=["saw", "batch"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_truthy(value: str) -> bool:
    """Check if env var value is truthy (1, true, yes, y, on)."""
    return value.lower() in ("1", "true", "yes", "y", "on")


# ---------------------------------------------------------------------------
# Learning Events Endpoints
# ---------------------------------------------------------------------------


@router.get("/learning-events/by-execution")
def list_learning_events_by_execution(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
) -> List[Dict[str, Any]]:
    """
    List learning event artifacts for a given execution.
    """
    events = query_learning_events_by_execution(batch_execution_artifact_id)[:limit]

    results = []
    for ev in events:
        payload = ev.get("payload", {})
        results.append(
            {
                "artifact_id": ev.get("artifact_id"),
                "id": ev.get("artifact_id"),
                "kind": "saw_lab_learning_event",  # Use saw_lab_ prefix for consistency
                "status": ev.get("status", "OK"),
                "created_utc": ev.get("created_utc"),
                "suggestion_type": payload.get("suggestion_type"),
                "policy_decision": payload.get("policy_decision"),
                "payload": payload,
            }
        )

    return results


@router.post("/learning-events/approve")
def approve_learning_event(
    learning_event_artifact_id: str = Query(
        ..., description="Learning event artifact ID"
    ),
    policy_decision: str = Query(..., description="Policy decision (ACCEPT or REJECT)"),
    approved_by: str = Query(..., description="Approver name"),
    reason: str = Query("", description="Reason for decision"),
) -> Dict[str, Any]:
    """
    Approve or reject a learning event.

    Updates the learning event's policy_decision field.
    """
    event = get_artifact(learning_event_artifact_id)
    if not event:
        raise HTTPException(status_code=404, detail="Learning event not found")

    # Update the event payload with the decision
    payload = event.get("payload", {})
    payload["policy_decision"] = policy_decision.upper()
    payload["approved_by"] = approved_by
    payload["approval_reason"] = reason

    # Update in store (in-memory update)
    event["payload"] = payload

    return {
        "artifact_id": learning_event_artifact_id,
        "policy_decision": policy_decision.upper(),
        "approved_by": approved_by,
    }


# ---------------------------------------------------------------------------
# Learning Overrides Endpoints
# ---------------------------------------------------------------------------


@router.get("/learning-overrides/apply/status")
def get_apply_flag_status() -> Dict[str, Any]:
    """
    Get the current status of the SAW_LAB_APPLY_ACCEPTED_OVERRIDES flag.

    Returns the flag value as a boolean.
    """
    raw_value = os.getenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", "")
    is_enabled = _is_truthy(raw_value)

    return {
        "SAW_LAB_APPLY_ACCEPTED_OVERRIDES": is_enabled,
    }


@router.get("/learning-overrides/resolve")
def resolve_learning_overrides(
    limit_events: int = Query(200, ge=1, le=1000, description="Max events to consider"),
) -> Dict[str, Any]:
    """
    Resolve accumulated learning overrides from all accepted events.

    Returns multipliers for spindle_rpm, feed_rate, doc based on accepted suggestions.
    """
    accepted = query_all_accepted_learning_events(limit=limit_events)

    # Default multipliers
    spindle_rpm_mult = 1.0
    feed_rate_mult = 1.0
    doc_mult = 1.0

    # Apply multipliers from accepted events
    for event in accepted:
        payload = event.get("payload", {})
        suggestion_type = payload.get("suggestion_type", "")
        trigger = payload.get("trigger", {})

        if trigger.get("burn"):
            # burn => reduce RPM, increase feed
            spindle_rpm_mult *= 0.9
            feed_rate_mult *= 1.05
        elif trigger.get("tearout"):
            # tearout => reduce DOC
            doc_mult *= 0.85
        elif trigger.get("kickback"):
            # kickback => reduce RPM
            spindle_rpm_mult *= 0.85

    return {
        "resolved": {
            "spindle_rpm_mult": round(spindle_rpm_mult, 4),
            "feed_rate_mult": round(feed_rate_mult, 4),
            "doc_mult": round(doc_mult, 4),
        },
        "source_count": len(accepted),
    }


@router.post("/learning-overrides/apply")
def apply_learning_overrides(
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply resolved learning overrides to a context.

    Takes spindle_rpm, feed_rate, doc_mm and returns tuned values.
    """
    apply_enabled = _is_truthy(os.getenv("SAW_LAB_APPLY_ACCEPTED_OVERRIDES", ""))

    # Get resolved multipliers
    accepted = query_all_accepted_learning_events(limit=200)

    spindle_rpm_mult = 1.0
    feed_rate_mult = 1.0
    doc_mult = 1.0

    for event in accepted:
        payload = event.get("payload", {})
        trigger = payload.get("trigger", {})

        if trigger.get("burn"):
            spindle_rpm_mult *= 0.9
            feed_rate_mult *= 1.05
        elif trigger.get("tearout"):
            doc_mult *= 0.85
        elif trigger.get("kickback"):
            spindle_rpm_mult *= 0.85

    # Extract original values
    orig_rpm = context.get("spindle_rpm", 0)
    orig_feed = context.get("feed_rate", 0)
    orig_doc = context.get("doc_mm", 0)

    # Apply multipliers
    tuned_rpm = round(orig_rpm * spindle_rpm_mult, 2)
    tuned_feed = round(orig_feed * feed_rate_mult, 2)
    tuned_doc = round(orig_doc * doc_mult, 2)

    tuned_context = {
        "spindle_rpm": tuned_rpm,
        "feed_rate": tuned_feed,
        "doc_mm": tuned_doc,
    }

    return {
        "apply_enabled": apply_enabled,
        "resolved": {
            "spindle_rpm_mult": round(spindle_rpm_mult, 4),
            "feed_rate_mult": round(feed_rate_mult, 4),
            "doc_mult": round(doc_mult, 4),
        },
        "tuning_stamp": {
            "applied": apply_enabled,
            "before": {
                "spindle_rpm": orig_rpm,
                "feed_rate": orig_feed,
                "doc_mm": orig_doc,
            },
            "after": {
                "spindle_rpm": tuned_rpm,
                "feed_rate": tuned_feed,
                "doc_mm": tuned_doc,
            },
            "multipliers": {
                "spindle_rpm_mult": round(spindle_rpm_mult, 4),
                "feed_rate_mult": round(feed_rate_mult, 4),
                "doc_mult": round(doc_mult, 4),
            },
        },
        "tuned_context": tuned_context,
    }


# ---------------------------------------------------------------------------
# Executions with Learning Info
# ---------------------------------------------------------------------------


@router.get("/executions/with-learning")
def list_executions_with_learning(
    only_applied: str = Query(
        "false", description="Filter to only executions with learning applied"
    ),
    batch_label: Optional[str] = Query(None, description="Filter by batch label"),
) -> List[Dict[str, Any]]:
    """
    List execution artifacts with learning info.

    If only_applied=true, only returns executions where learning was actually applied.
    """
    only_applied_bool = only_applied.lower() in ("true", "1", "yes")
    results = query_executions_with_learning(
        batch_label=batch_label, only_applied=only_applied_bool
    )

    return [
        {
            "artifact_id": art.get("artifact_id"),
            "id": art.get("artifact_id"),
            "kind": art.get("kind"),
            "status": art.get("status"),
            "created_utc": art.get("created_utc"),
            "batch_label": art.get("payload", {}).get("batch_label"),
            "session_id": art.get("payload", {}).get("session_id"),
            "learning": art.get("payload", {}).get("learning", {}),
        }
        for art in results
    ]
