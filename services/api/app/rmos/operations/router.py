"""
RMOS Operations Router

LANE: OPERATION (governance-compliant)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

FastAPI router for operation execution and planning endpoints.
Mount at: /api/rmos/operations
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

from fastapi.responses import StreamingResponse

from .adapter import (
    execute_operation,
    plan_operation,
    OperationResult,
    PlanResult,
)
from .export import export_run_to_zip, get_export_filename, ExportError


router = APIRouter(
    prefix="/api/rmos/operations",
    tags=["RMOS Operations", "OPERATION Lane"],
)


# =============================================================================
# Request/Response Schemas
# =============================================================================

class ExecuteRequest(BaseModel):
    """Request body for operation execution."""
    cam_intent_v1: Dict[str, Any] = Field(..., description="CAM intent payload")
    feasibility: Dict[str, Any] = Field(..., description="Server-computed feasibility")
    parent_plan_run_id: Optional[str] = Field(None, description="Parent plan for lineage")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExecuteResponse(BaseModel):
    """Response from operation execution."""
    run_id: str
    status: str
    risk_level: str
    event_type: str
    block_reason: Optional[str] = None
    gcode_sha256: Optional[str] = None
    warnings: list = Field(default_factory=list)


class PlanRequestBody(BaseModel):
    """Request body for operation planning."""
    cam_intent_v1: Dict[str, Any] = Field(..., description="CAM intent payload")
    feasibility: Optional[Dict[str, Any]] = Field(None, description="Optional pre-computed feasibility")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PlanResponse(BaseModel):
    """Response from operation planning."""
    run_id: str
    status: str
    risk_level: Optional[str] = None
    event_type: str
    plan: Dict[str, Any] = Field(default_factory=dict)
    warnings: list = Field(default_factory=list)


# =============================================================================
# Generic Endpoints (tool_id in path)
# =============================================================================

@router.post(
    "/{tool_id}/execute",
    response_model=ExecuteResponse,
    summary="Execute operation with governance",
    description="Execute a machine operation with full feasibility gate and artifact persistence.",
    responses={
        200: {"description": "Execution successful"},
        409: {"description": "Execution blocked by feasibility gate"},
    },
)
async def execute_operation_endpoint(
    tool_id: str,
    body: ExecuteRequest,
    request: Request,
    x_request_id: Optional[str] = Header(None, alias="X-Request-Id"),
) -> ExecuteResponse:
    """
    Execute an operation for the specified tool.

    - **tool_id**: Tool identifier (e.g., 'saw_v1', 'cam_roughing_v1')
    - **cam_intent_v1**: The CAM intent payload
    - **feasibility**: Server-computed feasibility (REQUIRED)
    - **parent_plan_run_id**: Optional parent plan for lineage tracking

    Returns:
    - 200 OK with execution artifact if GREEN/YELLOW
    - 409 Conflict if RED/UNKNOWN (still creates BLOCKED artifact)
    """
    # Derive mode from tool_id (e.g., 'saw_v1' -> 'saw')
    mode = tool_id.split("_")[0] if "_" in tool_id else tool_id

    result: OperationResult = execute_operation(
        tool_id=tool_id,
        mode=mode,
        cam_intent_v1=body.cam_intent_v1,
        feasibility=body.feasibility,
        request_id=x_request_id,
        parent_plan_run_id=body.parent_plan_run_id,
        meta=body.meta,
    )

    # Return 409 for BLOCKED status (per governance contract)
    if result.status == "BLOCKED":
        raise HTTPException(
            status_code=409,
            detail={
                "run_id": result.run_id,
                "status": result.status,
                "risk_level": result.risk_level,
                "event_type": result.event_type,
                "block_reason": result.block_reason,
                "warnings": result.warnings,
            },
        )

    return ExecuteResponse(
        run_id=result.run_id,
        status=result.status,
        risk_level=result.risk_level,
        event_type=result.event_type,
        gcode_sha256=result.gcode_sha256,
        warnings=result.warnings,
    )


@router.post(
    "/{tool_id}/plan",
    response_model=PlanResponse,
    summary="Create operation plan",
    description="Create a plan artifact for later execution with lineage tracking.",
)
async def plan_operation_endpoint(
    tool_id: str,
    body: PlanRequestBody,
    request: Request,
    x_request_id: Optional[str] = Header(None, alias="X-Request-Id"),
) -> PlanResponse:
    """
    Create an operation plan for the specified tool.

    Plans capture intent without generating G-code. Use the returned
    run_id as parent_plan_run_id when executing.

    - **tool_id**: Tool identifier
    - **cam_intent_v1**: The CAM intent payload
    - **feasibility**: Optional pre-computed feasibility
    """
    mode = tool_id.split("_")[0] if "_" in tool_id else tool_id

    result: PlanResult = plan_operation(
        tool_id=tool_id,
        mode=mode,
        cam_intent_v1=body.cam_intent_v1,
        feasibility=body.feasibility,
        request_id=x_request_id,
        meta=body.meta,
    )

    return PlanResponse(
        run_id=result.run_id,
        status=result.status,
        risk_level=result.risk_level,
        event_type=result.event_type,
        plan=result.plan,
        warnings=result.warnings,
    )


# =============================================================================
# ZIP Export (Bundle 04)
# =============================================================================

@router.get(
    "/{run_id}/export.zip",
    summary="Export operation as ZIP",
    description="Download a run artifact and all associated data as an auditable ZIP file.",
    responses={
        200: {
            "description": "ZIP file download",
            "content": {"application/zip": {}},
        },
        404: {"description": "Run not found"},
    },
)
async def export_operation_zip(
    run_id: str,
    x_request_id: Optional[str] = Header(None, alias="X-Request-Id"),
) -> StreamingResponse:
    """
    Export a run artifact as a ZIP file.

    ZIP contains:
    - meta/artifact.json - Full artifact
    - meta/summary.json - Quick summary
    - meta/hashes.json - SHA256 hashes
    - inputs/cam_intent_v1.json - Original intent
    - inputs/feasibility.json - Server feasibility
    - outputs/gcode.nc - G-code (if generated)
    - outputs/plan.json - Plan (if generated)
    - audit/lineage.json - Parent references
    - audit/decision.json - Safety decision
    """
    try:
        zip_buffer = export_run_to_zip(run_id)
        filename = get_export_filename(run_id)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Request-Id": x_request_id or "",
            },
        )
    except ExportError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


# =============================================================================
# Health Check
# =============================================================================

@router.get(
    "/health",
    summary="Operations health check",
    tags=["Health"],
)
async def operations_health():
    """Health check for operations endpoints."""
    return {"status": "ok", "lane": "OPERATION", "module": "operations"}
