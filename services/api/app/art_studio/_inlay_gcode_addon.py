# --------------------------------------------------------------------- #
# G-code Export for Inlay Pockets (VINE-01)
# --------------------------------------------------------------------- #

from math import cos, sin, pi
from typing import List, Tuple
from pydantic import BaseModel, Field
from fastapi import HTTPException
from fastapi.responses import Response

from ..core.safety import safety_critical
from ..cam.adaptive_core_l1 import (
    plan_adaptive_l1,
    to_toolpath,
    spiralize_linked,
)
from ..calculators.inlay_calc import (
    InlayPatternType,
    InlayCalcInput,
    InlayShape,
    calculate_fretboard_inlays,
)


class InlayGcodeRequest(BaseModel):
    """Request model for inlay pocket G-code export."""

    # Inlay pattern parameters (same as DXF export)
    pattern_type: InlayPatternType = Field(default=InlayPatternType.DOT)
    fret_positions: List[int] = Field(
        default_factory=lambda: [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]
    )
    double_at_12: bool = Field(default=True)
    marker_diameter_mm: float = Field(default=6.0, ge=2.0, le=20.0)
    block_width_mm: float = Field(default=40.0)
    block_height_mm: float = Field(default=8.0)
    scale_length_mm: float = Field(default=648.0)
    pocket_depth_mm: float = Field(default=1.5, ge=0.5, le=5.0)
    include_side_dots: bool = Field(default=False)

    # Tool parameters
    tool_diameter_mm: float = Field(
        default=3.175,
        ge=0.5,
        le=12.0,
        description="End mill diameter (1/8 inch = 3.175mm typical)"
    )
    stepover: float = Field(
        default=0.4,
        ge=0.3,
        le=0.7,
        description="Stepover as fraction of tool diameter"
    )
    stepdown_mm: float = Field(
        default=0.5,
        ge=0.1,
        le=3.0,
        description="Depth per pass"
    )

    # Machining parameters
    feed_rate_mm_min: float = Field(
        default=800.0,
        ge=100.0,
        le=3000.0,
        description="XY feed rate"
    )
    plunge_rate_mm_min: float = Field(
        default=200.0,
        ge=50.0,
        le=1000.0,
        description="Z plunge rate"
    )
    safe_z_mm: float = Field(default=5.0, ge=1.0, le=25.0)
    retract_z_mm: float = Field(default=2.0, ge=0.5, le=10.0)
    spindle_rpm: int = Field(default=18000, ge=5000, le=30000)

    # Output options
    units: str = Field(default="mm", description="Output units (mm or inch)")


def _circle_to_polygon(cx: float, cy: float, radius: float, segments: int = 32) -> List[Tuple[float, float]]:
    """Convert circle to polygon for adaptive pocketing."""
    points = []
    for i in range(segments):
        angle = 2 * pi * i / segments
        x = cx + radius * cos(angle)
        y = cy + radius * sin(angle)
        points.append((x, y))
    points.append(points[0])  # Close the polygon
    return points


def _shape_to_loop(shape: InlayShape) -> List[Tuple[float, float]]:
    """Convert InlayShape to closed polygon loop for adaptive pocketing."""
    if shape.pattern_type == InlayPatternType.DOT:
        # Circle - convert to polygon
        return _circle_to_polygon(shape.x_mm, shape.y_mm, shape.width_mm / 2.0)
    elif shape.vertices:
        # Custom or polygon shape - use vertices offset by shape position
        points = [(shape.x_mm + vx, shape.y_mm + vy) for vx, vy in shape.vertices]
        if points and points[0] != points[-1]:
            points.append(points[0])  # Close the polygon
        return points
    else:
        # Fallback: treat as circle
        return _circle_to_polygon(shape.x_mm, shape.y_mm, shape.width_mm / 2.0)


