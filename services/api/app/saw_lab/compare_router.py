from __future__ import annotations

from fastapi import APIRouter

from app.saw_lab.schemas_compare import SawCompareRequest, SawCompareResponse, SawCompareItem
from app.services.saw_lab_compare_service import compare_saw_candidates


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
