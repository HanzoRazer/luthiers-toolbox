from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.pipeline_handoff import handoff_to_pipeline
from app.schemas.pipeline_handoff import (
    PipelineHandoffRequest,
    PipelineHandoffResponse,
)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/handoff", response_model=PipelineHandoffResponse)
def pipeline_handoff(req: PipelineHandoffRequest) -> PipelineHandoffResponse:
    try:
        result = handoff_to_pipeline(req)
        return PipelineHandoffResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=400, detail=str(exc)) from exc
