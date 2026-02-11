from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.safety import safety_critical


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ToolpathsValidateRequest(BaseModel):
    toolpaths_artifact_id: str = Field(..., description="Artifact ID of saw_batch_toolpaths")

    # either set these directly...
    safe_z_mm: float = Field(5.0, description="Minimum safe Z height")
    bounds_mm: Optional[Dict[str, float]] = Field(
        None,
        description="Optional hard bounds: min_x, max_x, min_y, max_y, min_z, max_z",
    )

    # ...or have them pulled from a machine profile artifact
    machine_profile_artifact_id: Optional[str] = Field(
        None,
        description="If provided, overrides safe_z_mm/bounds_mm from machine profile payload.",
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
@safety_critical
def validate_toolpaths(req: ToolpathsValidateRequest) -> ToolpathsValidateResponse:
    if not req.toolpaths_artifact_id:
        raise HTTPException(status_code=400, detail="toolpaths_artifact_id required")

    safe_z_mm = req.safe_z_mm
    bounds_mm = req.bounds_mm

    if req.machine_profile_artifact_id:
        from .machine_profile_resolver import resolve_machine_profile_constraints

        c = resolve_machine_profile_constraints(machine_profile_artifact_id=req.machine_profile_artifact_id)
        if isinstance(c.get("safe_z_mm"), (int, float)):
            safe_z_mm = float(c["safe_z_mm"])
        if isinstance(c.get("bounds_mm"), dict):
            bounds_mm = c["bounds_mm"]

    from .toolpaths_validate_service import validate_toolpaths_artifact_static

    result = validate_toolpaths_artifact_static(
        toolpaths_artifact_id=req.toolpaths_artifact_id,
        safe_z_mm=safe_z_mm,
        bounds_mm=bounds_mm,
        require_units_mm=req.require_units_mm,
        require_absolute=req.require_absolute,
        require_xy_plane=req.require_xy_plane,
        require_spindle_on=req.require_spindle_on,
        require_feed_on_cut=req.require_feed_on_cut,
    )

    # stamp which constraints were applied (for UI)
    summary = result.get("summary") if isinstance(result, dict) else None
    if isinstance(summary, dict):
        summary["applied_safe_z_mm"] = safe_z_mm
        summary["applied_bounds_mm"] = bounds_mm
        summary["machine_profile_artifact_id"] = req.machine_profile_artifact_id

    return ToolpathsValidateResponse(**result)
