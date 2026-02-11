"""
Adaptive Pocketing DXF Upload Router
====================================

DXF file upload endpoint for adaptive pocket toolpath generation.

LANE: OPERATION
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md

Endpoints:
- POST /plan_from_dxf: Upload DXF → extract geometry → generate toolpath
"""

import os
import tempfile
from typing import Any, Dict, List

from ezdxf import readfile as dxf_readfile
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..adaptive_schemas import Loop, PlanIn
from .plan_router import plan

router = APIRouter(tags=["cam-adaptive"])


def _dxf_to_loops_from_bytes(data: bytes, layer_name: str = "GEOMETRY") -> List[Loop]:
    """
    Convert DXF bytes into adaptive Loop objects from the given layer.

    Extracts closed LWPOLYLINE entities from specified DXF layer and converts
    them to Loop objects for adaptive pocket planning.

    Args:
        data: DXF file content as bytes
        layer_name: DXF layer to extract geometry from (default: "GEOMETRY")

    Returns:
        List of Loop objects (first is outer boundary, rest are islands)

    Raises:
        HTTPException: If DXF is invalid or no closed polylines found on layer

    Notes:
        - Only processes closed LWPOLYLINE entities
        - Open polylines are silently ignored
        - Coordinates are extracted as (x, y) tuples
        - Z coordinates are ignored (2D pocketing only)
        - First loop should be outer boundary (CCW), rest islands (CW)
    """
    try:
        # ezdxf.read() with StringIO has issues with complex DXF files,
        # so we use a temp file approach with readfile() instead
        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            doc = dxf_readfile(tmp_path)
        finally:
            os.unlink(tmp_path)
    except HTTPException:  # WP-1: pass through HTTPException
        raise
    except Exception as exc:  # WP-1: governance catch-all — HTTP endpoint
        raise HTTPException(status_code=400, detail=f"Invalid DXF: {exc}") from exc

    msp = doc.modelspace()
    loops: List[Loop] = []

    # Extract closed polylines from specified layer
    for entity in msp.query(f'LWPOLYLINE[layer=="{layer_name}"]'):
        if not getattr(entity, "closed", False):
            continue
        pts = []
        for p in entity.get_points():
            x, y = float(p[0]), float(p[1])
            pts.append((x, y))
        if pts:
            loops.append(Loop(pts=pts))

    if not loops:
        raise HTTPException(
            status_code=400,
            detail=f"No closed polylines found on '{layer_name}' layer.",
        )
    return loops


@router.post("/plan_from_dxf")
async def plan_from_dxf(
    file: UploadFile = File(..., description="DXF with GEOMETRY layer"),
    tool_d: float = Form(..., description="Tool diameter in mm"),
    units: str = Form("mm"),
    stepover: float = Form(0.45),
    stepdown: float = Form(2.0),
    margin: float = Form(0.5),
    strategy: str = Form("Spiral"),
    smoothing: float = Form(0.5),
    feed_xy: float = Form(1200.0),
    safe_z: float = Form(5.0),
    z_rough: float = Form(-1.5),
    corner_radius_min: float = Form(1.0),
    target_stepover: float = Form(0.45),
    slowdown_feed_pct: float = Form(60.0),
) -> Dict[str, Any]:
    """
    Bridge endpoint: Upload DXF → extract geometry → generate adaptive toolpath.

    Accepts DXF file upload (multipart/form-data) and extracts closed polylines
    from GEOMETRY layer. Converts to Loop objects and calls existing /plan logic.

    Form Parameters:
        file: DXF file (closed polylines on GEOMETRY layer)
        tool_d: Tool diameter in mm (required)
        units: "mm" or "inch" (default: "mm")
        stepover: Stepover as fraction of tool diameter (default: 0.45)
        stepdown: Z depth per pass in mm (default: 2.0)
        margin: Clearance from boundary in mm (default: 0.5)
        strategy: "Spiral" or "Lanes" (default: "Spiral")
        smoothing: Arc tolerance for rounded joins (default: 0.5)
        feed_xy: Cutting feed rate (default: 1200.0 mm/min)
        safe_z: Retract height (default: 5.0 mm)
        z_rough: Cutting depth (default: -1.5 mm)
        corner_radius_min: Min radius for fillet injection (default: 1.0 mm)
        target_stepover: Adaptive stepover target (default: 0.45)
        slowdown_feed_pct: Feed reduction percentage (default: 60.0%)

    Returns:
        {
            "request": <PlanIn dict with extracted loops>,
            "plan": <PlanOut dict from /plan endpoint>
        }

    Example Usage (curl):
        ```
        curl -X POST http://localhost:8000/api/cam/pocket/adaptive/plan_from_dxf \\
          -F "file=@pocket.dxf" \\
          -F "tool_d=6.0" \\
          -F "stepover=0.45" \\
          -F "strategy=Spiral"
        ```

    Notes:
        - DXF must contain closed LWPOLYLINE entities on "GEOMETRY" layer
        - First polyline is outer boundary (CCW), rest are islands (CW)
        - All geometry converted to Loop objects before planning
        - Uses existing /plan logic for consistent results
    """
    data = await file.read()
    loops = _dxf_to_loops_from_bytes(data, layer_name="GEOMETRY")

    body = PlanIn(
        loops=loops,
        units=units,
        tool_d=tool_d,
        stepover=stepover,
        stepdown=stepdown,
        margin=margin,
        strategy=strategy,
        smoothing=smoothing,
        climb=True,
        feed_xy=feed_xy,
        safe_z=safe_z,
        z_rough=z_rough,
        corner_radius_min=corner_radius_min,
        target_stepover=target_stepover,
        slowdown_feed_pct=slowdown_feed_pct,
    )

    plan_result = plan(body)

    return {
        "request": body.dict(),
        "plan": plan_result.dict() if hasattr(plan_result, 'dict') else plan_result,
    }
