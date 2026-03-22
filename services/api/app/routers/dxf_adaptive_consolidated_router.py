"""
DXF Adaptive Router (Consolidated)
===================================

DXF file to adaptive pocket toolpath conversion endpoints.

Consolidated from:
    - dxf_plan_router.py (1 route)
    - cam_dxf_adaptive_router.py (1 route)

Endpoints (under /api/cam):
    POST /plan_from_dxf          - Extract DXF → plan JSON (for editing)
    POST /dxf_adaptive_plan_run  - DXF → adaptive toolpath (direct run)
"""
from __future__ import annotations

import io
import logging
from typing import Any, Dict, Literal, Optional

import ezdxf
from ezdxf.lldxf.const import DXFStructureError
import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from ..cam.dxf_preflight import DXFPreflight
from ..routers.blueprint_cam import extract_loops_from_dxf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cam", tags=["cam", "dxf", "adaptive"])


# ===========================================================================
# PLAN EXTRACTION (for editing before run)
# ===========================================================================

@router.post("/plan_from_dxf")
async def plan_from_dxf(
    file: UploadFile = File(..., description="DXF file"),
    units: Literal["mm", "inch"] = Form("mm"),
    tool_d: float = Form(6.0, description="Tool diameter"),
    geometry_layer: Optional[str] = Form(
        None, description="Optional explicit geometry layer; defaults to 'GEOMETRY'."
    ),
    stepover: float = Form(0.45, description="Stepover fraction (0.0-1.0)"),
    stepdown: float = Form(2.0, description="Stepdown in mm/inch"),
    margin: float = Form(0.5, description="Margin from boundary in mm/inch"),
    strategy: Literal["Spiral", "Lanes"] = Form("Spiral"),
    feed_xy: float = Form(1200.0, description="XY feed rate"),
    safe_z: float = Form(5.0, description="Safe Z height"),
    z_rough: float = Form(-1.5, description="Rough cut depth"),
) -> Dict[str, Any]:
    """
    Convert DXF file into adaptive pocket plan request (for editing).

    Returns loops JSON + adaptive parameters ready for /api/cam/pocket/adaptive/plan.
    """
    from app.cam.dxf_upload_guard import read_dxf_with_validation
    from app.cam.dxf_validation_gate import enforce_dxf_validation

    try:
        dxf_bytes = await read_dxf_with_validation(file)

        # MANDATORY: Validate DXF geometry before G-code export (FAIL-CLOSED)
        enforce_dxf_validation(dxf_bytes, file.filename or "upload.dxf")
    except DXFStructureError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid DXF file structure: {exc}"
        ) from exc

    # Optional preflight for debug info
    preflight_debug: Optional[Dict[str, Any]] = None
    try:
        preflight = DXFPreflight(dxf_bytes, filename=file.filename or "upload.dxf")
        report = preflight.run_all_checks()
        preflight_debug = {
            "passed": report.passed,
            "layers": report.layers,
            "issue_count": len(report.issues),
        }
    except (ValueError, KeyError, AttributeError, OSError) as e:
        preflight_debug = {"error": str(e)}

    # Extract loops
    layer_name = geometry_layer or "GEOMETRY"
    try:
        loops, warnings = extract_loops_from_dxf(dxf_bytes, layer_name=layer_name)
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, OSError) as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract loops: {str(e)}") from e

    if not loops:
        raise HTTPException(
            status_code=400,
            detail=f"No closed loops found on layer '{layer_name}'. "
                   f"Available layers: {preflight_debug.get('layers', [])}"
        )

    plan = {
        "loops": [{"pts": loop.pts} for loop in loops],
        "units": units,
        "tool_d": tool_d,
        "stepover": stepover,
        "stepdown": stepdown,
        "margin": margin,
        "strategy": strategy,
        "feed_xy": feed_xy,
        "safe_z": safe_z,
        "z_rough": z_rough,
    }

    return {
        "plan": plan,
        "debug": {
            "source": "dxf",
            "filename": file.filename,
            "layer": layer_name,
            "loop_count": len(loops),
            "warnings": warnings,
            "preflight": preflight_debug,
        },
    }


