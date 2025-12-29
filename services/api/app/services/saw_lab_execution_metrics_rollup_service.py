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


def _num(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def compute_execution_metrics_rollup(
    *,
    batch_execution_artifact_id: str,
    limit_job_logs: int = 500,
) -> Dict[str, Any]:
    """
    Compute a compact rollup for a specific execution based on:
      - saw_batch_job_log artifacts parented to the execution
      - saw_lab_learning_event artifacts parented to the execution (optional)

    This is deliberately small and UI-friendly.
    """
    from app.rmos.run_artifacts.store import read_run_artifact, query_run_artifacts

    ex = read_run_artifact(batch_execution_artifact_id)
    ex_d = _as_dict(ex)
    if str(ex_d.get("kind") or "") != "saw_batch_execution":
        raise ValueError("batch_execution_artifact_id must reference kind='saw_batch_execution'")

    ex_meta = ex_d.get("index_meta") or {}
    if not isinstance(ex_meta, dict):
        ex_meta = {}

    limit_job_logs = max(1, min(int(limit_job_logs), 2000))
    job_logs = query_run_artifacts(
        kind="saw_batch_job_log",
        parent_batch_execution_artifact_id=batch_execution_artifact_id,
        limit=limit_job_logs,
        offset=0,
    )
    job_logs.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=False)

    learning_events = query_run_artifacts(
        kind="saw_lab_learning_event",
        parent_batch_execution_artifact_id=batch_execution_artifact_id,
        limit=2000,
        offset=0,
    )

    # Aggregate metrics
    parts_ok = 0
    parts_scrap = 0
    cut_time_s = 0.0
    setup_time_s = 0.0
    job_log_count = 0

    status_counts: Dict[str, int] = {}
    operators: Dict[str, int] = {}

    for jl in job_logs:
        job_log_count += 1
        pl = _payload(jl)
        op = str(pl.get("operator") or _meta(jl).get("operator") or "unknown")
        operators[op] = operators.get(op, 0) + 1

        st = str(pl.get("status") or jl.get("status") or "UNKNOWN").upper()
        status_counts[st] = status_counts.get(st, 0) + 1

        m = pl.get("metrics") or {}
        if not isinstance(m, dict):
            m = {}

        po = _int(m.get("parts_ok"))
        ps = _int(m.get("parts_scrap") or m.get("scrap_count"))
        if po is not None:
            parts_ok += max(0, po)
        if ps is not None:
            parts_scrap += max(0, ps)

        ct = _num(m.get("cut_time_s") or m.get("cut_time_sec"))
        if ct is not None:
            cut_time_s += max(0.0, ct)

        stt = _num(m.get("setup_time_s") or m.get("setup_time_sec"))
        if stt is not None:
            setup_time_s += max(0.0, stt)

    # Learning signals (counts only)
    burn_n = 0
    tearout_n = 0
    kickback_n = 0
    for ev in learning_events:
        ep = _payload(ev)
        sig = ep.get("signals") or {}
        if not isinstance(sig, dict):
            sig = {}
        if bool(sig.get("burn")):
            burn_n += 1
        if bool(sig.get("tearout")):
            tearout_n += 1
        if bool(sig.get("kickback")):
            kickback_n += 1

    return {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "batch_label": ex_meta.get("batch_label"),
        "session_id": ex_meta.get("session_id"),
        "parent_batch_decision_artifact_id": ex_meta.get("parent_batch_decision_artifact_id"),
        "counts": {
            "job_log_count": job_log_count,
            "learning_event_count": len(learning_events),
        },
        "operators": operators,
        "statuses": status_counts,
        "metrics": {
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
            "cut_time_s": round(cut_time_s, 3),
            "setup_time_s": round(setup_time_s, 3),
            "total_time_s": round(cut_time_s + setup_time_s, 3),
        },
        "signals": {
            "burn_events": burn_n,
            "tearout_events": tearout_n,
            "kickback_events": kickback_n,
        },
    }


def persist_execution_metrics_rollup(
    *,
    batch_execution_artifact_id: str,
    limit_job_logs: int = 500,
) -> Dict[str, Any]:
    """
    Persist a governed rollup artifact so UI/diff can compare executions over time.
    """
    from app.rmos.run_artifacts.store import write_run_artifact

    rollup = compute_execution_metrics_rollup(
        batch_execution_artifact_id=batch_execution_artifact_id,
        limit_job_logs=limit_job_logs,
    )

    art = write_run_artifact(
        kind="saw_batch_execution_metrics_rollup",
        status="OK",
        session_id=rollup.get("session_id"),
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": rollup.get("batch_label"),
            "session_id": rollup.get("session_id"),
            "parent_batch_execution_artifact_id": batch_execution_artifact_id,
            "parent_batch_decision_artifact_id": rollup.get("parent_batch_decision_artifact_id"),
        },
        payload=rollup,
    )
    return _as_dict(art)
