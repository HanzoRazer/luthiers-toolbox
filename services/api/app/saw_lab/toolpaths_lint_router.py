from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


class ToolpathsLintRequest(BaseModel):
    toolpaths_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    tool_kind: str = "saw"

    machine_profile_artifact_id: Optional[str] = None
    safe_z_mm: float = 5.0
    bounds_mm: Optional[Dict[str, float]] = None

    require_units_mm: bool = True
    require_absolute: bool = True
    require_xy_plane: bool = False
    require_spindle_on: bool = True
    require_feed_on_cut: bool = True


class ToolpathsLintResponse(BaseModel):
    lint_artifact_id: str
    ok: bool
    errors: list[str]
    warnings: list[str]
    summary: Dict[str, Any]


@router.post("/toolpaths/lint", response_model=ToolpathsLintResponse)
def lint_toolpaths(req: ToolpathsLintRequest) -> ToolpathsLintResponse:
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

    from .toolpaths_lint_service import write_toolpaths_lint_report_artifact

    out = write_toolpaths_lint_report_artifact(
        toolpaths_artifact_id=req.toolpaths_artifact_id,
        session_id=req.session_id,
        batch_label=req.batch_label,
        tool_kind=req.tool_kind,
        machine_profile_artifact_id=req.machine_profile_artifact_id,
        safe_z_mm=safe_z_mm,
        bounds_mm=bounds_mm,
        require_units_mm=req.require_units_mm,
        require_absolute=req.require_absolute,
        require_xy_plane=req.require_xy_plane,
        require_spindle_on=req.require_spindle_on,
        require_feed_on_cut=req.require_feed_on_cut,
    )

    result = out["result"]
    summary = result.get("summary") if isinstance(result, dict) else {}
    return ToolpathsLintResponse(
        lint_artifact_id=out["lint_artifact_id"],
        ok=bool(result.get("ok")),
        errors=list(result.get("errors") or []),
        warnings=list(result.get("warnings") or []),
        summary=summary if isinstance(summary, dict) else {},
    )
