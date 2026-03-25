from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.saw_lab_execution_metrics_rollup_service import compute_execution_metrics_rollup


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


def compute_decision_metrics_rollup(
    *,
    batch_decision_artifact_id: str,
    limit_executions: int = 200,
    limit_job_logs_per_execution: int = 500,
) -> Dict[str, Any]:
    """
    Roll up metrics across ALL executions under one decision artifact.

    Inputs:
      - saw_batch_execution artifacts parented to decision
      - saw_batch_job_log artifacts (via execution rollups)

    Output is compact + UI-friendly, suitable for diffing and trends.
    """
    from app.rmos.run_artifacts.store import read_run_artifact, query_run_artifacts

    dec = read_run_artifact(batch_decision_artifact_id)
    dec_d = _as_dict(dec)
    if str(dec_d.get("kind") or "") != "saw_batch_decision":
        raise ValueError("batch_decision_artifact_id must reference kind='saw_batch_decision'")

    dec_meta = dec_d.get("index_meta") or {}
    if not isinstance(dec_meta, dict):
        dec_meta = {}

    limit_executions = max(1, min(int(limit_executions), 2000))
    executions = query_run_artifacts(
        kind="saw_batch_execution",
        parent_batch_decision_artifact_id=batch_decision_artifact_id,
        limit=limit_executions,
        offset=0,
    )
    executions.sort(key=lambda x: str(x.get("created_utc") or ""), reverse=False)

    # Aggregate totals
    total_job_logs = 0
    total_learning_events = 0
    total_parts_ok = 0
    total_parts_scrap = 0
    total_cut_time_s = 0.0
    total_setup_time_s = 0.0
    applied_learning_n = 0

    execution_summaries: List[Dict[str, Any]] = []

    for ex in executions:
        ex_id = ex.get("artifact_id") or ex.get("id")
        if not ex_id:
            continue

        # applied stamp is authoritative in execution payload
        ex_payload = _payload(ex)
        applied = False
        if isinstance(ex_payload, dict):
            learning = ex_payload.get("learning") or {}
            if isinstance(learning, dict):
                stamp = learning.get("tuning_stamp") or {}
                if isinstance(stamp, dict) and stamp.get("applied") is True:
                    applied = True
        if applied:
            applied_learning_n += 1

        ex_roll = compute_execution_metrics_rollup(
            batch_execution_artifact_id=ex_id,
            limit_job_logs=limit_job_logs_per_execution,
        )

        total_job_logs += int((ex_roll.get("counts") or {}).get("job_log_count") or 0)
        total_learning_events += int((ex_roll.get("counts") or {}).get("learning_event_count") or 0)

        m = ex_roll.get("metrics") or {}
        total_parts_ok += int(m.get("parts_ok") or 0)
        total_parts_scrap += int(m.get("parts_scrap") or 0)
        total_cut_time_s += float(m.get("cut_time_s") or 0.0)
        total_setup_time_s += float(m.get("setup_time_s") or 0.0)

        execution_summaries.append(
            {
                "batch_execution_artifact_id": ex_id,
                "created_utc": ex.get("created_utc"),
                "learning_applied": applied,
                "counts": ex_roll.get("counts"),
                "metrics": ex_roll.get("metrics"),
                "signals": ex_roll.get("signals"),
            }
        )

    n_exec = len(execution_summaries)
    return {
        "batch_decision_artifact_id": batch_decision_artifact_id,
        "batch_label": dec_meta.get("batch_label"),
        "session_id": dec_meta.get("session_id"),
        "counts": {
            "execution_count": n_exec,
            "job_log_count": total_job_logs,
            "learning_event_count": total_learning_events,
            "learning_applied_execution_count": applied_learning_n,
        },
        "metrics": {
            "parts_ok": total_parts_ok,
            "parts_scrap": total_parts_scrap,
            "cut_time_s": round(total_cut_time_s, 3),
            "setup_time_s": round(total_setup_time_s, 3),
            "total_time_s": round(total_cut_time_s + total_setup_time_s, 3),
        },
        "rate": {
            "scrap_rate": (total_parts_scrap / max(1, (total_parts_ok + total_parts_scrap))),
            "learning_applied_rate": (applied_learning_n / max(1, n_exec)),
        },
        # bounded summaries for UI; full details can be pulled per execution via existing endpoints
        "executions": execution_summaries[:200],
    }


def persist_decision_metrics_rollup(
    *,
    batch_decision_artifact_id: str,
    limit_executions: int = 200,
    limit_job_logs_per_execution: int = 500,
) -> Dict[str, Any]:
    """
    Persist governed rollup artifact for the decision.
    """
    from app.rmos.run_artifacts.store import write_run_artifact

    rollup = compute_decision_metrics_rollup(
        batch_decision_artifact_id=batch_decision_artifact_id,
        limit_executions=limit_executions,
        limit_job_logs_per_execution=limit_job_logs_per_execution,
    )

    art = write_run_artifact(
        kind="saw_batch_decision_metrics_rollup",
        status="OK",
        session_id=rollup.get("session_id"),
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": rollup.get("batch_label"),
            "session_id": rollup.get("session_id"),
            "parent_batch_decision_artifact_id": batch_decision_artifact_id,
        },
        payload=rollup,
    )
    return _as_dict(art)
