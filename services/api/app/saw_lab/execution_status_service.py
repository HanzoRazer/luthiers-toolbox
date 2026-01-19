from __future__ import annotations

from typing import Any, Dict, List, Optional


# Artifact kinds
K_EXECUTION = "saw_batch_execution"
K_CONFIRM = "saw_batch_execution_confirmation"
K_JOB_LOG = "saw_batch_job_log"
K_ABORT = "saw_batch_execution_abort"
K_COMPLETE = "saw_batch_execution_complete"
K_METRICS = "saw_batch_execution_metrics"
K_LINT = "saw_toolpaths_lint_report"


def _payload(art: Dict[str, Any]) -> Dict[str, Any]:
    p = art.get("payload") or art.get("data") or {}
    return p if isinstance(p, dict) else {}


def _id(art: Dict[str, Any]) -> Optional[str]:
    v = art.get("id") or art.get("artifact_id")
    return str(v) if v else None


def _created_utc(art: Dict[str, Any]) -> str:
    return art.get("created_utc") or ""


def _parent_id(art: Dict[str, Any]) -> Optional[str]:
    v = art.get("parent_id") or art.get("parent_artifact_id")
    return str(v) if v else None


def _safe_list_runs(
    *,
    session_id: Optional[str],
    batch_label: Optional[str],
    tool_kind: str,
    kind: Optional[str] = None,
    limit: int = 5000,
) -> List[Dict[str, Any]]:
    from app.rmos.runs_v2 import store as runs_store

    try:
        res = runs_store.list_runs_filtered(
            session_id=session_id,
            batch_label=batch_label,
            tool_kind=tool_kind,
            kind=kind,
            limit=limit,
        )
    except TypeError:
        res = runs_store.list_runs_filtered(
            session_id=session_id,
            batch_label=batch_label,
            tool_kind=tool_kind,
            limit=limit,
        )

    items = res.get("items") if isinstance(res, dict) else None
    return items if isinstance(items, list) else []


def _latest_child(
    artifacts: List[Dict[str, Any]],
    parent_artifact_id: str,
) -> Optional[Dict[str, Any]]:
    matches = [
        a for a in artifacts
        if isinstance(a, dict) and _parent_id(a) == parent_artifact_id
    ]
    matches.sort(key=_created_utc, reverse=True)
    return matches[0] if matches else None


def compute_execution_status(
    *,
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> Dict[str, Any]:
    """
    Returns execution status for operator / dashboard use.
    Deterministic, best-effort, no hard failures.
    """
    from app.rmos.runs_v2 import store as runs_store

    execution = runs_store.get_run(batch_execution_artifact_id)
    if not isinstance(execution, dict):
        return {
            "ok": False,
            "status": "UNKNOWN",
            "error": "execution not found",
        }

    exec_id = _id(execution) or batch_execution_artifact_id
    payload = _payload(execution)

    session_id = session_id or payload.get("session_id")
    batch_label = batch_label or payload.get("batch_label")

    confirmations = _safe_list_runs(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        kind=K_CONFIRM,
    )
    job_logs = _safe_list_runs(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        kind=K_JOB_LOG,
    )
    aborts = _safe_list_runs(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        kind=K_ABORT,
    )
    completes = _safe_list_runs(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        kind=K_COMPLETE,
    )
    metrics = _safe_list_runs(
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        kind=K_METRICS,
    )

    latest_confirm = _latest_child(confirmations, exec_id)
    latest_job_log = _latest_child(job_logs, exec_id)
    latest_abort = _latest_child(aborts, exec_id)
    latest_complete = _latest_child(completes, exec_id)
    latest_metrics = _latest_child(metrics, exec_id)

    # Status resolution (strict precedence)
    if payload.get("status") == "BLOCKED":
        status = "BLOCKED"
    elif latest_abort:
        status = "ABORTED"
    elif latest_complete:
        status = "COMPLETE"
    elif latest_confirm and latest_job_log:
        status = "RUNNING"
    elif latest_confirm:
        status = "CONFIRMED"
    else:
        status = "PENDING"

    out: Dict[str, Any] = {
        "ok": True,
        "batch_execution_artifact_id": exec_id,
        "session_id": session_id,
        "batch_label": batch_label,
        "tool_kind": tool_kind,
        "status": status,
        "created_utc": execution.get("created_utc"),
        "updated_utc": execution.get("updated_utc"),
        "links": {
            "decision_artifact_id": payload.get("decision_artifact_id"),
            "toolpaths_artifact_id": payload.get("toolpaths_artifact_id"),
            "confirmation_artifact_id": _id(latest_confirm),
            "latest_job_log_artifact_id": _id(latest_job_log),
            "latest_metrics_artifact_id": _id(latest_metrics),
            "abort_artifact_id": _id(latest_abort),
            "complete_artifact_id": _id(latest_complete),
        },
    }

    if latest_metrics:
        mp = _payload(latest_metrics)
        if isinstance(mp.get("kpis"), dict):
            out["kpis"] = mp["kpis"]

    return out
