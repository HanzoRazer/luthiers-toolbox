"""Batch Metrics Decision Router - Decision-level metrics rollups, trends, and exports.

Provides:
- GET  /decisions/metrics-rollup/by-decision - Preview decision rollup
- POST /decisions/metrics-rollup/by-decision - Persist decision rollup
- GET  /decisions/metrics-rollup/latest - Get latest decision rollup
- GET  /decisions/trends - Compute decision trends
- GET  /decisions/execution-rollups.csv - Export execution rollups as CSV

Total: 5 routes for decision metrics operations.

LANE: UTILITY
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from app.saw_lab.store import (
    query_executions_by_decision,
    query_execution_rollups_by_decision,
    query_job_logs_by_execution,
    store_artifact,
)
from app.services.saw_lab_metrics_trends_service import compute_decision_trends

router = APIRouter(tags=["saw", "batch", "decision-metrics"])


# --- Helpers ---

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


__all__ = [
    "router",
    "_compute_decision_rollup",
]
