"""
CP-S57 — Saw G-Code Generator

Generates machine-ready G-code for saw-based CNC operations.
Supports slice, batch, and contour operations with multi-pass depth control.

Key Features:
- Multi-pass depth planning (DOC control)
- Safe entry/exit moves (rapid → plunge → cut → retract)
- Feed rate conversion (IPM → mm/min)
- Standard G-code headers/footers
- Path length estimation

Usage:
```python
from cam_core.gcode.saw_gcode_generator import generate_saw_gcode
from cam_core.gcode.gcode_models import SawGCodeRequest, SawToolpath

request = SawGCodeRequest(
    op_type="slice",
    toolpaths=[SawToolpath(points=[(0, 0), (100, 0)])],
    total_depth_mm=3.0,
    doc_per_pass_mm=1.0,
    feed_ipm=60,
    plunge_ipm=20
)

result = generate_saw_gcode(request)
print(result.gcode)
```
"""

from __future__ import annotations
import math
from typing import List

from .gcode_models import (
    SawGCodeRequest,
    SawGCodeResult,
    DepthPass,
    SawToolpath,
    Point2D
)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ipm_to_mm_per_min(feed_ipm: float) -> float:
    """
    Convert inches per minute to millimeters per minute.
    
    Args:
        feed_ipm: Feed rate in inches per minute
    
    Returns:
        Feed rate in mm/min
    """
    return feed_ipm * 25.4


def format_point(x: float, y: float, decimals: int = 3) -> str:
    """
    Format XY coordinates for G-code.
    
    Args:
        x: X coordinate (mm)
        y: Y coordinate (mm)
        decimals: Decimal places for formatting
    
    Returns:
        Formatted string "X{x} Y{y}"
    """
    return f"X{x:.{decimals}f} Y{y:.{decimals}f}"


def estimate_path_length_mm(toolpaths: List[SawToolpath]) -> float:
    """
    Calculate total cutting path length across all toolpaths.
    
    Sums linear distance between consecutive points.
    For closed paths, includes return distance to start.
    
    Args:
        toolpaths: List of cutting paths
    
    Returns:
        Total length in mm
    """
    total = 0.0
    for tp in toolpaths:
        pts = tp.points
        if len(pts) < 2:
            continue
        
        # Sum segment lengths
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            total += math.hypot(x1 - x0, y1 - y0)
        
        # Add closing segment if path is closed
        if tp.is_closed and len(pts) > 2:
            x0, y0 = pts[-1]
            x1, y1 = pts[0]
            total += math.hypot(x1 - x0, y1 - y0)
    
    return total


# ============================================================================
# DEPTH PLANNING
# ============================================================================

def plan_depth_passes(total_depth_mm: float, doc_per_pass_mm: float) -> List[DepthPass]:
    """
    Plan multi-pass depth levels for incremental cutting.
    
    Divides total depth into equal passes, clamped to max DOC per pass.
    Returns depths as negative Z values (below surface at Z=0).
    
    Args:
        total_depth_mm: Total cutting depth (positive value)
        doc_per_pass_mm: Maximum depth of cut per pass
    
    Returns:
        List of DepthPass objects with negative Z depths
    
    Example:
        >>> plan_depth_passes(3.0, 1.0)
        [DepthPass(depth_mm=-1.0), DepthPass(depth_mm=-2.0), DepthPass(depth_mm=-3.0)]
    """
    total_depth_mm = abs(total_depth_mm)
    doc_per_pass_mm = max(doc_per_pass_mm, 0.001)  # Prevent division by zero

    n_passes = max(1, math.ceil(total_depth_mm / doc_per_pass_mm))

    depths = []
    for i in range(1, n_passes + 1):
        d = min(i * doc_per_pass_mm, total_depth_mm)
        depths.append(DepthPass(depth_mm=-d))  # Negative = below surface
    
    return depths


# ============================================================================
# G-CODE GENERATION
# ============================================================================

def emit_header(req: SawGCodeRequest) -> str:
    """
    Generate G-code program header.
    
    Includes:
    - Program ID and comment
    - Units (G21 mm / G20 inch)
    - Absolute positioning (G90)
    - XY plane selection (G17)
    - Cancel modal states (G40/G49/G80)
    
    Args:
        req: G-code request with program metadata
    
    Returns:
        Multi-line header string
    """
    lines = []
    lines.append(f"( {req.program_comment} )")
    lines.append(f"O{req.program_id}")
    
    if req.machine_units == "mm":
        lines.append("G21  (units: mm)")
    else:
        lines.append("G20  (units: inches)")
    
    lines.append("G90  (absolute mode)")
    lines.append("G17  (XY plane)")
    lines.append("G40  (cutter comp off)")
    lines.append("G49  (cancel tool length)")
    lines.append("G80  (cancel canned cycles)")
    lines.append("")
    
    return "\n".join(lines) + "\n"


