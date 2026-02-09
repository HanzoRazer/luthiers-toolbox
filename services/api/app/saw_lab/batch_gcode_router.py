"""
Saw Lab Batch G-code Router

G-code export and execution retry endpoints extracted from batch_router.py:
  - Op-toolpaths G-code export
  - Execution G-code export (combined)
  - Execution retry
  - Job logs CSV export

Mounted at: /api/saw/batch
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.saw_lab.batch_router_schemas import RetryResponse
from app.saw_lab.store import (
    get_artifact,
    query_job_logs_by_execution,
    store_artifact,
)

router = APIRouter(prefix="/api/saw/batch", tags=["saw", "batch"])


# ---------------------------------------------------------------------------
# G-code Export Endpoints
# ---------------------------------------------------------------------------


@router.get("/op-toolpaths/{op_toolpaths_artifact_id}/gcode")
def get_op_toolpaths_gcode(op_toolpaths_artifact_id: str) -> PlainTextResponse:
    """
    Export G-code for a single op toolpath artifact.

    Returns plain text G-code with Content-Disposition for download.
    """
    from app.saw_lab.store import read_artifact as read_saw_artifact
    from app.services.saw_lab_gcode_emit_service import export_op_toolpaths_gcode

    try:
        result = export_op_toolpaths_gcode(
            op_toolpaths_artifact_id=op_toolpaths_artifact_id,
            read_artifact=read_saw_artifact,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Op toolpaths artifact not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = result.get("filename", f"{op_toolpaths_artifact_id[:8]}.ngc")

    return PlainTextResponse(
        content=result["gcode"],
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/executions/{batch_execution_artifact_id}/gcode")
def get_execution_gcode(batch_execution_artifact_id: str) -> PlainTextResponse:
    """
    Export combined G-code for all OK ops in an execution.

    Returns plain text G-code with Content-Disposition for download.
    """
    from app.saw_lab.store import read_artifact as read_saw_artifact
    from app.services.saw_lab_gcode_emit_service import export_execution_gcode

    try:
        result = export_execution_gcode(
            batch_execution_artifact_id=batch_execution_artifact_id,
            read_artifact=read_saw_artifact,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Execution artifact not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = result.get("filename", f"{batch_execution_artifact_id[:8]}.ngc")

    return PlainTextResponse(
        content=result["gcode"],
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Execution Retry Endpoint
# ---------------------------------------------------------------------------


@router.post("/executions/retry", response_model=RetryResponse)
def retry_execution(
    batch_execution_artifact_id: str = Query(
        ..., description="Source execution to retry"
    ),
    reason: str = Query("", description="Reason for retry"),
) -> RetryResponse:
    """
    Create a retry execution from a source execution.

    Retries BLOCKED or ERROR ops. If all OK, creates an empty retry.
    """
    source = get_artifact(batch_execution_artifact_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source execution not found")

    source_payload = source.get("payload", {})
    decision_id = source_payload.get("batch_decision_artifact_id", "")
    plan_id = source_payload.get("batch_plan_artifact_id", "")
    spec_id = source_payload.get("batch_spec_artifact_id", "")
    batch_label = source_payload.get("batch_label", "")
    session_id = source_payload.get("session_id", "")

    # Collect ops that need retry (BLOCKED/ERROR)
    results = source_payload.get("results", [])
    retry_ops = [r for r in results if r.get("status") in ("BLOCKED", "ERROR")]

    # Create new child op_toolpaths for retry ops (or empty if all OK)
    new_children = []
    new_results = []
    for op in retry_ops:
        op_payload = {
            "batch_decision_artifact_id": decision_id,
            "batch_plan_artifact_id": plan_id,
            "batch_spec_artifact_id": spec_id,
            "op_id": op.get("op_id"),
            "setup_key": op.get("setup_key", ""),
            "toolpaths": {"moves": []},  # Empty retry toolpaths
            "retry_source": batch_execution_artifact_id,
        }
        child_id = store_artifact(
            kind="saw_batch_op_toolpaths",
            payload=op_payload,
            parent_id=decision_id,
            session_id=session_id,
            status="OK",
        )
        new_children.append({"artifact_id": child_id, "kind": "saw_batch_op_toolpaths"})
        new_results.append(
            {
                "op_id": op.get("op_id"),
                "setup_key": op.get("setup_key", ""),
                "status": "OK",
                "toolpaths_artifact_id": child_id,
            }
        )

    # Create new execution artifact
    new_exec_payload = {
        "batch_decision_artifact_id": decision_id,
        "batch_plan_artifact_id": plan_id,
        "batch_spec_artifact_id": spec_id,
        "batch_label": batch_label,
        "session_id": session_id,
        "summary": {
            "op_count": len(new_results),
            "ok_count": len(new_results),
            "blocked_count": 0,
            "error_count": 0,
        },
        "children": new_children,
        "results": new_results,
        "retry_source_execution_id": batch_execution_artifact_id,
    }
    new_exec_id = store_artifact(
        kind="saw_batch_execution",
        payload=new_exec_payload,
        parent_id=decision_id,
        session_id=session_id,
        status="OK",
    )

    # Create retry artifact
    retry_payload = {
        "source_execution_artifact_id": batch_execution_artifact_id,
        "new_execution_artifact_id": new_exec_id,
        "reason": reason,
        "retry_op_count": len(retry_ops),
    }
    retry_id = store_artifact(
        kind="saw_batch_execution_retry",
        payload=retry_payload,
        parent_id=batch_execution_artifact_id,
        session_id=session_id,
    )

    return RetryResponse(
        source_execution_artifact_id=batch_execution_artifact_id,
        new_execution_artifact_id=new_exec_id,
        retry_artifact_id=retry_id,
    )


# ---------------------------------------------------------------------------
# CSV Export: Job Logs
# ---------------------------------------------------------------------------


@router.get("/executions/job-logs.csv")
def export_job_logs_csv(
    batch_execution_artifact_id: str = Query(..., description="Execution artifact ID"),
) -> PlainTextResponse:
    """
    Export job logs for an execution as CSV.
    """
    logs = query_job_logs_by_execution(batch_execution_artifact_id)

    # Build CSV
    headers = [
        "job_log_artifact_id",
        "operator",
        "notes",
        "status",
        "parts_ok",
        "parts_scrap",
        "cut_time_s",
        "setup_time_s",
        "created_utc",
    ]
    lines = [",".join(headers)]

    for log in logs:
        payload = log.get("payload", {})
        metrics = payload.get("metrics", {})
        row = [
            log.get("artifact_id", ""),
            payload.get("operator", ""),
            payload.get("notes", "").replace(",", ";").replace("\n", " "),
            payload.get("status", ""),
            str(metrics.get("parts_ok", 0)),
            str(metrics.get("parts_scrap", 0)),
            str(metrics.get("cut_time_s", 0)),
            str(metrics.get("setup_time_s", 0)),
            log.get("created_utc", ""),
        ]
        lines.append(",".join(row))

    csv_content = "\n".join(lines)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="job_logs_{batch_execution_artifact_id[:8]}.csv"'
        },
    )
