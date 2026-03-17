"""
OM-PURF-05: Binding Corner Miter G-code

Calculate miter angles at corners where binding strips meet and generate
clean corner cut moves for the CNC router.

Workflow:
1. Identify corners in the binding path (angle between adjacent segments)
2. Calculate miter angle (half the corner angle for clean join)
3. Generate corner miter cut moves (small diagonal approach/departure)
4. Return corner positions with angles for binding strip preparation

A miter joint occurs where two binding strips meet at an angle:
- Straight sections: no miter needed
- Gentle curves: no miter needed (strip bends)
- Sharp corners (>20 deg): miter cut required
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

Pt = Tuple[float, float]


# =============================================================================
# CORNER DETECTION
# =============================================================================

def _vector_angle(v: Pt) -> float:
    """Calculate angle of vector from X-axis in radians (-pi to pi)."""
    return math.atan2(v[1], v[0])


def _angle_between_segments(p1: Pt, p2: Pt, p3: Pt) -> float:
    """
    Calculate the angle at p2 formed by segments p1->p2 and p2->p3.

    Returns angle in degrees (0-180).
    A straight line returns ~180 degrees.
    A right-angle corner returns ~90 degrees.
    """
    # Vector from p1 to p2
    v1 = (p2[0] - p1[0], p2[1] - p1[1])
    # Vector from p2 to p3
    v2 = (p3[0] - p2[0], p3[1] - p2[1])

    # Normalize
    len1 = (v1[0]**2 + v1[1]**2) ** 0.5
    len2 = (v2[0]**2 + v2[1]**2) ** 0.5

    if len1 < 1e-9 or len2 < 1e-9:
        return 180.0  # Degenerate segment

    # Dot product for angle
    dot = (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)
    # Clamp to [-1, 1] for numerical stability
    dot = max(-1.0, min(1.0, dot))

    angle_rad = math.acos(dot)
    return math.degrees(angle_rad)


def _compute_miter_angle(corner_angle_deg: float) -> float:
    """
    Compute the miter cut angle from the corner angle.

    For a corner of angle A (interior angle at vertex):
    - Miter angle = (180 - A) / 2
    - This creates two complementary cuts that meet at the corner

    Example:
    - 90-degree corner (right angle): miter = 45 degrees
    - 60-degree corner (acute): miter = 60 degrees
    - 120-degree corner (obtuse): miter = 30 degrees
    """
    return (180.0 - corner_angle_deg) / 2


def _segment_direction(p1: Pt, p2: Pt) -> float:
    """Calculate direction angle of segment p1->p2 in degrees."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.degrees(math.atan2(dy, dx))


# =============================================================================
# CORNER MITER DATA STRUCTURES
# =============================================================================

@dataclass
class CornerMiter:
    """A single corner miter specification."""

    # Corner position
    position: Pt
    vertex_index: int

    # Angles (degrees)
    corner_angle_deg: float  # Interior angle at vertex (0-180)
    miter_angle_deg: float   # Cut angle for binding strip
    incoming_direction_deg: float  # Direction of segment approaching corner
    outgoing_direction_deg: float  # Direction of segment leaving corner

    # Miter geometry
    miter_depth_mm: float  # How far the miter cut extends

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": list(self.position),
            "vertex_index": self.vertex_index,
            "corner_angle_deg": round(self.corner_angle_deg, 2),
            "miter_angle_deg": round(self.miter_angle_deg, 2),
            "incoming_direction_deg": round(self.incoming_direction_deg, 2),
            "outgoing_direction_deg": round(self.outgoing_direction_deg, 2),
            "miter_depth_mm": round(self.miter_depth_mm, 3),
        }


@dataclass
class CornerMiterConfig:
    """Configuration for corner miter detection and G-code generation."""

    # Corner detection threshold
    corner_threshold_deg: float = 20.0  # Angles sharper than (180 - this) are corners

    # Miter geometry
    binding_width_mm: float = 2.5  # Width of binding strip
    miter_depth_mm: float = 0.0    # Calculated from binding_width if 0

    # Tool parameters
    tool_diameter_mm: float = 1.5  # Small bit for corner cuts

    # Feed rates (mm/min)
    feed_rate: float = 300.0   # Slow for precision
    plunge_rate: float = 60.0

    # Safety
    safe_z_mm: float = 5.0
    retract_z_mm: float = 2.0

    # Cut depth
    cut_depth_mm: float = 2.0  # Depth of miter cut

    def __post_init__(self):
        # Calculate miter depth from binding width if not specified
        if self.miter_depth_mm <= 0:
            # Miter extends 1.5x binding width for clean corner
            self.miter_depth_mm = self.binding_width_mm * 1.5


