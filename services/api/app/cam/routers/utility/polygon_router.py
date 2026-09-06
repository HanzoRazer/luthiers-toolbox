"""Polygon Router — Polygon offset G-code generation (N17 utility lane).

Provides:
- POST /polygon_offset_n17.nc - Generate G-code for polygon offsetting

STEPOVER IS ABSOLUTE MILLIMETRES HERE (default 2.0), which is why this handler
must not share a URL with the governed engine, whose `stepover` is a FRACTION
of tool_dia (Field(gt=0, le=1.0), step = tool_dia * stepover).

This route was previously mounted at `/polygon_offset.nc`, colliding with
app.routers.polygon_offset_router.polygon_offset_nc. The utility router is
registered first, so it won FastAPI first-match and silently served every
caller of that URL. Both live consumers -- OffsetLabView.vue and
api/n17_n18.ts -- send the governed fraction convention (n17_n18.ts documents
it as "Fraction (0-1), e.g. 0.4 = 40%") and both preview against the
governed-only /polygon_offset.preview. The result was a UI that previewed one
toolpath and downloaded another: stepover 0.4 became 0.4 mm passes instead of
0.4 x 6.0 = 2.4 mm.

Renamed rather than deleted: the implementation is real and stays reachable at
its own explicit path.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from fastapi import APIRouter, Response
from pydantic import BaseModel

from ...polygon_offset_n17 import toolpath_offsets
from ....util.gcode_emit_advanced import emit_xy_with_arcs
from ....util.gcode_emit_basic import emit_xy_polyline_nc

router = APIRouter()  # No prefix

Pt = Tuple[float, float]


class PolyOffsetReq(BaseModel):
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


@router.post("/polygon_offset_n17.nc", response_class=Response)
def polygon_offset(req: PolyOffsetReq) -> Response:
    """Generate G-code for polygon offsetting with multiple passes."""
    paths = toolpath_offsets(
        req.polygon, req.tool_dia, req.stepover, req.inward, req.join_type, req.arc_tolerance
    )
    if not paths:
        return Response(
            content="(Error: No valid offset paths generated)\nM30\n", media_type="text/plain"
        )

    if req.link_mode == "arc":
        nc = emit_xy_with_arcs(
            paths,
            z=req.z,
            safe_z=req.safe_z,
            units=req.units,
            feed=req.feed,
            feed_arc=req.feed_arc,
            feed_floor=req.feed_floor,
            link_radius=req.link_radius,
        )
    else:
        nc = emit_xy_polyline_nc(
            paths, z=req.z, safe_z=req.safe_z, units=req.units, feed=req.feed, spindle=req.spindle
        )
    return Response(content=nc, media_type="text/plain")


__all__ = ["router", "PolyOffsetReq"]
