"""
CAM Profile Toolpath Router

Production perimeter profiling with holding tabs, lead-in/out arcs,
and multi-pass stepdown.

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /gcode     - Generate profiling G-code
    POST /preview   - Preview tab positions
    GET  /info      - Get operation info
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.core.safety import safety_critical

# Import production profiling module
from app.cam.profiling import (
    ProfileToolpath,
    ProfileConfig,
    TabGenerator,
)

router = APIRouter()


class Point2D(BaseModel):
    """2D point."""
    x: float
    y: float


class ProfileRequest(BaseModel):
    """Request for profile toolpath generation."""

    # Geometry
    contour: List[Point2D] = Field(..., description="Profile contour points")
    is_closed: bool = Field(True, description="Whether contour is closed")
    is_outside: bool = Field(True, description="Outside (True) or inside (False) cut")

    # Tool parameters
    tool_diameter_mm: float = Field(6.35, ge=0.5, le=50.0, description="Tool diameter")

    # Cut parameters
    cut_depth_mm: float = Field(6.0, ge=0.1, le=100.0, description="Total cut depth")
    max_stepdown_mm: float = Field(2.0, ge=0.1, le=20.0, description="Max depth per pass")

    # Tab parameters
    use_tabs: bool = Field(True, description="Add holding tabs")
    tab_count: int = Field(4, ge=0, le=20, description="Number of tabs")
    tab_width_mm: float = Field(6.0, ge=1.0, le=30.0, description="Tab width")
    tab_height_mm: float = Field(1.5, ge=0.5, le=10.0, description="Tab height")

    # Feed rates
    feed_rate_mm_min: float = Field(1200.0, ge=100.0, le=10000.0)
    plunge_rate_mm_min: float = Field(400.0, ge=50.0, le=2000.0)

    # Heights
    safe_z_mm: float = Field(5.0, ge=1.0, le=50.0)
    retract_z_mm: float = Field(2.0, ge=0.5, le=25.0)

    # Options
    climb_milling: bool = Field(True, description="Use climb milling")
    lead_in_radius_mm: Optional[float] = Field(None, description="Lead-in arc radius")


class TabPreviewRequest(BaseModel):
    """Request for tab position preview."""

    contour: List[Point2D]
    is_closed: bool = True
    tab_count: int = 4
    min_corner_distance_mm: float = 10.0


class TabInfo(BaseModel):
    """Tab position info."""

    index: int
    position: Point2D
    width_mm: float


@router.post("/gcode", response_class=Response)
@safety_critical
def generate_profile_gcode(req: ProfileRequest) -> Response:
    """
    Generate perimeter profiling G-code with holding tabs.

    Uses production-quality ProfileToolpath with:
    - Multi-pass stepdown for deep cuts
    - Holding tabs to prevent part movement
    - Lead-in/out arcs (optional)
    - Climb/conventional milling selection
    - Cutter compensation awareness
    """
    if len(req.contour) < 3:
        raise HTTPException(
            status_code=400,
            detail="Contour must have at least 3 points"
        )

    # Convert to tuple format expected by module
    points: List[Tuple[float, float]] = [
        (pt.x, pt.y) for pt in req.contour
    ]

    # Build configuration
    config = ProfileConfig(
        tool_diameter_mm=req.tool_diameter_mm,
        cut_depth_mm=req.cut_depth_mm,
        max_stepdown_mm=req.max_stepdown_mm,
        use_tabs=req.use_tabs,
        tab_count=req.tab_count,
        tab_width_mm=req.tab_width_mm,
        tab_height_mm=req.tab_height_mm,
        safe_z_mm=req.safe_z_mm,
        retract_z_mm=req.retract_z_mm,
        feed_rate_mm_min=req.feed_rate_mm_min,
        plunge_rate_mm_min=req.plunge_rate_mm_min,
        climb_milling=req.climb_milling,
        lead_in_radius_mm=req.lead_in_radius_mm,
        is_outside_cut=req.is_outside,
    )

    # Generate toolpath
    profiler = ProfileToolpath(
        contour=points,
        is_closed=req.is_closed,
        config=config,
    )

    result = profiler.generate()

    return Response(
        content=result.gcode,
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Pass-Count": str(result.pass_count),
            "X-Tab-Count": str(result.tab_count),
            "X-Total-Length-MM": f"{result.total_length_mm:.2f}",
            "X-Estimated-Time-S": f"{result.estimated_time_seconds:.1f}",
        }
    )


@router.post("/preview")
def preview_tabs(req: TabPreviewRequest) -> Dict[str, Any]:
    """
    Preview tab positions on a profile contour.

    Returns tab positions without generating G-code.
    """
    if len(req.contour) < 3:
        raise HTTPException(
            status_code=400,
            detail="Contour must have at least 3 points"
        )

    points: List[Tuple[float, float]] = [
        (pt.x, pt.y) for pt in req.contour
    ]

    generator = TabGenerator(
        contour=points,
        is_closed=req.is_closed,
        tab_count=req.tab_count,
        min_corner_distance_mm=req.min_corner_distance_mm,
    )

    tabs = generator.generate()

    return {
        "ok": True,
        "tab_count": len(tabs),
        "tabs": [
            {
                "index": i,
                "position": {"x": tab.position[0], "y": tab.position[1]},
                "width_mm": tab.width,
            }
            for i, tab in enumerate(tabs)
        ],
        "contour_length_mm": generator.contour_length,
    }


@router.get("/info")
def profile_info() -> Dict[str, Any]:
    """Get profiling operation information."""
    return {
        "operation": "profiling",
        "description": "Perimeter profiling with holding tabs",
        "features": [
            "Multi-pass stepdown for deep cuts",
            "Automatic holding tab placement",
            "Tab corner avoidance",
            "Lead-in/out arcs (optional)",
            "Climb/conventional milling selection",
            "Cutter radius compensation awareness",
        ],
        "resolves": ["OM-GAP-02", "BEN-GAP-03", "VINE-07", "FV-GAP-03"],
    }
