"""
Plan Choose Service

Provides helpers for finding operator overrides (plan-choose artifacts).
An operator can CHOOSE a specific tuning decision to apply, or CLEAR any override.

Used by batch_router.py to determine whether an override is active.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _get_items(res: Any) -> List[Dict[str, Any]]:
    """Extract items list from various response shapes."""
    if isinstance(res, dict):
        items = res.get("items") or res.get("runs") or res.get("artifacts") or []
        return items if isinstance(items, list) else []
    return res if isinstance(res, list) else []


def find_latest_plan_choose(
    *,
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
) -> Optional[Dict[str, Any]]:
    """
    Find the most recent plan-choose artifact for a context.

    Plan-choose artifacts track operator overrides:
    - state="CHOSEN": Operator selected a specific tuning decision
    - state="CLEARED": Operator explicitly cleared any override

    Returns the full artifact dict or None if not found.
    """
    try:
        from app.rmos.runs_v2 import store as runs_store

        res = runs_store.list_runs_filtered(
            kind="saw_batch_plan_choose",
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

            # Match context (session_id, batch_label, tool_kind)
            # Allow match if meta exists and contains matching values,
            # or if payload contains matching values
            meta_session = meta.get("session_id") if isinstance(meta, dict) else None
            meta_batch = meta.get("batch_label") if isinstance(meta, dict) else None
            meta_tool = meta.get("tool_kind") if isinstance(meta, dict) else None

            payload_session = payload.get("session_id")
            payload_batch = payload.get("batch_label")
            payload_tool = payload.get("tool_kind")

            # Match session_id
            if session_id and meta_session and meta_session != session_id:
                if payload_session and payload_session != session_id:
                    continue

            # Match batch_label
            if batch_label and meta_batch and meta_batch != batch_label:
                if payload_batch and payload_batch != batch_label:
                    continue

            # Match tool_kind
            if tool_kind and meta_tool and meta_tool != tool_kind:
                if payload_tool and payload_tool != tool_kind:
                    continue

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
        return candidates[0]

    except (ImportError, KeyError, ValueError, TypeError, AttributeError, IndexError):  # WP-1: narrowed from except Exception
        return None