def generate_inlay_gcode(req: InlayGcodeRequest, logger) -> Response:
    """
    Generate pocket milling G-code for inlay cavities.

    This function bridges inlay design to CNC machining by:
    1. Calculating inlay shape positions
    2. Converting each shape to a pocket boundary
    3. Generating adaptive clearing toolpaths
    4. Emitting G-code with proper headers/footers

    Resolves: VINE-01 (Inlay DXF -> pocket milling G-code bridge)
    """
    # Calculate inlay shapes
    calc_input = InlayCalcInput(
        pattern_type=req.pattern_type,
        fret_positions=req.fret_positions,
        double_at_12=req.double_at_12,
        marker_diameter_mm=req.marker_diameter_mm,
        block_width_mm=req.block_width_mm,
        block_height_mm=req.block_height_mm,
        scale_length_mm=req.scale_length_mm,
        pocket_depth_mm=req.pocket_depth_mm,
        include_side_dots=req.include_side_dots,
    )
    result = calculate_fretboard_inlays(calc_input)

    if not result.shapes:
        raise HTTPException(400, "No inlay shapes generated")

    # Build G-code
    lines = []

    # Header
    units_cmd = "G20" if req.units.lower().startswith("in") else "G21"
    lines.extend([
        f"; Inlay pocket G-code",
        f"; Pattern: {req.pattern_type.value}",
        f"; Shapes: {len(result.shapes)}",
        f"; Pocket depth: {req.pocket_depth_mm}mm",
        f"; Tool: {req.tool_diameter_mm}mm end mill",
        f";",
        units_cmd,
        "G90",  # Absolute positioning
        "G17",  # XY plane
        f"S{req.spindle_rpm} M3",  # Spindle on
        f"G0 Z{req.safe_z_mm:.3f}",  # Retract to safe Z
    ])

    # Calculate depth passes
    total_depth = abs(req.pocket_depth_mm)
    current_depth = 0.0
    pass_depths = []
    while current_depth < total_depth:
        current_depth = min(current_depth + req.stepdown_mm, total_depth)
        pass_depths.append(-current_depth)  # Negative Z

    # Generate toolpath for each shape
    for shape_idx, shape in enumerate(result.shapes):
        lines.append(f"; Shape {shape_idx + 1}: {shape.pattern_type.value} at ({shape.x_mm:.2f}, {shape.y_mm:.2f})")

        # Convert shape to polygon loop
        loop = _shape_to_loop(shape)
        if len(loop) < 3:
            lines.append(f"; WARNING: Shape too small, skipped")
            continue

        # Generate toolpath for each depth pass
        for pass_idx, z_depth in enumerate(pass_depths):
            try:
                # Use adaptive pocketing to generate XY path
                path_pts = plan_adaptive_l1(
                    loops=[loop],
                    tool_d=req.tool_diameter_mm,
                    stepover=req.stepover,
                    stepdown=req.stepdown_mm,
                    margin=0.0,
                    strategy="Spiral",
                    smoothing_radius=0.1,
                )

                if not path_pts:
                    lines.append(f"; WARNING: No toolpath for pass {pass_idx + 1}")
                    continue

                # Generate G-code moves
                moves = to_toolpath(
                    path_pts=path_pts,
                    feed_xy=req.feed_rate_mm_min,
                    z_rough=z_depth,
                    safe_z=req.safe_z_mm,
                )

                # Emit G-code lines
                for move in moves:
                    code = move.get("code", "G1")
                    parts = [code]
                    if "x" in move:
                        parts.append(f"X{move['x']:.4f}")
                    if "y" in move:
                        parts.append(f"Y{move['y']:.4f}")
                    if "z" in move:
                        parts.append(f"Z{move['z']:.4f}")
                    if "f" in move and code == "G1":
                        parts.append(f"F{move['f']:.0f}")
                    lines.append(" ".join(parts))

            except ValueError as e:
                lines.append(f"; WARNING: Toolpath generation failed: {e}")

    # Footer
    lines.extend([
        f"G0 Z{req.safe_z_mm:.3f}",  # Final retract
        "M5",  # Spindle off
        "M30",  # Program end
    ])

    gcode_content = "\n".join(lines)
    filename = f"inlay_{req.pattern_type.value}_{len(result.shapes)}shapes.nc"

    return Response(
        content=gcode_content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
