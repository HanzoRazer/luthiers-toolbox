"""
G-code Visualization Router (Consolidated)
==========================================

G-code visualization, simulation, and estimation endpoints.

Consolidated from:
    - gcode_backplot_router.py (2 routes)
    - gcode_simulate_router.py (1 route)

Endpoints (under /api/cam/gcode):
    POST /plot.svg   - Generate SVG backplot from G-code
    POST /estimate   - Calculate distances and cycle time
    POST /simulate   - Per-segment animation data

Architecture:
    UTILITY lane — stateless, no governance, no audit trail.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from ..util.gcode_parser import simulate, simulate_segments, svg_from_points


router = APIRouter(prefix="/cam/gcode", tags=["cam", "gcode"])


# ===========================================================================
# SHARED MODELS
# ===========================================================================

class PlotReq(BaseModel):
    """Request model for G-code backplot and estimation."""
    gcode: str
    units: str = "mm"
    rapid_mm_min: float = 3000.0
    default_feed_mm_min: float = 500.0
    stroke: str = "black"


# ===========================================================================
# BACKPLOT ENDPOINTS
# ===========================================================================

@router.post("/plot.svg", response_class=Response)
def plot(req: PlotReq) -> Response:
    """
    Generate SVG backplot from G-code.

    Parses G-code and creates a 2D XY visualization of the toolpath.

    Args:
        req: PlotReq with gcode, units, feed rates, and stroke color

    Returns:
        SVG image as application/svg+xml
    """
    sim = simulate(
        req.gcode,
        rapid_mm_min=req.rapid_mm_min,
        default_feed_mm_min=req.default_feed_mm_min,
        units=req.units
    )
    svg = svg_from_points(sim["points_xy"], stroke=req.stroke)
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/estimate")
def estimate(req: PlotReq) -> Dict[str, Any]:
    """
    Estimate G-code cycle time and distances.

    Calculates:
    - Travel distance (rapid moves)
    - Cutting distance (feed moves)
    - Time breakdown (rapid vs feed)
    - Total cycle time
    """
    sim = simulate(
        req.gcode,
        rapid_mm_min=req.rapid_mm_min,
        default_feed_mm_min=req.default_feed_mm_min,
        units=req.units
    )
    return sim


# ===========================================================================
# SIMULATION MODELS
# ===========================================================================

class SimulateRequest(BaseModel):
    """Request body for the toolpath simulation endpoint."""
    gcode: str = Field(..., description="Raw G-code program text")
    units: str = Field("mm", description="Input units: 'mm' or 'inch'")
    rapid_mm_min: float = Field(3000.0, description="Machine rapid traverse rate (mm/min)")
    default_feed_mm_min: float = Field(500.0, description="Default feed if F not yet set")
    arc_resolution_deg: float = Field(
        5.0,
        description="Angular step for arc interpolation (degrees). "
                    "Smaller = smoother arcs, more segments.",
    )


class MoveSegment(BaseModel):
    """One atomic motion segment — linear or arc sub-segment."""
    type: str = Field(..., description="'rapid' | 'cut' | 'arc_cw' | 'arc_ccw'")
    from_pos: list = Field(..., description="[x, y, z] start position in mm")
    to_pos: list = Field(..., description="[x, y, z] end position in mm")
    feed: float = Field(..., description="Feed rate for this move (mm/min)")
    duration_ms: float = Field(..., description="Real-time duration of this move (ms)")
    line_number: int = Field(..., description="1-based source G-code line index")
    line_text: str = Field(..., description="Raw G-code text for HUD display")


class SimulateBounds(BaseModel):
    """XYZ bounding box of the entire toolpath."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float


class SimulateTotals(BaseModel):
    """Aggregate statistics matching simulate() for cross-validation."""
    rapid_mm: float
    cut_mm: float
    time_min: float
    segment_count: int


class SimulateResponse(BaseModel):
    """Full simulation response — segments + metadata."""
    segments: list[MoveSegment]
    bounds: SimulateBounds
    totals: SimulateTotals


# ===========================================================================
# SIMULATION ENDPOINT
# ===========================================================================

@router.post("/simulate", response_model=SimulateResponse)
def simulate_gcode(req: SimulateRequest) -> SimulateResponse:
    """
    Simulate G-code and return per-segment move data for animation.

    The response contains one segment per atomic G-code motion command.
    G2/G3 arcs are pre-interpolated at arc_resolution_deg steps so the
    frontend renderer only needs lineTo() calls — no arc math in the UI.
    """
    result = simulate_segments(
        req.gcode,
        rapid_mm_min=req.rapid_mm_min,
        default_feed_mm_min=req.default_feed_mm_min,
        units=req.units,
        arc_resolution_deg=req.arc_resolution_deg,
    )

    return SimulateResponse(
        segments=[MoveSegment(**s) for s in result["segments"]],
        bounds=SimulateBounds(**result["bounds"]),
        totals=SimulateTotals(**result["totals"]),
    )


__all__ = ["router"]
