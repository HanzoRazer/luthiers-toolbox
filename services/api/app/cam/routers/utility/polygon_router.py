"""
CAM Polygon Offset Router

Polygon offset G-code generation for pocket milling.

Migrated from: routers/cam_polygon_offset_router.py

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /polygon_offset.nc    - Generate G-code for polygon offsetting
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from ...polygon_offset_n17 import toolpath_offsets
from ....util.gcode_emit_advanced import emit_xy_with_arcs
from ....util.gcode_emit_basic import emit_xy_polyline_nc

router = APIRouter()

Pt = Tuple[float, float]


class PolyOffsetReq(BaseModel):
    """Request model for polygon offset G-code generation"""
    polygon: List[Tuple[float, float]]
    tool_dia: float = 6.0
    stepover: float = 2.0
    inward: bool = True
    z: float = -1.5
    safe_z: float = 5.0
    units: str = "mm"
    feed: float = 600.0
    feed_arc: Optional[float] = None
    feed_floor: Optional[float] = None
    join_type: str = "round"
    arc_tolerance: float = 0.25
    link_mode: str = "arc"
    link_radius: float = 1.0
    spindle: int = 12000
    post: Optional[str] = None


@router.post("/polygon_offset.nc", response_class=Response)
def polygon_offset(req: PolyOffsetReq) -> Response:
    """
    Generate G-code for polygon offsetting with multiple passes.

    Supports:
    - Robust pyclipper offsetting (or fallback miter)
    - Join types: miter, round, bevel
    - Arc linking (G2/G3) or linear linking (G1)
    - Feed management for tight curves

    Args:
        req: PolyOffsetReq with polygon, tool parameters, and G-code settings

    Returns:
        G-code file (text/plain) with offset toolpaths
    """
    # Generate offset paths
    paths = toolpath_offsets(
        req.polygon,
        req.tool_dia,
        req.stepover,
        req.inward,
        req.join_type,
        req.arc_tolerance
    )

    if not paths:
        return Response(
            content="(Error: No valid offset paths generated)\nM30\n",
            media_type="text/plain"
        )

    # Generate G-code with selected linking mode
    if req.link_mode == "arc":
        nc = emit_xy_with_arcs(
            paths,
            z=req.z,
            safe_z=req.safe_z,
            units=req.units,
            feed=req.feed,
            feed_arc=req.feed_arc,
            feed_floor=req.feed_floor,
            link_radius=req.link_radius
        )
    else:
        nc = emit_xy_polyline_nc(
            paths,
            z=req.z,
            safe_z=req.safe_z,
            units=req.units,
            feed=req.feed,
            spindle=req.spindle
        )

    return Response(content=nc, media_type="text/plain")
