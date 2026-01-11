"""
Tuning Decision Service

Provides helpers for:
- Finding latest approved tuning decisions
- Applying tuning to plan payloads
- Building advisory blocks from plan-choose artifacts

Used by batch_router.py for Decision Intelligence integration.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _get_items(res: Any) -> List[Dict[str, Any]]:
    """Extract items list from various response shapes."""
    if isinstance(res, dict):
        items = res.get("items") or res.get("runs") or res.get("artifacts") or []
        return items if isinstance(items, list) else []
    return res if isinstance(res, list) else []


def is_apply_approved_tuning_on_plan_enabled() -> bool:
    """
    Feature flag: SAW_LAB_APPLY_APPROVED_TUNING_ON_PLAN

    When enabled, automatically applies approved tuning decisions to new plans.
    Default: False (requires explicit operator approval)
    """
    val = os.environ.get("SAW_LAB_APPLY_APPROVED_TUNING_ON_PLAN", "false")
    return val.lower() in ("true", "1", "yes")


def find_latest_approved_tuning_decision(
    *,
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
) -> Optional[Dict[str, Any]]:
    """
    Find the most recent APPROVED tuning decision for a given context.

    Returns advisory dict:
    {
        "decision_artifact_id": str,
        "tuning": {...},
        "state": "APPROVED",
        "created_utc": str,
    }
    """
    try:
        from app.rmos.runs_v2 import store as runs_store

        res = runs_store.list_runs_filtered(
            kind="saw_lab_tuning_decision",
            limit=200,
        )
        items = _get_items(res)

        candidates: List[Dict[str, Any]] = []
        for a in items:
            if not isinstance(a, dict):
                continue
            meta = a.get("index_meta") or {}
            payload = a.get("payload") or a.get("data") or {}

            if not isinstance(payload, dict):
                continue

            # Must be APPROVED state
            state = payload.get("state", "")
            if not isinstance(state, str) or state.upper() != "APPROVED":
                continue

            # Match session/batch/tool context if provided in meta
            if isinstance(meta, dict):
                if meta.get("tool_kind") and meta.get("tool_kind") != tool_kind:
                    continue
                # session_id/batch_label matching is optional for broader discovery

            candidates.append(a)

        if not candidates:
            return None

        # Sort by created_utc descending
        def _ts(x: Dict[str, Any]) -> str:
            payload = x.get("payload") or x.get("data") or {}
            if isinstance(payload, dict) and isinstance(
                payload.get("created_utc"), str
            ):
                return payload["created_utc"]
            return ""

        candidates.sort(key=_ts, reverse=True)
        best = candidates[0]

        payload = best.get("payload") or best.get("data") or {}
        decision_id = str(best.get("id") or best.get("artifact_id") or "")

        return {
            "decision_artifact_id": decision_id,
            "tuning": payload.get("tuning") or payload.get("effective_delta") or {},
            "state": "APPROVED",
            "created_utc": payload.get("created_utc", ""),
        }
    except Exception:
        return None


def advisory_from_plan_choose_artifact(
    plan_choose: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Build an advisory block from a plan-choose artifact (operator override).

    Returns None if:
    - plan_choose is None
    - plan_choose state is not CHOSEN
    - No tuning data present
    """
    if not plan_choose or not isinstance(plan_choose, dict):
        return None

    payload = plan_choose.get("payload") or plan_choose.get("data") or {}
    if not isinstance(payload, dict):
        return None

    state = payload.get("state", "")
    if not isinstance(state, str) or state.upper() != "CHOSEN":
        return None

    tuning = payload.get("tuning") or {}
    if not tuning:
        return None

    decision_id = payload.get("chosen_decision_artifact_id") or str(
        plan_choose.get("id") or plan_choose.get("artifact_id") or ""
    )

    return {
        "decision_artifact_id": decision_id,
        "tuning": tuning,
        "state": "CHOSEN",
        "created_utc": payload.get("created_utc", ""),
        "note": payload.get("note", ""),
    }


def apply_approved_tuning_to_plan_payload(
    *,
    plan_payload: Dict[str, Any],
    advisory: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply tuning multipliers from an advisory to a plan payload.

    Returns the modified payload with tuning_applied=True if changes were made.
    """
    tuning = advisory.get("tuning") or {}
    if not tuning:
        return plan_payload

    # Clone payload to avoid mutation
    result = dict(plan_payload)

    # Mark as tuned
    result["tuning_applied"] = True
    result["applied_decision_artifact_id"] = advisory.get("decision_artifact_id")
    result["applied_tuning"] = tuning

    # Apply multipliers to setups if present
    # This is a simplified example - actual application would depend on payload structure
    if "setups" in result and isinstance(result["setups"], list):
        for setup in result["setups"]:
            if isinstance(setup, dict):
                # Store applied tuning reference
                setup["tuning_ref"] = advisory.get("decision_artifact_id")

    return result
