from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from app.saw_lab.schemas_compare import (
    SawCompareRequest,
    SawCompareResponse,
    SawCompareItem,
    SawCompareDecisionRequest,
    SawCompareDecisionResponse,
)
from app.services.saw_lab_compare_service import compare_saw_candidates
from app.services.saw_lab_batch_lookup_service import list_saw_compare_batches
from app.services.saw_lab_decision_service import create_saw_compare_decision


router = APIRouter(prefix="/api/saw", tags=["saw"])


@router.post("/compare", response_model=SawCompareResponse)
def compare_candidates(req: SawCompareRequest) -> SawCompareResponse:
    """
    Feasibility-only batch compare.
    Persists one RunArtifact per candidate and returns artifact IDs immediately.
    Router is wiring-only by design.
    """
    out = compare_saw_candidates(
        candidates=[c.model_dump() for c in req.candidates],
        batch_label=req.batch_label,
        session_id=req.session_id,
    )
    return SawCompareResponse(
        batch_label=req.batch_label,
        session_id=req.session_id,
        parent_artifact_id=out.get("parent_artifact_id"),
        items=[SawCompareItem(**i) for i in out["items"]],
    )


@router.get("/compare/batches")
def list_compare_batches(
    batch_label: Optional[str] = Query(default=None, description="Filter by batch_label"),
    session_id: Optional[str] = Query(default=None, description="Filter by session_id"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Convenience alias to retrieve compare batch parent artifacts without knowing IDs.

    Returns only event_type='saw_compare_batch' artifacts, newest first.

    Usage:
        GET /api/saw/compare/batches?batch_label=my-batch
        GET /api/saw/compare/batches?session_id=sess_123
    """
    return list_saw_compare_batches(
        batch_label=batch_label,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )


@router.post("/compare/approve", response_model=SawCompareDecisionResponse)
def approve_compare_selection(req: SawCompareDecisionRequest) -> SawCompareDecisionResponse:
    """
    Records an operator decision choosing a candidate from a compare batch.
    Creates a new RunArtifact kind='saw_compare_decision' (does not mutate batch).

    Governance rules:
    - Never mutates existing artifacts
    - Decision artifact is independently auditable
    - Even failures create ERROR artifacts for forensics
    """
    out = create_saw_compare_decision(
        parent_batch_artifact_id=req.parent_batch_artifact_id,
        selected_child_artifact_id=req.selected_child_artifact_id,
        approved_by=req.approved_by,
        reason=req.reason,
        ticket_id=req.ticket_id,
    )
    return SawCompareDecisionResponse(**out)
