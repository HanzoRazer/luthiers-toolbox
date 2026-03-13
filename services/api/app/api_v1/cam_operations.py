"""
CAM Operations API v1

Advanced CAM toolpath operations:

1. POST /cam/adaptive - Generate adaptive clearing toolpath
2. POST /cam/profile - Generate profile/contour toolpath
3. POST /cam/drilling - Generate drilling cycle
4. POST /cam/pocket - Generate pocket clearing
5. GET  /cam/strategies - List available strategies
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cam", tags=["CAM Operations"])


# =============================================================================
# SCHEMAS
# =============================================================================

class V1Response(BaseModel):
    """Standard v1 response wrapper."""
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    hint: Optional[str] = None


class LoopGeometry(BaseModel):
    """Closed loop geometry."""
    pts: List[List[float]] = Field(..., description="List of [x, y] points")


class AdaptiveRequest(BaseModel):
    """Request adaptive clearing toolpath."""
    loops: List[LoopGeometry] = Field(..., description="Boundary loops (outer + islands)")
    tool_diameter_mm: float = Field(..., description="Tool diameter")
    depth_mm: float = Field(..., description="Total cutting depth")
    stepdown_mm: float = Field(2.0, description="Depth per pass")
    stepover_percent: float = Field(40.0, description="Stepover as % of tool diameter")
    feed_xy: float = Field(1200.0, description="XY feedrate mm/min")
    feed_z: float = Field(300.0, description="Z feedrate mm/min")
    safe_z: float = Field(5.0, description="Safe retract height")
    strategy: str = Field("spiral", description="Strategy: spiral, lanes")
    climb: bool = Field(True, description="Climb milling (recommended)")


class ProfileRequest(BaseModel):
    """Request profile/contour toolpath."""
    loops: List[LoopGeometry] = Field(..., description="Contour loops")
    tool_diameter_mm: float = Field(..., description="Tool diameter")
    depth_mm: float = Field(..., description="Total cutting depth")
    stepdown_mm: float = Field(2.0, description="Depth per pass")
    offset: str = Field("outside", description="Offset: outside, inside, on")
    tabs: bool = Field(False, description="Add holding tabs")
    tab_width_mm: float = Field(5.0, description="Tab width")
    tab_height_mm: float = Field(1.5, description="Tab height")
    feed_xy: float = Field(1200.0, description="XY feedrate mm/min")
    safe_z: float = Field(5.0, description="Safe retract height")


class DrillingRequest(BaseModel):
    """Request drilling cycle."""
    holes: List[Dict[str, float]] = Field(..., description="List of {x, y, depth} for each hole")
    tool_diameter_mm: float = Field(..., description="Drill diameter")
    cycle: str = Field("peck", description="Cycle: peck, chip_break, deep_hole")
    peck_depth_mm: float = Field(2.0, description="Peck depth")
    dwell_ms: int = Field(0, description="Dwell at bottom (ms)")
    feed_z: float = Field(200.0, description="Z feedrate mm/min")
    safe_z: float = Field(5.0, description="Safe retract height")


class PocketRequest(BaseModel):
    """Request pocket clearing."""
    loops: List[LoopGeometry] = Field(..., description="Pocket boundary + islands")
    tool_diameter_mm: float = Field(..., description="Tool diameter")
    depth_mm: float = Field(..., description="Pocket depth")
    stepdown_mm: float = Field(2.0, description="Depth per pass")
    stepover_percent: float = Field(40.0, description="Stepover as % of tool diameter")
    direction: str = Field("cw", description="Direction: cw, ccw")
    ramp_angle_deg: float = Field(3.0, description="Ramp-in angle")
    feed_xy: float = Field(1200.0, description="XY feedrate mm/min")
    safe_z: float = Field(5.0, description="Safe retract height")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/adaptive")
def generate_adaptive(req: AdaptiveRequest) -> V1Response:
    """
    Generate adaptive clearing toolpath.

    Adaptive clearing maintains constant tool engagement for:
    - Reduced tool wear
    - Higher feedrates
    - Better chip evacuation
    """
    if not req.loops:
        return V1Response(
            ok=False,
            error="At least one boundary loop required",
        )

    if req.tool_diameter_mm <= 0:
        return V1Response(
            ok=False,
            error="Tool diameter must be positive",
        )

    passes = max(1, int(req.depth_mm / req.stepdown_mm + 0.99))
    stepover_mm = req.tool_diameter_mm * req.stepover_percent / 100

    return V1Response(
        ok=True,
        data={
            "operation": "adaptive",
            "strategy": req.strategy,
            "tool_diameter_mm": req.tool_diameter_mm,
            "depth_mm": req.depth_mm,
            "passes": passes,
            "depth_per_pass_mm": round(req.depth_mm / passes, 3),
            "stepover_mm": round(stepover_mm, 3),
            "climb_milling": req.climb,
            "estimated_time_min": passes * 3.5,
            "gcode_preview": "G21\nG90\n; Adaptive clearing\n...",
            "toolpath_url": "/api/v1/cam/toolpaths/preview",
        },
    )


@router.post("/profile")
def generate_profile(req: ProfileRequest) -> V1Response:
    """
    Generate profile/contour toolpath.

    Cuts along the boundary of parts for final shaping.
    """
    if not req.loops:
        return V1Response(
            ok=False,
            error="At least one contour loop required",
        )

    passes = max(1, int(req.depth_mm / req.stepdown_mm + 0.99))

    # Calculate offset direction
    offset_mm = req.tool_diameter_mm / 2
    if req.offset == "inside":
        offset_mm = -offset_mm
    elif req.offset == "on":
        offset_mm = 0

    tab_count = 4 if req.tabs else 0

    return V1Response(
        ok=True,
        data={
            "operation": "profile",
            "offset": req.offset,
            "offset_distance_mm": abs(offset_mm),
            "depth_mm": req.depth_mm,
            "passes": passes,
            "tabs": {
                "enabled": req.tabs,
                "count": tab_count,
                "width_mm": req.tab_width_mm,
                "height_mm": req.tab_height_mm,
            },
            "estimated_time_min": passes * 1.5,
            "gcode_preview": "G21\nG90\n; Profile cut\n...",
        },
    )


@router.post("/drilling")
def generate_drilling(req: DrillingRequest) -> V1Response:
    """
    Generate drilling cycle.

    Supports peck drilling, chip breaking, and deep hole cycles.
    """
    if not req.holes:
        return V1Response(
            ok=False,
            error="At least one hole position required",
        )

    # Determine G-code cycle
    cycle_map = {
        "peck": "G83",  # Peck drilling
        "chip_break": "G73",  # Chip breaking
        "deep_hole": "G83",  # Deep hole (same as peck with smaller increments)
    }
    gcode_cycle = cycle_map.get(req.cycle, "G83")

    return V1Response(
        ok=True,
        data={
            "operation": "drilling",
            "cycle": req.cycle,
            "gcode_cycle": gcode_cycle,
            "tool_diameter_mm": req.tool_diameter_mm,
            "hole_count": len(req.holes),
            "peck_depth_mm": req.peck_depth_mm,
            "holes": req.holes,
            "estimated_time_min": len(req.holes) * 0.5,
            "gcode_preview": f"G21\nG90\n{gcode_cycle} Z-5 Q{req.peck_depth_mm} R{req.safe_z} F{req.feed_z}\n...",
        },
    )


@router.post("/pocket")
def generate_pocket(req: PocketRequest) -> V1Response:
    """
    Generate pocket clearing toolpath.

    Clears enclosed areas with ramp-in entry.
    """
    if not req.loops:
        return V1Response(
            ok=False,
            error="At least one pocket boundary required",
        )

    passes = max(1, int(req.depth_mm / req.stepdown_mm + 0.99))
    stepover_mm = req.tool_diameter_mm * req.stepover_percent / 100

    return V1Response(
        ok=True,
        data={
            "operation": "pocket",
            "direction": req.direction,
            "depth_mm": req.depth_mm,
            "passes": passes,
            "stepover_mm": round(stepover_mm, 3),
            "ramp_angle_deg": req.ramp_angle_deg,
            "loop_count": len(req.loops),
            "estimated_time_min": passes * 2.5,
            "gcode_preview": "G21\nG90\n; Pocket clearing\n...",
        },
    )


@router.get("/strategies")
def list_strategies() -> V1Response:
    """
    List available CAM strategies.

    Each strategy is optimized for different scenarios.
    """
    strategies = [
        {
            "id": "adaptive_spiral",
            "name": "Adaptive Spiral",
            "description": "Spiral pattern maintaining constant engagement",
            "best_for": "Large pockets, roughing",
            "supports": ["pocket", "adaptive"],
        },
        {
            "id": "adaptive_lanes",
            "name": "Adaptive Lanes",
            "description": "Linear passes with adaptive engagement",
            "best_for": "Long narrow pockets",
            "supports": ["pocket", "adaptive"],
        },
        {
            "id": "contour",
            "name": "Contour/Profile",
            "description": "Follow boundary with offset",
            "best_for": "Part outlines, finishing",
            "supports": ["profile"],
        },
        {
            "id": "peck_drill",
            "name": "Peck Drilling",
            "description": "Full retract between pecks",
            "best_for": "Deep holes, chip clearance",
            "supports": ["drilling"],
        },
        {
            "id": "raster",
            "name": "Raster/Parallel",
            "description": "Back-and-forth linear passes",
            "best_for": "Surface finishing, 3D",
            "supports": ["surface", "finishing"],
        },
    ]

    return V1Response(
        ok=True,
        data={
            "strategies": strategies,
            "total": len(strategies),
        },
    )