# ===========================================================================
# DIRECT RUN (DXF → toolpath in one call)
# ===========================================================================

def _dxf_to_adaptive_request(
    dxf_bytes: bytes,
    tool_d: float,
    *,
    units: str = "mm",
    geometry_layer: str = "GEOMETRY",
    stepover: float = 0.45,
    stepdown: float = 2.0,
    margin: float = 0.5,
    strategy: str = "Spiral",
    feed_xy: float = 1200.0,
    safe_z: float = 5.0,
    z_rough: float = -1.5,
) -> Dict[str, Any]:
    """Convert DXF closed polylines to Adaptive Pocket request body."""
    try:
        data_stream = io.BytesIO(dxf_bytes)
        doc = ezdxf.read(data_stream)
    except HTTPException:
        raise
    except (ValueError, IOError, ezdxf.DXFError) as exc:  # audited: DXF-parse
        logger.exception("Failed to parse DXF for adaptive pocket")
        raise HTTPException(status_code=400, detail=f"Failed to parse DXF: {exc}") from exc

    msp = doc.modelspace()
    loops = []

    query_str = f'LWPOLYLINE[layer=="{geometry_layer}"]'
    for entity in msp.query(query_str):
        if not entity.closed:
            continue
        pts = [(p[0], p[1]) for p in entity.get_points()]
        if len(pts) >= 3:
            loops.append({"pts": pts})

    if not loops:
        raise HTTPException(
            status_code=400,
            detail=f"No closed polylines found on layer {geometry_layer!r}."
        )

    return {
        "loops": loops,
        "tool_d": float(tool_d),
        "units": units,
        "stepover": float(stepover),
        "stepdown": float(stepdown),
        "margin": float(margin),
        "strategy": strategy,
        "feed_xy": float(feed_xy),
        "safe_z": float(safe_z),
        "z_rough": float(z_rough),
    }


@router.post("/dxf_adaptive_plan_run")
async def dxf_adaptive_plan_run(
    request: Request,
    file: UploadFile = File(...),
    units: str = Form("mm"),
    tool_d: float = Form(...),
    geometry_layer: str = Form("GEOMETRY"),
    stepover: float = Form(0.45),
    stepdown: float = Form(2.0),
    margin: float = Form(0.5),
    strategy: str = Form("Spiral"),
    feed_xy: float = Form(1200.0),
    safe_z: float = Form(5.0),
    z_rough: float = Form(-1.5),
) -> Dict[str, Any]:
    """
    DXF → Adaptive Pocket → Toolpath (direct run).

    Reads DXF, extracts loops, calls adaptive planner, returns toolpath.
    """
    try:
        dxf_bytes = await file.read()
    except HTTPException:
        raise
    except (IOError, ValueError) as exc:  # audited: file-read
        logger.exception("Failed to read DXF file")
        raise HTTPException(status_code=400, detail=f"Failed to read DXF file: {exc}") from exc

    body = _dxf_to_adaptive_request(
        dxf_bytes=dxf_bytes,
        tool_d=tool_d,
        units=units,
        geometry_layer=geometry_layer,
        stepover=stepover,
        stepdown=stepdown,
        margin=margin,
        strategy=strategy,
        feed_xy=feed_xy,
        safe_z=safe_z,
        z_rough=z_rough,
    )

    base_url = str(request.base_url).rstrip("/")
    adaptive_url = f"{base_url}/api/cam/pocket/adaptive/plan"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(adaptive_url, json=body, timeout=30.0)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to call adaptive planner: {exc}") from exc

    if resp.status_code != 200:
        try:
            detail = resp.json()
        except (ValueError, TypeError):
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)

    return resp.json()


__all__ = ["router"]
