"""
CAM Binding/Purfling Toolpath Router

Production binding channel and purfling ledge toolpath generation
for acoustic guitars.

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Endpoints:
    POST /channel/gcode    - Generate binding channel G-code
    POST /purfling/gcode   - Generate purfling ledge G-code
    POST /preview          - Preview offset geometry
    GET  /info             - Get operation info
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.core.safety import safety_critical

# Import production binding module
from app.cam.binding import (
    BindingChannel,
    BindingConfig,
    PurflingLedge,
    PurflingConfig,
    generate_binding_offset,
    generate_purfling_offset,
)

router = APIRouter()


class Point2D(BaseModel):
    """2D point."""
    x: float
    y: float


class BindingChannelRequest(BaseModel):
    """Request for binding channel toolpath generation."""

    # Geometry - body outline
    body_outline: List[Point2D] = Field(..., description="Body outline points")
    is_closed: bool = Field(True, description="Whether outline is closed")

    # Channel dimensions
    channel_width_mm: float = Field(
        2.0, ge=0.5, le=10.0,
        description="Binding channel width"
    )
    channel_depth_mm: float = Field(
        2.0, ge=0.5, le=10.0,
        description="Binding channel depth"
    )

    # Tool parameters
    tool_diameter_mm: float = Field(
        3.175, ge=0.5, le=12.0,
        description="Rabbeting bit diameter"
    )

    # Cut parameters
    max_stepdown_mm: float = Field(1.0, ge=0.1, le=5.0)
    max_stepover_mm: float = Field(1.0, ge=0.1, le=5.0)

    # Feed rates
    feed_rate_mm_min: float = Field(800.0, ge=100.0, le=5000.0)
    plunge_rate_mm_min: float = Field(300.0, ge=50.0, le=1500.0)

    # Heights
    safe_z_mm: float = Field(5.0, ge=1.0, le=50.0)


class PurflingLedgeRequest(BaseModel):
    """Request for purfling ledge toolpath generation."""

    # Geometry - body outline
    body_outline: List[Point2D] = Field(..., description="Body outline points")
    is_closed: bool = Field(True, description="Whether outline is closed")

    # Ledge dimensions
    ledge_width_mm: float = Field(
        1.5, ge=0.3, le=5.0,
        description="Purfling ledge width"
    )
    ledge_depth_mm: float = Field(
        0.8, ge=0.2, le=3.0,
        description="Purfling ledge depth"
    )
    offset_from_edge_mm: float = Field(
        2.0, ge=0.5, le=10.0,
        description="Offset from binding edge"
    )

    # Tool parameters
    tool_diameter_mm: float = Field(
        1.5, ge=0.5, le=6.0,
        description="Small end mill diameter"
    )

    # Feed rates
    feed_rate_mm_min: float = Field(600.0, ge=100.0, le=3000.0)
    plunge_rate_mm_min: float = Field(200.0, ge=50.0, le=1000.0)

    # Heights
    safe_z_mm: float = Field(5.0, ge=1.0, le=50.0)


class OffsetPreviewRequest(BaseModel):
    """Request for offset preview."""

    body_outline: List[Point2D]
    is_closed: bool = True
    binding_width_mm: float = 2.0
    purfling_offset_mm: float = 2.0
    purfling_width_mm: float = 1.5


@router.post("/channel/gcode", response_class=Response)
@safety_critical
def generate_binding_channel_gcode(req: BindingChannelRequest) -> Response:
    """
    Generate binding channel G-code.

    Uses production-quality BindingChannel with:
    - Multi-pass depth stepping
    - Multi-pass width stepping (for wide channels)
    - Rabbeting tool compensation
    - Smooth corner handling
    """
    if len(req.body_outline) < 3:
        raise HTTPException(
            status_code=400,
            detail="Body outline must have at least 3 points"
        )

    # Convert to tuple format
    points: List[Tuple[float, float]] = [
        (pt.x, pt.y) for pt in req.body_outline
    ]

    # Build configuration
    config = BindingConfig(
        channel_width_mm=req.channel_width_mm,
        channel_depth_mm=req.channel_depth_mm,
        tool_diameter_mm=req.tool_diameter_mm,
        max_stepdown_mm=req.max_stepdown_mm,
        max_stepover_mm=req.max_stepover_mm,
        safe_z_mm=req.safe_z_mm,
        feed_rate_mm_min=req.feed_rate_mm_min,
        plunge_rate_mm_min=req.plunge_rate_mm_min,
    )

    # Generate toolpath
    channel = BindingChannel(
        body_outline=points,
        is_closed=req.is_closed,
        config=config,
    )

    result = channel.generate()

    return Response(
        content=result.gcode,
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Depth-Passes": str(result.depth_passes),
            "X-Width-Passes": str(result.width_passes),
            "X-Total-Length-MM": f"{result.total_length_mm:.2f}",
            "X-Estimated-Time-S": f"{result.estimated_time_seconds:.1f}",
        }
    )


@router.post("/purfling/gcode", response_class=Response)
@safety_critical
def generate_purfling_ledge_gcode(req: PurflingLedgeRequest) -> Response:
    """
    Generate purfling ledge G-code.

    Creates a shallow ledge inside the binding channel for
    purfling strip inlay.
    """
    if len(req.body_outline) < 3:
        raise HTTPException(
            status_code=400,
            detail="Body outline must have at least 3 points"
        )

    # Convert to tuple format
    points: List[Tuple[float, float]] = [
        (pt.x, pt.y) for pt in req.body_outline
    ]

    # Build configuration
    config = PurflingConfig(
        ledge_width_mm=req.ledge_width_mm,
        ledge_depth_mm=req.ledge_depth_mm,
        offset_from_edge_mm=req.offset_from_edge_mm,
        tool_diameter_mm=req.tool_diameter_mm,
        safe_z_mm=req.safe_z_mm,
        feed_rate_mm_min=req.feed_rate_mm_min,
        plunge_rate_mm_min=req.plunge_rate_mm_min,
    )

    # Generate toolpath
    ledge = PurflingLedge(
        body_outline=points,
        is_closed=req.is_closed,
        config=config,
    )

    result = ledge.generate()

    return Response(
        content=result.gcode,
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Pass-Count": str(result.pass_count),
            "X-Total-Length-MM": f"{result.total_length_mm:.2f}",
            "X-Estimated-Time-S": f"{result.estimated_time_seconds:.1f}",
        }
    )


@router.post("/preview")
def preview_offsets(req: OffsetPreviewRequest) -> Dict[str, Any]:
    """
    Preview binding and purfling offset geometry.

    Returns offset paths as SVG for visualization.
    """
    if len(req.body_outline) < 3:
        raise HTTPException(
            status_code=400,
            detail="Body outline must have at least 3 points"
        )

    points: List[Tuple[float, float]] = [
        (pt.x, pt.y) for pt in req.body_outline
    ]

    # Generate offsets
    binding_path = generate_binding_offset(points, req.binding_width_mm)
    purfling_path = generate_purfling_offset(
        points,
        req.purfling_offset_mm,
        req.purfling_width_mm,
    )

    # Convert to SVG
    def path_to_svg_polyline(path: List[Tuple[float, float]], color: str) -> str:
        if not path:
            return ""
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in path)
        return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="0.5"/>'

    # Calculate bounds
    all_pts = points + binding_path + purfling_path
    if not all_pts:
        return {"ok": False, "error": "No geometry generated"}

    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    w, h = max(1, maxx - minx), max(1, maxy - miny)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx - 5} {miny - 5} {w + 10} {h + 10}">
{path_to_svg_polyline(points, "#333")}
{path_to_svg_polyline(binding_path, "blue")}
{path_to_svg_polyline(purfling_path, "green")}
</svg>'''

    return {
        "ok": True,
        "svg": svg,
        "body_points": len(points),
        "binding_points": len(binding_path),
        "purfling_points": len(purfling_path),
    }


@router.get("/info")
def binding_info() -> Dict[str, Any]:
    """Get binding/purfling operation information."""
    return {
        "operation": "binding",
        "description": "Binding channel and purfling ledge toolpaths for acoustic guitars",
        "features": [
            "Multi-pass depth stepping",
            "Multi-pass width stepping for wide channels",
            "Rabbeting tool compensation",
            "Purfling ledge with offset control",
            "Polygon offset for accurate insets",
        ],
        "resolves": ["OM-GAP-03", "OM-GAP-04", "OM-PURF-01", "OM-PURF-02", "BEN-GAP-01"],
    }
