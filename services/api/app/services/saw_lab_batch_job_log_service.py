from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def write_job_log(
    *,
    batch_execution_artifact_id: str,
    operator: str,
    notes: str,
    status: str,
    metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Persist an operator-facing job log tied to a batch execution.
    """
    from app.rmos.run_artifacts.store import read_run_artifact, write_run_artifact
    from app.services.saw_lab_learning_hook_config import is_saw_lab_learning_hook_enabled
    from app.services.saw_lab_operator_feedback_learning_hook import record_operator_feedback_event
    from app.services.saw_lab_metrics_rollup_hook_config import is_saw_lab_metrics_rollup_hook_enabled
    from app.services.saw_lab_execution_metrics_rollup_service import persist_execution_metrics_rollup
    from app.services.saw_lab_decision_metrics_rollup_service import persist_decision_metrics_rollup

    parent = read_run_artifact(batch_execution_artifact_id)
    if str(getattr(parent, "kind", parent.get("kind", ""))) != "saw_batch_execution":
        raise ValueError("batch_execution_artifact_id must reference saw_batch_execution")

    parent_d: Dict[str, Any] = parent if isinstance(parent, dict) else {
        "artifact_id": getattr(parent, "artifact_id", None) or getattr(parent, "id", None),
        "kind": getattr(parent, "kind", None),
        "status": getattr(parent, "status", None),
        "index_meta": getattr(parent, "index_meta", None),
        "payload": getattr(parent, "payload", None),
        "created_utc": getattr(parent, "created_utc", None),
    }

    meta = parent_d.get("index_meta", {}) or {}

    art = write_run_artifact(
        kind="saw_batch_job_log",
        status=status,
        session_id=meta.get("session_id"),
        index_meta={
            "tool_kind": "saw_lab",
            "kind_group": "batch",
            "batch_label": meta.get("batch_label"),
            "session_id": meta.get("session_id"),
            "parent_batch_execution_artifact_id": batch_execution_artifact_id,
            "parent_batch_decision_artifact_id": meta.get("parent_batch_decision_artifact_id"),
            "operator": operator,
        },
        payload={
            "batch_execution_artifact_id": batch_execution_artifact_id,
            "operator": operator,
            "notes": notes,
            "status": status,
            "metrics": metrics or {},
        },
    )

    job_log_art = art if isinstance(art, dict) else getattr(art, "__dict__", {})

    # Optional: auto-wire learning event emission (feature-flagged)
    learning_event_art = None
    learning_event_error = None
    if is_saw_lab_learning_hook_enabled():
        try:
            learning_event_art = record_operator_feedback_event(
                job_log_artifact=job_log_art,
                execution_artifact=parent_d,
                decision_artifact=None,
                policy_decision="PROPOSE",
            )
        except Exception as e:
            # Never fail the job log write if the learning hook fails.
            learning_event_error = f"{type(e).__name__}: {e}"

    # Optional: auto-persist rollup artifacts (feature-flagged)
    rollups = None
    if is_saw_lab_metrics_rollup_hook_enabled():
        try:
            ex_roll = persist_execution_metrics_rollup(batch_execution_artifact_id=batch_execution_artifact_id)
            # If we can discover a decision parent from execution meta/payload, also persist decision rollup
            dec_id = meta.get("parent_batch_decision_artifact_id")
            dec_roll = None
            if dec_id:
                try:
                    dec_roll = persist_decision_metrics_rollup(batch_decision_artifact_id=dec_id)
                except Exception:
                    dec_roll = None

            rollups = {
                "execution_rollup_artifact": ex_roll,
                "decision_rollup_artifact": dec_roll,
            }
        except Exception:
            rollups = None

    # Keep response backward-compatible but include hook outputs when present.
    if isinstance(job_log_art, dict):
        if learning_event_art is not None:
            job_log_art["learning_event"] = learning_event_art
        if learning_event_error is not None:
            job_log_art["learning_event_error"] = learning_event_error
        job_log_art["learning_hook_enabled"] = is_saw_lab_learning_hook_enabled()
        job_log_art["rollups"] = rollups
        return job_log_art

    return {
        "job_log": job_log_art,
        "learning_event": learning_event_art,
        "learning_event_error": learning_event_error,
        "learning_hook_enabled": is_saw_lab_learning_hook_enabled(),
        "rollups": rollups,
    }