@dataclass
class CornerMiterResult:
    """Result of corner miter analysis."""

    corners: List[CornerMiter]
    gcode: str
    total_corners: int
    sharp_corners: int  # Corners needing miter (< 160 deg)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "corners": [c.to_dict() for c in self.corners],
            "total_corners": self.total_corners,
            "sharp_corners": self.sharp_corners,
            "warnings": self.warnings,
        }


# =============================================================================
# CORNER MITER ANALYSIS
# =============================================================================

def detect_corners(
    path: List[Pt],
    threshold_deg: float = 20.0,
) -> List[Tuple[int, Pt, float]]:
    """
    Detect corners in a path where miter cuts are needed.

    Args:
        path: Closed polygon path (first point != last point)
        threshold_deg: Deviation from 180 that triggers corner detection

    Returns:
        List of (vertex_index, position, corner_angle_deg)
    """
    if len(path) < 3:
        return []

    corners = []
    n = len(path)

    for i in range(n):
        p1 = path[(i - 1) % n]
        p2 = path[i]
        p3 = path[(i + 1) % n]

        angle = _angle_between_segments(p1, p2, p3)

        # Sharp corner = angle significantly less than 180
        if angle < (180.0 - threshold_deg):
            corners.append((i, p2, angle))

    return corners


def analyze_corner_miters(
    path: List[Pt],
    config: Optional[CornerMiterConfig] = None,
) -> CornerMiterResult:
    """
    Analyze binding path corners and calculate miter angles.

    Args:
        path: Closed polygon path for binding
        config: Miter configuration

    Returns:
        CornerMiterResult with all corner miters
    """
    cfg = config or CornerMiterConfig()
    warnings = []

    if len(path) < 3:
        warnings.append("Path has fewer than 3 points - no corners possible")
        return CornerMiterResult(
            corners=[],
            gcode="",
            total_corners=0,
            sharp_corners=0,
            warnings=warnings,
        )

    # Detect corners
    corner_data = detect_corners(path, cfg.corner_threshold_deg)

    # Build CornerMiter objects
    n = len(path)
    miters: List[CornerMiter] = []

    for idx, pos, angle in corner_data:
        # Calculate directions
        prev_pt = path[(idx - 1) % n]
        next_pt = path[(idx + 1) % n]

        incoming_dir = _segment_direction(prev_pt, pos)
        outgoing_dir = _segment_direction(pos, next_pt)

        miter_angle = _compute_miter_angle(angle)

        # Validate
        if miter_angle > 60:
            warnings.append(
                f"Corner at index {idx} has very acute angle ({angle:.1f}deg) - "
                f"miter angle {miter_angle:.1f}deg may be difficult to cut"
            )

        miters.append(CornerMiter(
            position=pos,
            vertex_index=idx,
            corner_angle_deg=angle,
            miter_angle_deg=miter_angle,
            incoming_direction_deg=incoming_dir,
            outgoing_direction_deg=outgoing_dir,
            miter_depth_mm=cfg.miter_depth_mm,
        ))

    # Generate G-code
    gcode = generate_corner_miter_gcode(miters, cfg)

    return CornerMiterResult(
        corners=miters,
        gcode=gcode,
        total_corners=len(path),  # Total vertices
        sharp_corners=len(miters),  # Vertices needing miter
        warnings=warnings,
    )


# =============================================================================
# G-CODE GENERATION
# =============================================================================

