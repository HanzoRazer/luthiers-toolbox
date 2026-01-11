from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _as_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def _kind(a: Dict[str, Any]) -> str:
    return str(a.get("kind") or _as_dict(a.get("index_meta")).get("kind") or "")


def _id(a: Dict[str, Any]) -> Optional[str]:
    v = a.get("id") or a.get("artifact_id")
    return str(v) if v else None


def _created_utc(a: Dict[str, Any]) -> str:
    if isinstance(a.get("created_utc"), str):
        return a["created_utc"]
    p = _as_dict(a.get("payload") or a.get("data"))
    if isinstance(p.get("created_utc"), str):
        return p["created_utc"]
    return ""


def _note_text(payload: Dict[str, Any]) -> str:
    for k in ("notes", "note", "operator_notes", "comments", "comment"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().lower()
    return ""


def _extract_job_log_stats(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Most common shapes:
    #   payload.statistics
    #   payload.metrics
    #   payload.plan_statistics
    stats = (
        payload.get("statistics")
        or payload.get("metrics")
        or payload.get("plan_statistics")
        or {}
    )
    return stats if isinstance(stats, dict) else {}


def rollup_execution_metrics_from_job_logs(
    job_log_artifacts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Roll up KPIs from a list of job log artifacts (best-effort).
    Output: dict ready to store as payload.kpis
    """
    totals = {
        "job_log_count": 0,
        "total_length_mm": 0.0,
        "total_cut_count": 0,
        "total_move_count": 0,
        "duration_sec_total": 0.0,
        "duration_sec_avg": None,
    }
    signals = {"burn": 0, "tearout": 0, "kickback": 0, "chatter": 0, "bog": 0}

    # Track durations if present
    durations: List[float] = []

    for a in job_log_artifacts:
        if not isinstance(a, dict):
            continue
        p = _as_dict(a.get("payload") or a.get("data"))
        totals["job_log_count"] += 1

        stats = _extract_job_log_stats(p)
        if isinstance(stats.get("total_length_mm"), (int, float)):
            totals["total_length_mm"] += float(stats["total_length_mm"])
        if isinstance(stats.get("cut_count"), (int, float)):
            totals["total_cut_count"] += int(stats["cut_count"])
        if isinstance(stats.get("move_count"), (int, float)):
            totals["total_move_count"] += int(stats["move_count"])

        # Optional timing fields
        for k in ("duration_sec", "elapsed_sec", "cut_time_sec"):
            if isinstance(stats.get(k), (int, float)):
                durations.append(float(stats[k]))
                break

        note = _note_text(p)
        for sk in list(signals.keys()):
            if sk in note:
                signals[sk] += 1

    totals["total_length_mm"] = round(float(totals["total_length_mm"]), 3)
    totals["duration_sec_total"] = round(sum(durations), 3) if durations else 0.0
    totals["duration_sec_avg"] = (
        round(sum(durations) / len(durations), 3) if durations else None
    )

    return {
        "totals": totals,
        "signal_mentions": signals,
        "schema_version": "saw_execution_metrics_v1",
    }


def write_execution_metrics_rollup_artifact(
    *,
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> str:
    """
    Reads all saw_batch_job_log artifacts for the batch execution, rolls up KPIs,
    and persists a governed metrics artifact:
      kind = saw_batch_execution_metrics
      parent = batch_execution_artifact_id

    Returns: metrics artifact id (string)
    """
    from app.rmos.runs_v2 import store as runs_store
    from app.rmos.runs_v2.store import store_artifact

    # Pull all runs for the batch (flat filter). We then filter to job logs that reference this execution.
    res = runs_store.list_runs_filtered(
        session_id=session_id or None,
        batch_label=batch_label or None,
        tool_kind=tool_kind,
        limit=10000,
    )
    items = res.get("items") if isinstance(res, dict) else res
    items = items if isinstance(items, list) else []

    job_logs: List[Dict[str, Any]] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        if "job_log" not in _kind(a).lower():
            continue
        p = _as_dict(a.get("payload") or a.get("data"))
        # common linkage fields used across the saw lab workflow
        ref = p.get("batch_execution_artifact_id") or _as_dict(
            _as_dict(a.get("index_meta")).get("links")
        ).get("batch_execution_artifact_id")
        if ref and str(ref) == str(batch_execution_artifact_id):
            job_logs.append(a)

    # Deterministic ordering
    job_logs.sort(key=lambda a: (_created_utc(a) or "9999", str(_id(a) or "")))

    kpis = rollup_execution_metrics_from_job_logs(job_logs)

    payload = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "kpis": kpis,
        "job_log_artifact_ids": [str(_id(a)) for a in job_logs if _id(a)],
    }

    # Optional: embed minimal pointers (do not duplicate full logs)
    metrics_id = store_artifact(
        kind="saw_batch_execution_metrics",
        payload=payload,
        parent_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )
    return str(metrics_id)
