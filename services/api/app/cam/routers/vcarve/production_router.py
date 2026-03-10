"""
CAM Production V-Carve Router

Production-quality V-carve toolpath generation with:
- Chipload-based feed rate calculation
- Multi-pass stepdown
- Corner slowdown
- V-bit geometry calculations

Architecture Layer: ROUTER (Layer 6)
See: docs/governance/ARCHITECTURE_INVARIANTS.md

Resolves: VINE-03 (V-carve G-code is demo quality)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.core.safety import safety_critical

# Import production vcarve module
from app.cam.vcarve import (
    VCarveToolpath,
    VCarveConfig,
    vbit_depth_for_width,
    vbit_width_at_depth,
    calculate_chipload,
    MATERIAL_CHIPLOAD,
)
from app.cam.vcarve.toolpath import MLPath

router = APIRouter()


class Point2D(BaseModel):
    """2D point."""
    x: float
    y: float


class PathInput(BaseModel):
    """Single path for V-carving."""
    points: List[Point2D] = Field(..., description="Path points")
    is_closed: bool = Field(False, description="Whether path is closed")


class VCarveProductionRequest(BaseModel):
    """Request for production V-carve toolpath generation."""

    # Geometry
    paths: List[PathInput] = Field(..., description="Paths to V-carve")

    # V-bit parameters
    bit_angle_deg: float = Field(
        60.0, ge=10.0, le=120.0,
        description="V-bit included angle in degrees"
    )
    tip_diameter_mm: float = Field(
        0.0, ge=0.0, le=2.0,
        description="Tip flat diameter (0 for sharp tip)"
    )

    # Target dimensions
    target_line_width_mm: float = Field(
        2.0, ge=0.1, le=20.0,
        description="Desired line width at surface"
    )
    target_depth_mm: Optional[float] = Field(
        None, ge=0.1, le=20.0,
        description="Override calculated depth (optional)"
    )

    # Material and feed calculation
    material: str = Field(
        "hardwood",
        description="Material type (softwood, hardwood, mdf, plywood, acrylic, aluminum)"
    )
    spindle_rpm: int = Field(
        18000, ge=5000, le=30000,
        description="Spindle speed in RPM"
    )
    flute_count: int = Field(2, ge=1, le=4, description="Number of flutes")
    chipload_factor: float = Field(
        0.8, ge=0.3, le=1.0,
        description="Chipload factor (0.5=conservative, 1.0=aggressive)"
    )

    # Multi-pass
    max_stepdown_mm: float = Field(2.0, ge=0.5, le=10.0)
    min_passes: int = Field(1, ge=1, le=10)

    # Heights
    safe_z_mm: float = Field(5.0, ge=1.0, le=50.0)
    retract_z_mm: float = Field(2.0, ge=0.5, le=25.0)

    # Feed rates (calculated if None)
    feed_rate_mm_min: Optional[float] = Field(
        None, ge=100.0, le=5000.0,
        description="Override calculated feed rate"
    )
    plunge_rate_mm_min: float = Field(300.0, ge=50.0, le=2000.0)

    # Options
    corner_slowdown: bool = Field(True, description="Slow down at sharp corners")
    corner_angle_threshold_deg: float = Field(90.0, ge=30.0, le=150.0)
    corner_feed_factor: float = Field(0.6, ge=0.3, le=1.0)
    optimize_path_order: bool = Field(True, description="Reorder paths to minimize rapids")


class VCarvePreviewRequest(BaseModel):
    """Request for V-carve parameter preview."""

    bit_angle_deg: float = 60.0
    target_line_width_mm: float = 2.0
    target_depth_mm: Optional[float] = None
    material: str = "hardwood"
    spindle_rpm: int = 18000
    flute_count: int = 2
    chipload_factor: float = 0.8


@router.post("/gcode", response_class=Response)
@safety_critical
def generate_production_vcarve_gcode(req: VCarveProductionRequest) -> Response:
    """
    Generate production-quality V-carve G-code.

    Uses chipload-based feed rate calculation:
        feed_rate = chipload * RPM * flute_count

    Material-specific chipload ranges ensure optimal cutting.
    Multi-pass stepdown prevents tool breakage.
    Corner slowdown improves surface finish.
    """
    if not req.paths:
        raise HTTPException(
            status_code=400,
            detail="At least one path is required"
        )

    # Convert to MLPath format
    ml_paths: List[MLPath] = []
    for path_input in req.paths:
        if len(path_input.points) < 2:
            continue
        points: List[Tuple[float, float]] = [
            (pt.x, pt.y) for pt in path_input.points
        ]
        ml_paths.append(MLPath(points=points, is_closed=path_input.is_closed))

    if not ml_paths:
        raise HTTPException(
            status_code=400,
            detail="No valid paths (each path needs at least 2 points)"
        )

    # Build configuration
    config = VCarveConfig(
        bit_angle_deg=req.bit_angle_deg,
        tip_diameter_mm=req.tip_diameter_mm,
        target_line_width_mm=req.target_line_width_mm,
        target_depth_mm=req.target_depth_mm,
        material=req.material,
        spindle_rpm=req.spindle_rpm,
        flute_count=req.flute_count,
        chipload_factor=req.chipload_factor,
        max_stepdown_mm=req.max_stepdown_mm,
        min_passes=req.min_passes,
        safe_z_mm=req.safe_z_mm,
        retract_z_mm=req.retract_z_mm,
        feed_rate_mm_min=req.feed_rate_mm_min,
        plunge_rate_mm_min=req.plunge_rate_mm_min,
        corner_slowdown=req.corner_slowdown,
        corner_angle_threshold_deg=req.corner_angle_threshold_deg,
        corner_feed_factor=req.corner_feed_factor,
        optimize_path_order=req.optimize_path_order,
    )

    # Generate toolpath
    vcarve = VCarveToolpath(paths=ml_paths, config=config)
    result = vcarve.generate()

    # Include warnings in response
    warning_header = "; ".join(result.warnings) if result.warnings else ""

    return Response(
        content=result.gcode,
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Path-Count": str(result.path_count),
            "X-Pass-Count": str(result.pass_count),
            "X-Cut-Depth-MM": f"{result.cut_depth_mm:.3f}",
            "X-Line-Width-MM": f"{result.line_width_mm:.3f}",
            "X-Feed-Rate": f"{result.feed_rate_mm_min:.0f}",
            "X-Total-Length-MM": f"{result.total_length_mm:.2f}",
            "X-Estimated-Time-S": f"{result.estimated_time_seconds:.1f}",
            "X-Warnings": warning_header[:200],  # Truncate for header safety
        }
    )


@router.post("/preview")
def preview_vcarve_params(req: VCarvePreviewRequest) -> Dict[str, Any]:
    """
    Preview V-carve calculation parameters without generating G-code.

    Returns calculated depth, feed rate, chipload, and pass count.
    """
    # Calculate depth from width
    if req.target_depth_mm is not None:
        depth = req.target_depth_mm
        width = vbit_width_at_depth(depth, req.bit_angle_deg)
    else:
        depth = vbit_depth_for_width(req.target_line_width_mm, req.bit_angle_deg)
        width = req.target_line_width_mm

    # Get material chipload range
    material_key = req.material.lower().replace(" ", "_").replace("-", "_")
    chipload_range = MATERIAL_CHIPLOAD.get(material_key, MATERIAL_CHIPLOAD["default"])

    # Calculate target chipload
    factor = max(0.0, min(1.0, req.chipload_factor))
    target_chipload = chipload_range[0] + factor * (chipload_range[1] - chipload_range[0])

    # Calculate feed rate
    feed_rate = target_chipload * req.spindle_rpm * req.flute_count

    # Calculate actual chipload
    actual_chipload = calculate_chipload(feed_rate, req.spindle_rpm, req.flute_count)

    # Calculate passes
    from app.cam.vcarve.geometry import calculate_stepdown
    pass_count, stepdown = calculate_stepdown(depth, req.bit_angle_deg, 2.0, 1)

    return {
        "ok": True,
        "calculations": {
            "depth_mm": round(depth, 3),
            "line_width_mm": round(width, 3),
            "feed_rate_mm_min": round(feed_rate, 1),
            "chipload_mm": round(actual_chipload, 4),
            "chipload_range": {
                "min": chipload_range[0],
                "max": chipload_range[1],
            },
            "pass_count": pass_count,
            "stepdown_mm": round(stepdown, 3),
        },
        "inputs": {
            "bit_angle_deg": req.bit_angle_deg,
            "target_line_width_mm": req.target_line_width_mm,
            "material": req.material,
            "spindle_rpm": req.spindle_rpm,
            "flute_count": req.flute_count,
        },
    }


@router.get("/materials")
def list_materials() -> Dict[str, Any]:
    """List supported materials with chipload ranges."""
    return {
        "materials": {
            name: {
                "chipload_min_mm": range_[0],
                "chipload_max_mm": range_[1],
            }
            for name, range_ in MATERIAL_CHIPLOAD.items()
        }
    }


@router.get("/info")
def vcarve_production_info() -> Dict[str, Any]:
    """Get production V-carve operation information."""
    return {
        "operation": "vcarve_production",
        "description": "Production-quality V-carve with chipload calculations",
        "features": [
            "Chipload-based feed rate calculation",
            "Material-specific cutting parameters",
            "Automatic depth calculation from line width",
            "Multi-pass stepdown for deep cuts",
            "Corner slowdown for surface quality",
            "Path order optimization (nearest-neighbor)",
        ],
        "supported_materials": list(MATERIAL_CHIPLOAD.keys()),
        "resolves": ["VINE-03"],
    }
