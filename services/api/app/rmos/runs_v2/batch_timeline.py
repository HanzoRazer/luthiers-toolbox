from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


def _as_items(res: Any) -> List[Dict[str, Any]]:
    """Normalize store response to list of artifact dicts."""
    if isinstance(res, dict):
        items = res.get("items") or res.get("runs") or res.get("artifacts") or []
        return items if isinstance(items, list) else []
    return res if isinstance(res, list) else []


def _get_id(a: Dict[str, Any]) -> Optional[str]:
    v = a.get("id") or a.get("artifact_id")
    return str(v) if v else None


def _get_kind(a: Dict[str, Any]) -> str:
    return str(a.get("kind") or (a.get("index_meta") or {}).get("kind") or "")


def _created(a: Dict[str, Any]) -> str:
    """Extract created_utc timestamp from artifact."""
    payload = a.get("payload") or a.get("data") or {}
    if isinstance(payload, dict) and isinstance(payload.get("created_utc"), str):
        return payload["created_utc"]
    if isinstance(a.get("created_utc"), str):
        return a["created_utc"]
    return ""


def _pick_parent_id(a: Dict[str, Any]) -> Optional[str]:
    """Extract parent artifact id from index_meta using typed pointer keys."""
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
        "parent_plan_run_id",
        "parent_run_id",
    ):
        v = meta.get(k)
        if v:
            return str(v)

    v2 = a.get("parent_artifact_id") or a.get("parent_id")
    return str(v2) if v2 else None


def _artifact_status(a: Dict[str, Any]) -> str:
    """Extract status from artifact."""
    return str(a.get("status") or (a.get("payload") or {}).get("status") or "UNKNOWN")


def _kind_to_phase(kind: str) -> str:
    """Map artifact kind to batch workflow phase."""
    k = (kind or "").lower()
    if "spec" in k:
        return "SPEC"
    if "plan" in k:
        return "PLAN"
    if "decision" in k:
        return "DECISION"
    if "toolpath" in k:
        return "TOOLPATHS"
    if "execution" in k or "execute" in k:
        return "EXECUTION"
    if "result" in k or "output" in k:
        return "RESULT"
    return "OTHER"


@dataclass
class BatchTimelinePorts:
    """
    Minimal ports for timeline builder so we can unit-test easily.
    """
    list_runs_filtered: Any  # callable(**filters) -> dict|list
    get_run: Any  # callable(artifact_id) -> dict|None


@dataclass
class TimelineEvent:
    """Single event in the batch timeline."""
    artifact_id: str
    kind: str
    phase: str
    created_utc: str
    status: str
    parent_id: Optional[str]
    index_meta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "kind": self.kind,
            "phase": self.phase,
            "created_utc": self.created_utc,
            "status": self.status,
            "parent_id": self.parent_id,
            "index_meta": self.index_meta,
        }


def build_batch_timeline(
    ports: BatchTimelinePorts,
    *,
    session_id: str,
    batch_label: str,
    tool_kind: Optional[str] = None,
    limit: int = 500,
) -> Dict[str, Any]:
    """
    Builds a chronological timeline of events for a batch.

    Returns:
      {
        "session_id": "...",
        "batch_label": "...",
        "tool_kind": "...",
        "event_count": N,
        "events": [
          {
            "artifact_id": "...",
            "kind": "saw_batch_spec",
            "phase": "SPEC",
            "created_utc": "2025-01-01T00:00:00Z",
            "status": "OK",
            "parent_id": null,
            "index_meta": {...}
          },
          ...
        ],
        "phase_summary": {
          "SPEC": {"count": 1, "first_utc": "...", "last_utc": "..."},
          "PLAN": {"count": 1, "first_utc": "...", "last_utc": "..."},
          ...
        }
      }
    """
    res = ports.list_runs_filtered(
        session_id=session_id,
        batch_label=batch_label,
        limit=limit,
    )
    items = _as_items(res)

    # Filter by tool_kind if specified
    if tool_kind:
        items = [
            a for a in items
            if isinstance(a, dict)
            and str((a.get("index_meta") or {}).get("tool_kind") or "") == tool_kind
        ]

    # Build events
    events: List[TimelineEvent] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        aid = _get_id(a)
        if not aid:
            continue

        kind = _get_kind(a)
        created = _created(a)
        status = _artifact_status(a)
        parent = _pick_parent_id(a)
        meta = a.get("index_meta") or {}

        events.append(TimelineEvent(
            artifact_id=aid,
            kind=kind,
            phase=_kind_to_phase(kind),
            created_utc=created,
            status=status,
            parent_id=parent,
            index_meta=meta if isinstance(meta, dict) else {},
        ))

    # Sort chronologically (oldest first)
    events.sort(key=lambda e: (e.created_utc or "9999", e.artifact_id))

    # Build phase summary
    phase_summary: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        phase = ev.phase
        if phase not in phase_summary:
            phase_summary[phase] = {
                "count": 0,
                "first_utc": ev.created_utc,
                "last_utc": ev.created_utc,
            }
        ps = phase_summary[phase]
        ps["count"] += 1
        if ev.created_utc:
            if not ps["first_utc"] or ev.created_utc < ps["first_utc"]:
                ps["first_utc"] = ev.created_utc
            if not ps["last_utc"] or ev.created_utc > ps["last_utc"]:
                ps["last_utc"] = ev.created_utc

    return {
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": tool_kind,
        "event_count": len(events),
        "events": [e.to_dict() for e in events],
        "phase_summary": phase_summary,
    }


def get_batch_progress(
    ports: BatchTimelinePorts,
    *,
    session_id: str,
    batch_label: str,
    tool_kind: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns a simplified progress summary for a batch.

    Useful for progress bars / status indicators.

    Returns:
      {
        "session_id": "...",
        "batch_label": "...",
        "tool_kind": "...",
        "phases_completed": ["SPEC", "PLAN"],
        "current_phase": "DECISION",
        "total_artifacts": N,
        "status": "IN_PROGRESS" | "COMPLETED" | "BLOCKED" | "ERROR"
      }
    """
    timeline = build_batch_timeline(
        ports,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        limit=500,
    )

    events = timeline.get("events") or []
    phase_summary = timeline.get("phase_summary") or {}

    # Define expected phase order
    phase_order = ["SPEC", "PLAN", "DECISION", "TOOLPATHS", "EXECUTION", "RESULT"]

    # Find completed phases (phases with at least one OK artifact)
    completed_phases = []
    current_phase = None
    has_error = False
    has_blocked = False

    for phase in phase_order:
        ps = phase_summary.get(phase)
        if ps and ps.get("count", 0) > 0:
            # Check if any artifacts in this phase have non-OK status
            phase_statuses = [
                e["status"] for e in events
                if e.get("phase") == phase
            ]
            if any(s == "ERROR" for s in phase_statuses):
                has_error = True
            if any(s == "BLOCKED" for s in phase_statuses):
                has_blocked = True

            # Consider phase complete if we have artifacts for the next phase
            completed_phases.append(phase)
            current_phase = phase

    # Determine overall status
    if has_error:
        overall_status = "ERROR"
    elif has_blocked:
        overall_status = "BLOCKED"
    elif "RESULT" in completed_phases or "EXECUTION" in completed_phases:
        overall_status = "COMPLETED"
    elif completed_phases:
        overall_status = "IN_PROGRESS"
    else:
        overall_status = "NOT_STARTED"

    return {
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": tool_kind,
        "phases_completed": completed_phases,
        "current_phase": current_phase,
        "total_artifacts": len(events),
        "status": overall_status,
    }
