"""Saw Lab Batch Metrics Router"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.saw_lab.store import (
    get_artifact,
    query_executions_by_decision,
    query_execution_rollups_by_decision,
    query_job_logs_by_execution,
    query_metrics_rollups_by_execution,
    store_artifact,
)
from app.services.saw_lab_metrics_trends_service import compute_decision_trends

router = APIRouter(prefix="/api/saw/batch", tags=["saw", "batch"])

# --- Helpers ---

def _compute_execution_rollup(batch_execution_artifact_id: str) -> Dict[str, Any]:
    """Compute metrics rollup from job logs for an execution."""
    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    for log in logs:
        m = log.get("payload", {}).get("metrics", {})
        total_cut_time += m.get("cut_time_s", 0.0)
        total_setup_time += m.get("setup_time_s", 0.0)
        parts_ok += m.get("parts_ok", 0)
        parts_scrap += m.get("parts_scrap", 0)
        if m.get("burn"):
            burn_events += 1
        if m.get("tearout"):
            tearout_events += 1
        if m.get("kickback"):
            kickback_events += 1

    return {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "counts": {"job_log_count": len(logs)},
        "metrics": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
            "total_time_s": total_cut_time + total_setup_time,
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
        },
        "signals": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
    }

def _compute_decision_rollup(batch_decision_artifact_id: str) -> Dict[str, Any]:
    """Compute aggregated metrics rollup across all executions for a decision."""
    executions = query_executions_by_decision(batch_decision_artifact_id)

    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    job_log_count = 0

    for ex in executions:
        ex_id = ex.get("artifact_id")
        logs = query_job_logs_by_execution(ex_id)
        job_log_count += len(logs)
        for log in logs:
            m = log.get("payload", {}).get("metrics", {})
            total_cut_time += m.get("cut_time_s", 0.0)
            total_setup_time += m.get("setup_time_s", 0.0)
            parts_ok += m.get("parts_ok", 0)
            parts_scrap += m.get("parts_scrap", 0)

    return {
        "batch_decision_artifact_id": batch_decision_artifact_id,
        "counts": {
            "execution_count": len(executions),
            "job_log_count": job_log_count,
        },
        "metrics": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
            "total_time_s": total_cut_time + total_setup_time,
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
        },
    }

# --- Execution Metrics Rollup Endpoints (executions/metrics-rollup/*) ---

@router.get("/executions/metrics-rollup/by-execution")
def preview_execution_rollup(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """Preview (compute but don't persist) metrics rollup for an execution."""
    return _compute_execution_rollup(batch_execution_artifact_id)

@router.post("/executions/metrics-rollup/by-execution")
def persist_execution_rollup_new(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """Compute and persist metrics rollup for an execution."""
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    decision_id = execution.get("payload", {}).get("batch_decision_artifact_id", "")
    rollup_data = _compute_execution_rollup(batch_execution_artifact_id)
    rollup_data["parent_batch_decision_artifact_id"] = decision_id

    rollup_id = store_artifact(
        kind="saw_batch_execution_metrics_rollup",
        payload=rollup_data,
        parent_id=batch_execution_artifact_id,
    )

    return {
        "artifact_id": rollup_id,
        "kind": "saw_batch_execution_metrics_rollup",
        "payload": rollup_data,
    }

@router.get("/executions/metrics-rollup/latest")
def get_latest_execution_rollup(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """Get the latest persisted rollup for an execution."""
    rollups = query_metrics_rollups_by_execution(batch_execution_artifact_id)
    if not rollups:
        return {
            "found": False,
            "batch_execution_artifact_id": batch_execution_artifact_id,
        }

    latest = rollups[0]
    return {
        "found": True,
        "artifact_id": latest.get("artifact_id"),
        "kind": latest.get("kind", "saw_batch_execution_metrics_rollup"),
        "created_utc": latest.get("created_utc"),
        "payload": latest.get("payload", {}),
    }

@router.get("/executions/metrics-rollup/history")
def get_execution_rollup_history(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
) -> List[Dict[str, Any]]:
    """Get rollup history for an execution."""
    rollups = query_metrics_rollups_by_execution(batch_execution_artifact_id)[:limit]
    return [
        {
            "artifact_id": r.get("artifact_id"),
            "id": r.get("artifact_id"),
            "kind": r.get("kind", "saw_batch_execution_metrics_rollup"),
            "created_utc": r.get("created_utc"),
            "payload": r.get("payload", {}),
        }
        for r in rollups
    ]

# --- Decision Metrics Rollup Endpoints ---

@router.get("/decisions/metrics-rollup/by-decision")
def preview_decision_rollup(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
) -> Dict[str, Any]:
    """Preview (compute but don't persist) metrics rollup for a decision."""
    return _compute_decision_rollup(batch_decision_artifact_id)

@router.post("/decisions/metrics-rollup/by-decision")
def persist_decision_rollup(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
) -> Dict[str, Any]:
    """Compute and persist metrics rollup for a decision."""
    rollup_data = _compute_decision_rollup(batch_decision_artifact_id)

    rollup_id = store_artifact(
        kind="saw_batch_decision_metrics_rollup",
        payload=rollup_data,
        parent_id=batch_decision_artifact_id,
    )

    return {
        "artifact_id": rollup_id,
        "kind": "saw_batch_decision_metrics_rollup",
        "payload": rollup_data,
    }

@router.get("/decisions/metrics-rollup/latest")
def get_latest_decision_rollup(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
) -> Dict[str, Any]:
    """Get the latest persisted rollup for a decision."""
    rollups = query_execution_rollups_by_decision(batch_decision_artifact_id)
    if not rollups:
        return {
            "found": False,
            "batch_decision_artifact_id": batch_decision_artifact_id,
        }

    latest = rollups[0]
    return {
        "found": True,
        "artifact_id": latest.get("artifact_id"),
        "kind": latest.get("kind", "saw_batch_decision_metrics_rollup"),
        "created_utc": latest.get("created_utc"),
        "payload": latest.get("payload", {}),
    }

# --- Rollup Diff Endpoint ---

@router.get("/rollups/diff")
def compute_rollup_diff(
    left_rollup_artifact_id: str = Query(..., description="Left rollup artifact ID"),
    right_rollup_artifact_id: str = Query(..., description="Right rollup artifact ID"),
) -> Dict[str, Any]:
    """Compute diff between two rollup artifacts."""
    left = get_artifact(left_rollup_artifact_id)
    right = get_artifact(right_rollup_artifact_id)

    if not left:
        raise HTTPException(
            status_code=404, detail=f"Left rollup not found: {left_rollup_artifact_id}"
        )
    if not right:
        raise HTTPException(
            status_code=404,
            detail=f"Right rollup not found: {right_rollup_artifact_id}",
        )

    left_metrics = left.get("payload", {}).get("metrics", {})
    right_metrics = right.get("payload", {}).get("metrics", {})

    # Compute diffs
    metrics_diff = {}
    all_keys = set(left_metrics.keys()) | set(right_metrics.keys())
    for key in all_keys:
        left_val = left_metrics.get(key, 0)
        right_val = right_metrics.get(key, 0)
        if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
            metrics_diff[key] = {
                "left": left_val,
                "right": right_val,
                "delta": right_val - left_val,
            }

    return {
        "left_artifact_id": left_rollup_artifact_id,
        "right_artifact_id": right_rollup_artifact_id,
        "metrics": metrics_diff,
    }

# --- Metrics Rollup Endpoints (metrics/rollup/* paths) ---

@router.get("/metrics/rollup/by-execution")
def compute_execution_rollup(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """
    Compute metrics rollup for an execution from its job logs (read-only).
    """
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    # Aggregate metrics
    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    for log in logs:
        metrics = log.get("payload", {}).get("metrics", {})
        total_cut_time += metrics.get("cut_time_s", 0.0)
        total_setup_time += metrics.get("setup_time_s", 0.0)
        parts_ok += metrics.get("parts_ok", 0)
        parts_scrap += metrics.get("parts_scrap", 0)
        if metrics.get("burn"):
            burn_events += 1
        if metrics.get("tearout"):
            tearout_events += 1
        if metrics.get("kickback"):
            kickback_events += 1

    parts_total = parts_ok + parts_scrap
    scrap_rate = (parts_scrap / parts_total) if parts_total > 0 else 0.0

    return {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "log_count": len(logs),
        "times": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
        },
        "yield": {
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
            "parts_total": parts_total,
            "scrap_rate": scrap_rate,
        },
        "events": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
    }

@router.post("/metrics/rollup/by-execution")
def persist_execution_rollup(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> Dict[str, Any]:
    """
    Compute and persist metrics rollup artifact for an execution.
    """
    execution = get_artifact(batch_execution_artifact_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    exec_payload = execution.get("payload", {})
    decision_id = exec_payload.get("batch_decision_artifact_id", "")

    # Compute rollup
    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    total_cut_time = 0.0
    total_setup_time = 0.0
    parts_ok = 0
    parts_scrap = 0
    burn_events = 0
    tearout_events = 0
    kickback_events = 0

    for log in logs:
        metrics = log.get("payload", {}).get("metrics", {})
        total_cut_time += metrics.get("cut_time_s", 0.0)
        total_setup_time += metrics.get("setup_time_s", 0.0)
        parts_ok += metrics.get("parts_ok", 0)
        parts_scrap += metrics.get("parts_scrap", 0)
        if metrics.get("burn"):
            burn_events += 1
        if metrics.get("tearout"):
            tearout_events += 1
        if metrics.get("kickback"):
            kickback_events += 1

    parts_total = parts_ok + parts_scrap

    rollup_payload = {
        "batch_execution_artifact_id": batch_execution_artifact_id,
        "parent_batch_decision_artifact_id": decision_id,
        "log_count": len(logs),
        "metrics": {
            "cut_time_s": total_cut_time,
            "setup_time_s": total_setup_time,
            "parts_ok": parts_ok,
            "parts_scrap": parts_scrap,
        },
        "counts": {"job_log_count": len(logs)},
        "signals": {
            "burn_events": burn_events,
            "tearout_events": tearout_events,
            "kickback_events": kickback_events,
        },
    }

    rollup_id = store_artifact(
        kind="saw_batch_execution_rollup",
        payload=rollup_payload,
        parent_id=batch_execution_artifact_id,
    )

    return {
        "artifact_id": rollup_id,
        "kind": "saw_batch_execution_rollup",
        "payload": rollup_payload,
    }

@router.get("/metrics/rollup/alias")
def list_metrics_rollups(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> List[Dict[str, Any]]:
    """
    List metrics rollup artifacts for a given execution.
    """
    rollups = query_metrics_rollups_by_execution(batch_execution_artifact_id)

    results = []
    for art in rollups:
        results.append(
            {
                "artifact_id": art.get("artifact_id"),
                "kind": art.get("kind", "saw_batch_execution_rollup"),
                "status": art.get("status", "OK"),
                "created_utc": art.get("created_utc"),
                "payload": art.get("payload", {}),
            }
        )

    return results

# --- Decision Trends Endpoint ---

@router.get("/decisions/trends")
def get_decision_trends(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
    window: int = Query(
        default=20, ge=2, le=200, description="Window size for trend calculation"
    ),
) -> Dict[str, Any]:
    """Compute trend deltas for a batch decision's execution metrics over time."""
    return compute_decision_trends(
        batch_decision_artifact_id=batch_decision_artifact_id,
        window=window,
    )

# --- CSV Export: Decision Execution Rollups ---

@router.get("/decisions/execution-rollups.csv")
def export_execution_rollups_csv(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact ID"),
) -> PlainTextResponse:
    """
    Export execution rollups for a decision as CSV.
    """
    rollups = query_execution_rollups_by_decision(batch_decision_artifact_id)

    # Build CSV
    headers = [
        "rollup_artifact_id",
        "batch_execution_artifact_id",
        "log_count",
        "parts_ok",
        "parts_scrap",
        "scrap_rate",
        "cut_time_s",
        "setup_time_s",
        "created_utc",
    ]
    lines = [",".join(headers)]

    for rollup in rollups:
        payload = rollup.get("payload", {})
        metrics = payload.get("metrics", {})
        parts_ok = metrics.get("parts_ok", 0)
        parts_scrap = metrics.get("parts_scrap", 0)
        parts_total = parts_ok + parts_scrap
        scrap_rate = (parts_scrap / parts_total) if parts_total > 0 else 0.0

        row = [
            rollup.get("artifact_id", ""),
            payload.get("batch_execution_artifact_id", ""),
            str(
                payload.get(
                    "log_count", payload.get("counts", {}).get("job_log_count", 0)
                )
            ),
            str(parts_ok),
            str(parts_scrap),
            f"{scrap_rate:.4f}",
            str(metrics.get("cut_time_s", 0)),
            str(metrics.get("setup_time_s", 0)),
            rollup.get("created_utc", ""),
        ]
        lines.append(",".join(row))

    csv_content = "\n".join(lines)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="execution_rollups_{batch_decision_artifact_id[:8]}.csv"'
        },
    )
