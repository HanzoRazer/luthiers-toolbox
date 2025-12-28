"""
Saw Lab Batch Router

API endpoints for batch operations:
  - POST /api/saw/batch/spec      - Create batch specification
  - POST /api/saw/batch/plan      - Generate plan from spec
  - POST /api/saw/batch/approve   - Approve plan with execution order
  - POST /api/saw/batch/toolpaths - Generate toolpaths from decision
  - GET  /api/saw/batch/execution - Lookup latest execution for decision
  - GET  /api/saw/batch/executions/by-decision - List executions by decision
  - GET  /api/saw/batch/executions - List execution artifacts
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException

from app.saw_lab.schemas_batch import (
    SawBatchSpecRequest,
    SawBatchSpecResponse,
    SawBatchPlanRequest,
    SawBatchPlanResponse,
    SawBatchPlanChooseRequest,
    SawBatchPlanChooseResponse,
    SawBatchToolpathsRequest,
    SawBatchToolpathsResponse,
)
from app.services.saw_lab_batch_spec_service import create_batch_spec
from app.services.saw_lab_batch_plan_service import create_batch_plan
from app.services.saw_lab_batch_decision_service import create_batch_plan_decision
from app.services.saw_lab_batch_toolpaths_service import generate_batch_toolpaths_from_decision
from app.services.saw_lab_batch_execution_lookup_service import (
    latest_execution_for_decision,
    list_executions_for_decision,
)


router = APIRouter(prefix="/api/saw/batch", tags=["saw-batch"])


@router.post("/spec", response_model=SawBatchSpecResponse)
def create_spec(req: SawBatchSpecRequest) -> SawBatchSpecResponse:
    """
    Create a batch specification from a list of items.

    The spec artifact stores the input items and generates op_ids for tracking.
    """
    out = create_batch_spec(
        batch_label=req.batch_label,
        session_id=req.session_id,
        tool_id=req.tool_id,
        items=[item.model_dump() for item in req.items],
    )
    return SawBatchSpecResponse(**out)


@router.post("/plan", response_model=SawBatchPlanResponse)
def generate_plan(req: SawBatchPlanRequest) -> SawBatchPlanResponse:
    """
    Generate a batch plan from a spec artifact.

    Groups items into setups by material and computes feasibility for each op.
    """
    out = create_batch_plan(batch_spec_artifact_id=req.batch_spec_artifact_id)
    return SawBatchPlanResponse(**out)


@router.post("/approve", response_model=SawBatchPlanChooseResponse)
def approve_plan(req: SawBatchPlanChooseRequest) -> SawBatchPlanChooseResponse:
    """
    Approve a batch plan with operator-defined execution order.

    Creates a decision artifact that locks in the setup and op order.
    """
    out = create_batch_plan_decision(
        batch_plan_artifact_id=req.batch_plan_artifact_id,
        approved_by=req.approved_by,
        reason=req.reason,
        setup_order=req.setup_order,
        op_order=req.op_order,
    )
    return SawBatchPlanChooseResponse(**out)


@router.post("/toolpaths", response_model=SawBatchToolpathsResponse)
def toolpaths_from_batch_decision(req: SawBatchToolpathsRequest) -> SawBatchToolpathsResponse:
    """
    Batch execution scaffold:
    - consumes saw_batch_decision
    - recomputes feasibility per op
    - generates toolpaths per op when feasible
    - persists child op artifacts + one parent execution artifact
    """
    out = generate_batch_toolpaths_from_decision(batch_decision_artifact_id=req.batch_decision_artifact_id)
    return SawBatchToolpathsResponse(**out)


@router.get("/execution")
def get_latest_execution_for_decision(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact id (kind='saw_batch_decision')"),
):
    """
    Convenience alias:
      GET /api/saw/batch/execution?batch_decision_artifact_id=...
    Returns the newest parent execution artifact that was produced from this decision.
    """
    it = latest_execution_for_decision(batch_decision_artifact_id)
    if not it:
        raise HTTPException(status_code=404, detail="No execution artifact found for batch_decision_artifact_id")
    return it


@router.get("/executions/by-decision")
def list_executions_by_decision(
    batch_decision_artifact_id: str = Query(..., description="Decision artifact id (kind='saw_batch_decision')"),
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Convenience alias:
      GET /api/saw/batch/executions/by-decision?batch_decision_artifact_id=...&limit=&offset=
    Returns a newest-first list of parent execution artifacts produced from this decision.
    """
    return list_executions_for_decision(
        batch_decision_artifact_id=batch_decision_artifact_id,
        limit=limit,
        offset=offset,
    )


@router.get("/executions")
def list_executions(
    batch_label: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[Dict[str, Any]]:
    """
    List batch execution artifacts, optionally filtered by batch_label or session_id.
    """
    from app.rmos.run_artifacts.store import query_run_artifacts

    return query_run_artifacts(
        kind="saw_batch_execution",
        batch_label=batch_label,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
