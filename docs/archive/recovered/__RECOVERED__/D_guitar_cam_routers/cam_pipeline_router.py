# services/api/app/routers/cam_pipeline_router.py

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.pipeline_ops_rosette import (
    RosetteCamOpInput,
    RosetteCamOpResult,
    run_rosette_cam_op,
)

router = APIRouter(prefix="/api/cam/pipeline", tags=["cam_pipeline"])


class RosetteCamPipelineOp(BaseModel):
    """Rosette CAM pipeline operation."""
    op: Literal["RosetteCam"] = "RosetteCam"
    input: RosetteCamOpInput


# Later you can add more op types to this union:
#   - AdaptivePocket
#   - ReliefRoughing
#   - etc.
PipelineOp = Union[RosetteCamPipelineOp]


class PipelineRunRequest(BaseModel):
    """Request payload for the unified CAM pipeline runner."""

    steps: List[PipelineOp] = Field(
        ..., description="Ordered list of pipeline steps to execute"
    )
    meta: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class PipelineStepResult(BaseModel):
    """Result payload for a single pipeline step."""

    op: str
    index: int
    result: Dict[str, Any]


class PipelineRunResponse(BaseModel):
    """Response from pipeline execution."""
    steps: List[PipelineStepResult]


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(req: PipelineRunRequest) -> PipelineRunResponse:
    """Unified CAM pipeline entrypoint (currently RosetteCam only)."""

    results: List[PipelineStepResult] = []

    for idx, step in enumerate(req.steps):
        try:
            if isinstance(step, RosetteCamPipelineOp):
                rosette_result = run_rosette_cam_op(step.input)
                results.append(
                    PipelineStepResult(
                        op="RosetteCam",
                        index=idx,
                        result=rosette_result.model_dump(),
                    )
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported pipeline op type at index {idx}",
                )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PipelineRunResponse(steps=results)
