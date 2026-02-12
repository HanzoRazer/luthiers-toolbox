"""
Consolidated toolpaths router.

Combines:
- toolpaths_lookup_router (GET /toolpaths/latest, /toolpaths/latest-by-batch)
- toolpaths_validate_router (POST /toolpaths/validate)
- toolpaths_lint_router (POST /toolpaths/lint)
- toolpaths_download_router (GET /toolpaths/{id}/download/gcode)

5 routes total covering toolpath operations:
  lookup → validate → lint → download
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.safety import safety_critical


router = APIRouter(prefix="/api/saw/batch", tags=["Saw", "Batch"])


# =============================================================================
# Schemas: Lookup
# =============================================================================


class LatestToolpathsByExecutionResponse(BaseModel):
    batch_execution_artifact_id: str
    session_id: Optional[str] = None
    batch_label: Optional[str] = None
    tool_kind: str = "saw"
    latest_toolpaths_artifact_id: Optional[str] = None
    attachments: Optional[dict] = None


class LatestToolpathsByBatchResponse(BaseModel):
    session_id: str
    batch_label: str
    tool_kind: str = "saw"
    latest_execution_artifact_id: Optional[str] = None
    latest_toolpaths_artifact_id: Optional[str] = None
    attachments: Optional[dict] = None


# =============================================================================
# Schemas: Validate
# =============================================================================


class ToolpathsValidateRequest(BaseModel):
    toolpaths_artifact_id: str = Field(..., description="Artifact ID of saw_batch_toolpaths")
    safe_z_mm: float = Field(5.0, description="Minimum safe Z height")
    bounds_mm: Optional[Dict[str, float]] = Field(
        None,
        description="Optional hard bounds: min_x, max_x, min_y, max_y, min_z, max_z",
    )
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


# =============================================================================
# Schemas: Lint
# =============================================================================


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


# =============================================================================
# Routes: Lookup
# =============================================================================


@router.get("/toolpaths/latest", response_model=LatestToolpathsByExecutionResponse)
def latest_toolpaths_by_execution(
    batch_execution_artifact_id: str,
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    tool_kind: str = "saw",
) -> LatestToolpathsByExecutionResponse:
    """execution -> latest toolpaths artifact (+ attachments block if present)."""
    if not batch_execution_artifact_id:
        raise HTTPException(status_code=400, detail="batch_execution_artifact_id required")

    from .toolpaths_lookup_service import resolve_latest_toolpaths_for_execution

    tp = resolve_latest_toolpaths_for_execution(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
    )

    tp_id = None
    attachments = None
    if isinstance(tp, dict):
        v = tp.get("id") or tp.get("artifact_id")
        tp_id = str(v) if v else None
        payload = tp.get("payload") or tp.get("data") or {}
        if isinstance(payload, dict) and isinstance(payload.get("attachments"), dict):
            attachments = payload["attachments"]

    return LatestToolpathsByExecutionResponse(
        batch_execution_artifact_id=batch_execution_artifact_id,
        session_id=session_id,
        batch_label=batch_label,
        tool_kind=tool_kind,
        latest_toolpaths_artifact_id=tp_id,
        attachments=attachments,
    )


@router.get("/toolpaths/latest-by-batch", response_model=LatestToolpathsByBatchResponse)
def latest_toolpaths_by_batch(
    session_id: str,
    batch_label: str,
    tool_kind: str = "saw",
) -> LatestToolpathsByBatchResponse:
    """batch -> latest execution -> latest toolpaths"""
    if not session_id or not batch_label:
        raise HTTPException(status_code=400, detail="session_id and batch_label required")

    from .toolpaths_lookup_service import resolve_latest_toolpaths_for_batch

    out = resolve_latest_toolpaths_for_batch(session_id=session_id, batch_label=batch_label, tool_kind=tool_kind)
    return LatestToolpathsByBatchResponse(**out)


# =============================================================================
# Route: Validate
# =============================================================================


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

    summary = result.get("summary") if isinstance(result, dict) else None
    if isinstance(summary, dict):
        summary["applied_safe_z_mm"] = safe_z_mm
        summary["applied_bounds_mm"] = bounds_mm
        summary["machine_profile_artifact_id"] = req.machine_profile_artifact_id

    return ToolpathsValidateResponse(**result)


# =============================================================================
# Route: Lint
# =============================================================================


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


# =============================================================================
# Route: Download
# =============================================================================


@router.get("/toolpaths/{toolpaths_artifact_id}/download/gcode")
def download_toolpaths_gcode(toolpaths_artifact_id: str):
    """
    Convenience download:
      toolpaths artifact -> gcode attachment sha256 -> redirect to global attachment fetch
    """
    if not toolpaths_artifact_id:
        raise HTTPException(status_code=400, detail="toolpaths_artifact_id required")

    from app.rmos.runs_v2 import store as runs_store

    art = runs_store.get_run(toolpaths_artifact_id)
    if not isinstance(art, dict):
        raise HTTPException(status_code=404, detail="toolpaths artifact not found")

    payload = art.get("payload") or art.get("data") or {}
    if not isinstance(payload, dict):
        payload = {}

    attachments = payload.get("attachments") or {}
    if not isinstance(attachments, dict):
        attachments = {}

    sha = attachments.get("gcode_sha256") or attachments.get("gcode") or attachments.get("sha256")
    if not isinstance(sha, str) or not sha:
        raise HTTPException(status_code=409, detail="toolpaths artifact has no gcode attachment sha256")

    return RedirectResponse(url=f"/api/rmos/attachments/{sha}", status_code=302)