def generate_corner_miter_gcode(
    miters: List[CornerMiter],
    config: CornerMiterConfig,
) -> str:
    """
    Generate G-code for corner miter cuts.

    Each corner gets a small V-shaped cut that:
    1. Approaches from the incoming direction
    2. Cuts to the corner vertex
    3. Departs in the outgoing direction

    This creates clean miter surfaces where binding strips join.
    """
    cfg = config
    lines = []

    # Header
    lines.append("(Binding Corner Miter Cuts - OM-PURF-05)")
    lines.append(f"(Total corners: {len(miters)})")
    lines.append(f"(Tool: {cfg.tool_diameter_mm}mm bit)")
    lines.append(f"(Cut depth: {cfg.cut_depth_mm}mm)")
    lines.append("")

    # Setup
    lines.append("G21 (Units: mm)")
    lines.append("G90 (Absolute positioning)")
    lines.append("G17 (XY plane)")
    lines.append(f"G0 Z{cfg.safe_z_mm:.3f} (Safe height)")
    lines.append("M3 S18000 (Spindle on)")
    lines.append("")

    if not miters:
        lines.append("(No corners requiring miter cuts)")
        lines.append("M5 (Spindle off)")
        lines.append("M30 (Program end)")
        return "\n".join(lines)

    z_depth = -cfg.cut_depth_mm

    for i, miter in enumerate(miters):
        cx, cy = miter.position
        depth = miter.miter_depth_mm

        # Calculate approach and departure points
        # Approach: start from incoming direction
        in_rad = math.radians(miter.incoming_direction_deg)
        approach_x = cx - depth * math.cos(in_rad)
        approach_y = cy - depth * math.sin(in_rad)

        # Departure: end in outgoing direction
        out_rad = math.radians(miter.outgoing_direction_deg)
        depart_x = cx + depth * math.cos(out_rad)
        depart_y = cy + depth * math.sin(out_rad)

        lines.append(f"(Corner {i+1}: vertex {miter.vertex_index}, miter {miter.miter_angle_deg:.1f}deg)")

        # Rapid to approach point
        lines.append(f"G0 X{approach_x:.3f} Y{approach_y:.3f}")
        lines.append(f"G0 Z{cfg.retract_z_mm:.3f}")

        # Plunge
        lines.append(f"G1 Z{z_depth:.3f} F{cfg.plunge_rate:.0f}")

        # Cut to corner vertex
        lines.append(f"G1 X{cx:.3f} Y{cy:.3f} F{cfg.feed_rate:.0f}")

        # Cut to departure point
        lines.append(f"G1 X{depart_x:.3f} Y{depart_y:.3f} F{cfg.feed_rate:.0f}")

        # Retract
        lines.append(f"G0 Z{cfg.retract_z_mm:.3f}")
        lines.append("")

    # Footer
    lines.append("M5 (Spindle off)")
    lines.append(f"G0 Z{cfg.safe_z_mm:.3f} (Final retract)")
    lines.append("M30 (Program end)")

    return "\n".join(lines)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def calculate_corner_miters(
    path: List[Pt],
    binding_width_mm: float = 2.5,
    corner_threshold_deg: float = 20.0,
) -> List[Dict[str, Any]]:
    """
    Convenience function to calculate corner miters for a binding path.

    Args:
        path: Closed polygon path
        binding_width_mm: Width of binding strip
        corner_threshold_deg: Threshold for corner detection

    Returns:
        List of corner miter dictionaries
    """
    config = CornerMiterConfig(
        binding_width_mm=binding_width_mm,
        corner_threshold_deg=corner_threshold_deg,
    )
    result = analyze_corner_miters(path, config)
    return [m.to_dict() for m in result.corners]


def generate_binding_corner_gcode(
    path: List[Pt],
    binding_width_mm: float = 2.5,
    cut_depth_mm: float = 2.0,
    tool_diameter_mm: float = 1.5,
    feed_rate: float = 300.0,
) -> str:
    """
    Convenience function to generate corner miter G-code.

    Args:
        path: Closed polygon path
        binding_width_mm: Width of binding strip
        cut_depth_mm: Depth of miter cut
        tool_diameter_mm: Tool diameter
        feed_rate: XY feed rate (mm/min)

    Returns:
        G-code string
    """
    config = CornerMiterConfig(
        binding_width_mm=binding_width_mm,
        cut_depth_mm=cut_depth_mm,
        tool_diameter_mm=tool_diameter_mm,
        feed_rate=feed_rate,
    )
    result = analyze_corner_miters(path, config)
    return result.gcode
