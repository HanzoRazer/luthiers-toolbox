from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _as_dict(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x
    if hasattr(x, "model_dump"):
        return x.model_dump()
    if hasattr(x, "dict"):
        return x.dict()
    return getattr(x, "__dict__", {}) or {}


def _meta(it: Dict[str, Any]) -> Dict[str, Any]:
    m = it.get("index_meta")
    return m if isinstance(m, dict) else {}


def _payload(it: Dict[str, Any]) -> Dict[str, Any]:
    p = it.get("payload")
    return p if isinstance(p, dict) else {}


def _extract_suggestion(ev_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Our learning event stores:
      suggested_override: { hint, suggestion: { spindle_rpm_mult, feed_rate_mult, doc_mult } }
    """
    so = ev_payload.get("suggested_override")
    if not isinstance(so, dict):
        return None
    sug = so.get("suggestion")
    if not isinstance(sug, dict):
        return None
    return sug


def resolve_learned_multipliers(
    *,
    tool_id: Optional[str] = None,
    material_id: Optional[str] = None,
    thickness_mm: Optional[float] = None,
    limit_events: int = 200,
) -> Dict[str, Any]:
    """
    Safe "read path":
      - Looks at saw_lab_learning_event + saw_lab_learning_decision
      - Only considers events with latest decision == ACCEPT
      - Produces conservative averaged multipliers (default 1.0) + provenance

    NOTE: This does NOT automatically apply anything to planning/toolpaths.
    It just computes "what would we apply if enabled?"
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    limit_events = max(1, min(int(limit_events), 2000))

    # Pull recent events (filter in-memory; store may not support payload querying)
    events = query_run_artifacts(kind="saw_lab_learning_event", limit=limit_events, offset=0)
    events.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)

    # Decisions: we consider the newest decision per event id
    decisions = query_run_artifacts(kind="saw_lab_learning_decision", limit=limit_events * 2, offset=0)
    decisions.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=True)
    latest_decision_by_event: Dict[str, Dict[str, Any]] = {}
    for d in decisions:
        dm = _meta(d)
        ev_id = dm.get("parent_learning_event_artifact_id") or _payload(d).get("learning_event_artifact_id")
        if not ev_id:
            continue
        if ev_id not in latest_decision_by_event:
            latest_decision_by_event[ev_id] = d

    # Aggregate accepted suggestions
    rpm_mults: List[float] = []
    feed_mults: List[float] = []
    doc_mults: List[float] = []
    sources: List[Dict[str, Any]] = []

    for ev in events:
        ev_id = ev.get("artifact_id") or ev.get("id")
        if not ev_id:
            continue

        dec = latest_decision_by_event.get(ev_id)
        if not dec:
            continue
        pd = str((_meta(dec).get("policy_decision") or _payload(dec).get("policy_decision") or "")).upper()
        if pd != "ACCEPT":
            continue

        ep = _payload(ev)

        # Optional filtering (best-effort): material/tool from refs (if present)
        refs = ep.get("refs") or {}
        if not isinstance(refs, dict):
            refs = {}
        # At this stage we only have batch refs; material/tool may not be present.
        # Still: allow a caller to filter by known keys if you later include them in events.
        ev_tool = refs.get("tool_id") or ep.get("tool_id")
        ev_mat = refs.get("material_id") or ep.get("material_id")

        if tool_id and ev_tool and str(ev_tool) != str(tool_id):
            continue
        if material_id and ev_mat and str(ev_mat) != str(material_id):
            continue

        sug = _extract_suggestion(ep)
        if not sug:
            continue

        if "spindle_rpm_mult" in sug:
            try:
                rpm_mults.append(float(sug["spindle_rpm_mult"]))
            except Exception:
                pass
        if "feed_rate_mult" in sug:
            try:
                feed_mults.append(float(sug["feed_rate_mult"]))
            except Exception:
                pass
        if "doc_mult" in sug:
            try:
                doc_mults.append(float(sug["doc_mult"]))
            except Exception:
                pass

        sources.append(
            {
                "learning_event_artifact_id": ev_id,
                "learning_decision_artifact_id": (dec.get("artifact_id") or dec.get("id")),
                "signals": ep.get("signals"),
                "suggestion": sug,
            }
        )

    def _avg(xs: List[float]) -> Optional[float]:
        return (sum(xs) / len(xs)) if xs else None

    # Conservative defaults
    rpm = _avg(rpm_mults) or 1.0
    feed = _avg(feed_mults) or 1.0
    doc = _avg(doc_mults) or 1.0

    return {
        "query": {
            "tool_id": tool_id,
            "material_id": material_id,
            "thickness_mm": thickness_mm,
            "limit_events": limit_events,
        },
        "resolved": {
            "spindle_rpm_mult": rpm,
            "feed_rate_mult": feed,
            "doc_mult": doc,
        },
        "source_count": len(sources),
        "sources": sources[:50],  # bounded for UI safety
    }
