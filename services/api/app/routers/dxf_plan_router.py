# services/api/app/routers/dxf_plan_router.py
"""
DXF → Adaptive Plan router.

Provides lightweight endpoint to convert DXF to adaptive plan request (loops JSON).
Uses existing blueprint_cam_bridge.extract_loops_from_dxf() infrastructure.
"""
from __future__ import annotations

from typing import Literal, Optional, Dict, Any, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from ..routers.blueprint_cam_bridge import extract_loops_from_dxf
from ..cam.dxf_preflight import DXFPreflight

router = APIRouter(prefix="/cam", tags=["cam", "dxf", "adaptive"])


@router.post("/plan_from_dxf")
async def plan_from_dxf(
    file: UploadFile = File(..., description="DXF file"),
    units: Literal["mm", "inch"] = Form("mm"),
    tool_d: float = Form(6.0, description="Tool diameter"),
    geometry_layer: Optional[str] = Form(
        None,
        description="Optional explicit geometry layer; defaults to 'GEOMETRY'.",
    ),
    stepover: float = Form(0.45, description="Stepover fraction (0.0-1.0)"),
    stepdown: float = Form(2.0, description="Stepdown in mm/inch"),
    margin: float = Form(0.5, description="Margin from boundary in mm/inch"),
    strategy: Literal["Spiral", "Lanes"] = Form("Spiral"),
    feed_xy: float = Form(1200.0, description="XY feed rate"),
    safe_z: float = Form(5.0, description="Safe Z height"),
    z_rough: float = Form(-1.5, description="Rough cut depth"),
):
    """
    Convert DXF file into adaptive pocket plan request.

    Returns loops JSON + adaptive parameters ready for /api/cam/pocket/adaptive/plan.
    
    **Workflow:**
    1. Upload DXF
    2. Extract loops from specified layer (or auto-detect)
    3. Return plan with loops + tool parameters
    4. Front-end can send to adaptive kernel or edit loops
    
    **Example:**
    ```bash
    curl -F "file=@body.dxf" -F "tool_d=6.0" -F "units=mm" \\
         http://localhost:8000/cam/plan_from_dxf
    ```
    """
    if not file.filename or not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Only .dxf files are supported.")

    dxf_bytes = await file.read()
    if not dxf_bytes:
        raise HTTPException(status_code=400, detail="Empty DXF file.")

    # Optional preflight for debug info
    preflight_debug: Optional[Dict[str, Any]] = None
    try:
        preflight = DXFPreflight(dxf_bytes, filename=file.filename)
        report = preflight.validate()
        preflight_debug = {
            "ok": report.ok,
            "units": report.units,
            "layers": report.layers,
            "candidate_layers": report.candidate_layers,
            "issue_count": len(report.issues),
            "critical_count": sum(1 for i in report.issues if i.level == "critical"),
            "error_count": sum(1 for i in report.issues if i.level == "error"),
        }
    except Exception as e:
        # Preflight errors are non-fatal for plan extraction
        preflight_debug = {"error": str(e)}

    # Extract loops
    layer_name = geometry_layer or "GEOMETRY"
    try:
        loops, warnings = extract_loops_from_dxf(dxf_bytes, layer_name=layer_name)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract loops from DXF: {str(e)}"
        ) from e

    if not loops:
        raise HTTPException(
            status_code=400,
            detail=f"No closed loops found on layer '{layer_name}'. "
                   f"Available layers: {preflight_debug.get('layers', [])}"
        )

    # Build adaptive plan request
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
