"""
G-code Animate Simulator Router

Provides per-segment move data for frontend toolpath animation.
Each segment carries type, coordinates, feed, and duration so the
Vue player can replay G-code execution visually at any speed.

Endpoint:
    POST /api/cam/gcode/simulate

Shares the /cam/gcode prefix with gcode_backplot_router.py.
Registered via router_registry/manifest.py (category: cam).

Architecture:
    UTILITY lane — stateless, no governance, no audit trail required.
    Router → util/gcode_parser.simulate_segments() only.
    No cross-domain imports.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..util.gcode_parser import simulate_segments

router = APIRouter(prefix="/cam/gcode", tags=["cam", "gcode", "simulate"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

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

    type: str = Field(
        ...,
        description="'rapid' | 'cut' | 'arc_cw' | 'arc_ccw'",
    )
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


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

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
