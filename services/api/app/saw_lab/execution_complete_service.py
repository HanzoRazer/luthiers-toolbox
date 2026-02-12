from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


# =============================================================================
# Helpers for execution artifact validation (extracted for consolidation)
# =============================================================================


def extract_parent_id(art: Any) -> Optional[str]:
    """Extract parent artifact id from various artifact formats."""
    pid = getattr(art, "parent_id", None)
    if pid:
        return str(pid)
    if isinstance(art, dict):
        return str(art.get("parent_id") or art.get("parent_artifact_id") or "") or None
    meta = getattr(art, "meta", None)
    if isinstance(meta, dict):
        pid = meta.get("parent_id")
        return str(pid) if pid else None
    return None


def extract_payload(art: Any) -> Dict[str, Any]:
    """Extract payload dict from various artifact formats."""
    p = getattr(art, "payload", None)
    if isinstance(p, dict):
        return p
    if isinstance(art, dict):
        p = art.get("payload") or art.get("data") or {}
        return p if isinstance(p, dict) else {}
    return {}


def extract_created_ts(art: Any) -> Optional[float]:
    """
    Best-effort extraction of a creation timestamp.

    Runtime: RunArtifact Pydantic models expose `created_at_utc: datetime`
    Tests/fixtures may use dicts with various timestamp fields.
    """
    created = getattr(art, "created_at_utc", None)
    if isinstance(created, datetime):
        return created.timestamp()

    if isinstance(art, dict):
        for key in ("created_at_utc", "created_utc", "created_at", "created", "timestamp", "ts"):
            v = art.get(key)
            if v is None:
                continue
            if isinstance(v, datetime):
                return v.timestamp()
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str) and v.strip():
                s = v.strip()
                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                try:
                    return datetime.fromisoformat(s).timestamp()
                except (ValueError, TypeError):
                    continue
    return None


def select_latest_artifact(items: list[Any]) -> Any:
    """
    Select the latest item by created timestamp.

    If timestamps collide (same second), pick the later item by insertion
    order (higher index). If timestamps are missing, fall back to last item.
    """
    if not items:
        raise ValueError("items must be non-empty")

    scored: list[tuple[float, int, Any]] = []
    for idx, it in enumerate(items):
        ts = extract_created_ts(it)
        if ts is None:
            continue
        scored.append((float(int(ts)), idx, it))

    if scored:
        return max(scored, key=lambda t: (t[0], t[1]))[2]

    return items[-1]


def metrics_indicate_work(m: Any) -> bool:
    """Check if metrics dict indicates actual work was done."""
    if not isinstance(m, dict):
        return False
    try:
        parts_ok = int(m.get("parts_ok") or 0)
        parts_scrap = int(m.get("parts_scrap") or 0)
    except (ValueError, TypeError):
        parts_ok, parts_scrap = 0, 0

    def _f(key: str) -> float:
        try:
            return float(m.get(key) or 0.0)
        except (ValueError, TypeError):
            return 0.0

    cut_time_s = _f("cut_time_s")
    total_time_s = _f("total_time_s")

    return (parts_ok + parts_scrap) > 0 or cut_time_s > 0.0 or total_time_s > 0.0


def write_execution_complete_artifact(
    *,
    batch_execution_artifact_id: str,
    session_id: str,
    batch_label: str,
    outcome: str,
    notes: Optional[str] = None,
    operator_id: Optional[str] = None,
    tool_kind: str = "saw",
    checklist: Optional[Dict[str, bool]] = None,
    statistics: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Persist a first-class execution complete artifact.

    Artifact kind:
      - saw_batch_execution_complete

    Parent:
      - batch_execution_artifact_id

    Checklist (optional, all must be True):
      - all_cuts_complete
      - material_removed
      - workpiece_inspected
      - area_cleared
    """
    if not batch_execution_artifact_id:
        raise ValueError("batch_execution_artifact_id required")
    if not session_id:
        raise ValueError("session_id required")
    if not batch_label:
        raise ValueError("batch_label required")
    if not outcome:
        raise ValueError("outcome required")

    # Validate checklist if provided
    if checklist:
        failed = [k for k, v in checklist.items() if v is not True]
        if failed:
            raise ValueError(f"checklist items not satisfied: {failed}")

    payload: Dict[str, Any] = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "session_id": session_id,
        "batch_label": batch_label,
        "outcome": outcome,
        "notes": notes,
        "operator_id": operator_id,
        "state": "COMPLETED",
    }

    if checklist:
        payload["checklist"] = checklist

    if statistics:
        payload["statistics"] = statistics

    from app.rmos.runs_v2.store import store_artifact

    complete_id = store_artifact(
        kind="saw_batch_execution_complete",
        payload=payload,
        parent_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )

    return complete_id