def emit_footer() -> str:
    """
    Generate G-code program footer.
    
    Returns:
        Multi-line footer string with M30 program end
    """
    lines = []
    lines.append("")
    lines.append("M30  (end of program)")
    return "\n".join(lines) + "\n"


def emit_toolpath_at_depth(
    tp: SawToolpath,
    depth_mm: float,
    req: SawGCodeRequest,
    feed_mm_min: float,
    plunge_mm_min: float,
) -> List[str]:
    """
    Generate G-code for single toolpath at specific depth.
    
    Sequence:
    1. Rapid to first XY at safe Z
    2. Plunge to cutting depth
    3. Cut along path at feed rate
    4. Retract to safe Z
    
    Args:
        tp: Toolpath with points
        depth_mm: Z depth for this pass (negative)
        req: Request with safe Z and surface Z
        feed_mm_min: Cutting feed rate (mm/min)
        plunge_mm_min: Plunge feed rate (mm/min)
    
    Returns:
        List of G-code lines
    """
    lines: List[str] = []
    if len(tp.points) < 2:
        return lines

    safe_z = req.safe_z_mm
    surf_z = req.surface_z_mm

    # 1) Rapid to first XY at safe Z
    x0, y0 = tp.points[0]
    lines.append(f"( pass at Z{depth_mm:.3f} )")
    lines.append(f"G0 Z{safe_z:.3f}")
    lines.append(f"G0 {format_point(x0, y0)}")

    # 2) Plunge to cutting depth
    lines.append(f"G1 Z{depth_mm:.3f} F{plunge_mm_min:.1f}")

    # 3) Cut along path
    lines.append(f"G1 F{feed_mm_min:.1f}")
    for i in range(1, len(tp.points)):
        x, y = tp.points[i]
        lines.append(f"G1 {format_point(x, y)}")

    # If closed path, return to start
    if tp.is_closed:
        lines.append(f"G1 {format_point(x0, y0)}")

    # 4) Retract to safe Z
    lines.append(f"G0 Z{safe_z:.3f}")
    lines.append("")

    return lines


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate_saw_gcode(req: SawGCodeRequest) -> SawGCodeResult:
    """
    Generate complete G-code for saw operation.
    
    Unified generator for slice, batch, and contour operations.
    Handles multi-pass depth control and safe entry/exit moves.
    
    Process:
    1. Plan depth passes based on DOC
    2. Convert feed rates to machine units
    3. Emit header
    4. For each depth pass:
       - For each toolpath:
         - Rapid to start
         - Plunge
         - Cut path
         - Retract
    5. Emit footer
    6. Calculate statistics
    
    Args:
        req: Complete G-code generation request
    
    Returns:
        SawGCodeResult with G-code and metadata
    
    Example:
        >>> from cam_core.gcode.gcode_models import SawGCodeRequest, SawToolpath
        >>> req = SawGCodeRequest(
        ...     op_type="slice",
        ...     toolpaths=[SawToolpath(points=[(0, 0), (100, 0)])],
        ...     total_depth_mm=3.0,
        ...     doc_per_pass_mm=1.0,
        ...     feed_ipm=60,
        ...     plunge_ipm=20
        ... )
        >>> result = generate_saw_gcode(req)
        >>> print(len(result.depth_passes))
        3
    """
    # Validate closed paths if required
    if req.closed_paths_only:
        for tp in req.toolpaths:
            if not tp.is_closed:
                raise ValueError(
                    f"closed_paths_only=True but toolpath with {len(tp.points)} points is open"
                )

    # Plan depth passes
    depth_passes = plan_depth_passes(req.total_depth_mm, req.doc_per_pass_mm)

    # Feed rate conversion
    if req.machine_units == "mm":
        feed_mm_min = ipm_to_mm_per_min(req.feed_ipm)
        plunge_mm_min = ipm_to_mm_per_min(req.plunge_ipm)
    else:
        # Machine already in inches/min
        feed_mm_min = req.feed_ipm
        plunge_mm_min = req.plunge_ipm

    # Generate G-code
    lines: List[str] = []
    lines.append(emit_header(req))

    # Depth-by-depth execution
    for dp in depth_passes:
        lines.append(f"( --- Depth pass to Z{dp.depth_mm:.3f} --- )")
        for tp in req.toolpaths:
            lines.extend(
                emit_toolpath_at_depth(
                    tp=tp,
                    depth_mm=dp.depth_mm,
                    req=req,
                    feed_mm_min=feed_mm_min,
                    plunge_mm_min=plunge_mm_min,
                )
            )

    lines.append(emit_footer())

    # Calculate statistics
    total_length = estimate_path_length_mm(req.toolpaths) * len(depth_passes)

    return SawGCodeResult(
        gcode="\n".join(lines),
        op_type=req.op_type,
        depth_passes=depth_passes,
        total_length_mm=total_length,
    )
