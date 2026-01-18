# services/api/app/saw_lab/toolpaths_validate_router.py
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ToolpathsValidateRequest(BaseModel):
    """
    Validate a toolpaths artifact using static G-code checks.
    """
    toolpaths_artifact_id: str = Field(..., description="Artifact ID of saw_batch_toolpaths")
    safe_z_mm: float = Field(5.0, description="Minimum safe Z height")
    bounds_mm: Optional[Dict[str, float]] = Field(
        None,
        description="Optional hard bounds: min_x, max_x, min_y, max_y, min_z, max_z",
    )
    require_units_mm: bool = True
    require_absolute: bool = True
    require_xy_plane: bool = False
    require_spindle_on: bool = True
    require_feed_on_cut: bool = True


class ToolpathsValidateResponse(BaseModel):
    ok: bool
    errors: list[str]
    warnings: list[str]
    summary: Dict[str, Any]


@router.post("/toolpaths/validate", response_model=ToolpathsValidateResponse)
def validate_toolpaths(req: ToolpathsValidateRequest) -> ToolpathsValidateResponse:
    """
    Static validation of saw toolpaths G-code.

    This endpoint does NOT simulate motion.
    It performs fast, deterministic checks:
      - units (G21)
      - absolute mode (G90)
      - spindle on (M3/M4)
      - feed rates on G1
      - bounds
      - safe-Z usage
    """
    if not req.toolpaths_artifact_id:
        raise HTTPException(status_code=400, detail="toolpaths_artifact_id required")

    from .toolpaths_validate_service import validate_toolpaths_artifact_static

    result = validate_toolpaths_artifact_static(
        toolpaths_artifact_id=req.toolpaths_artifact_id,
        safe_z_mm=req.safe_z_mm,
        bounds_mm=req.bounds_mm,
        require_units_mm=req.require_units_mm,
        require_absolute=req.require_absolute,
        require_xy_plane=req.require_xy_plane,
        require_spindle_on=req.require_spindle_on,
        require_feed_on_cut=req.require_feed_on_cut,
    )

    return ToolpathsValidateResponse(**result)
