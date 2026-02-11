"""
Shared artifact helper functions for runs_v2 modules.

Consolidates duplicate utility functions from batch_timeline.py and batch_tree.py.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def as_items(res: Any) -> List[Dict[str, Any]]:
    """Normalize store response to list of artifact dicts."""
    if isinstance(res, dict):
        items = res.get("items") or res.get("runs") or res.get("artifacts") or []
        return items if isinstance(items, list) else []
    return res if isinstance(res, list) else []


def get_id(a: Dict[str, Any]) -> Optional[str]:
    """Extract artifact id from artifact dict."""
    v = a.get("id") or a.get("artifact_id")
    return str(v) if v else None


def get_kind(a: Dict[str, Any]) -> str:
    """Extract kind from artifact dict."""
    return str(a.get("kind") or (a.get("index_meta") or {}).get("kind") or "")


def get_created(a: Dict[str, Any]) -> str:
    """Extract created_utc timestamp from artifact."""
    payload = a.get("payload") or a.get("data") or {}
    if isinstance(payload, dict) and isinstance(payload.get("created_utc"), str):
        return payload["created_utc"]
    if isinstance(a.get("created_utc"), str):
        return a["created_utc"]
    return ""


def pick_parent_id(a: Dict[str, Any]) -> Optional[str]:
    """
    Extract parent artifact id from index_meta using typed pointer keys.

    Prefers typed parent pointers, falls back to parent_artifact_id, then legacy keys.
    """
    meta = a.get("index_meta") or {}
    if not isinstance(meta, dict):
        meta = {}

    for k in (
        "parent_batch_execution_artifact_id",
        "parent_batch_toolpaths_artifact_id",
        "parent_batch_decision_artifact_id",
        "parent_batch_plan_artifact_id",
        "parent_batch_spec_artifact_id",
        "parent_artifact_id",
        # observed legacy-ish patterns
        "parent_plan_run_id",
        "parent_run_id",
    ):
        v = meta.get(k)
        if v:
            return str(v)

    # Some artifacts may store parent at top-level
    v2 = a.get("parent_artifact_id") or a.get("parent_id")
    return str(v2) if v2 else None
