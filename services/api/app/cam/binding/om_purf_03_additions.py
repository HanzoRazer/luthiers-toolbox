"""
OM-PURF-03: Second-Pass Purfling Ledge + Neck-Specific Purfling Path

This module extends purfling_ledge.py with:
1. Second-pass function for shallow step creation
2. Neck-specific purfling path using taper angle
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

Pt = Tuple[float, float]


# =============================================================================
# OM-PURF-03: Second-Pass Purfling Ledge (Shallow Step for Strip Seating)
# =============================================================================

@dataclass
class SecondPassConfig:
    """
    Configuration for purfling ledge second pass.

    The second pass creates a shallower step inside the first-pass ledge
    where the purfling strip seats. This creates a clean reveal edge.
    """
    # Step dimensions (inside the first-pass ledge)
    ledge_width_mm: float = 0.8  # Width of the step
    ledge_depth_mm: float = 0.4  # Shallow depth for strip seating

    # Tool parameters
    tool_diameter_mm: float = 1.0  # Even smaller bit for detail

    # Feed rates (mm/min) - slow for precision
    feed_rate: float = 400.0
    plunge_rate: float = 80.0

    # Safety
    safe_z_mm: float = 5.0
    retract_z_mm: float = 2.0


def generate_second_pass_gcode(
    path: List[Pt],
    config: Optional[SecondPassConfig] = None,
) -> str:
    """
    Generate G-code for the purfling ledge second pass.

    The second pass creates a shallow step inside the first-pass ledge
    for the purfling strip to seat in. This is typically:
    - Narrower than the first pass
    - Shallower (0.3-0.5mm vs 0.8-1.0mm)
    - Uses a smaller tool for cleaner edges

    Args:
        path: Purfling ledge path (from first pass offset)
        config: Second pass configuration

    Returns:
        G-code string for the second pass operation

    Example:
        >>> path = [(0, 0), (100, 0), (100, 50), (0, 50)]
        >>> gcode = generate_second_pass_gcode(path)
    """
    cfg = config or SecondPassConfig()
    lines = []

    # Header
    lines.append("(Purfling Ledge Second Pass - OM-PURF-03)")
    lines.append(f"(Step: {cfg.ledge_width_mm}mm W x {cfg.ledge_depth_mm}mm D)")
    lines.append(f"(Tool: {cfg.tool_diameter_mm}mm bit)")
    lines.append("")

    # Setup
    lines.append("G21 (Units: mm)")
    lines.append("G90 (Absolute positioning)")
    lines.append("G17 (XY plane)")
    lines.append(f"G0 Z{cfg.safe_z_mm:.3f} (Safe height)")
    lines.append("M3 S22000 (Spindle on - high RPM for detail bit)")
    lines.append("")

    if not path:
        lines.append("(WARNING: Empty path - no cuts generated)")
        lines.append("M5 (Spindle off)")
        lines.append("M30 (Program end)")
        return "\n".join(lines)

    # Single pass for shallow step
    z_depth = -cfg.ledge_depth_mm
    lines.append(f"(Second Pass: Z={z_depth:.3f})")

    # Rapid to start
    start = path[0]
    lines.append(f"G0 X{start[0]:.3f} Y{start[1]:.3f}")
    lines.append(f"G0 Z{cfg.retract_z_mm:.3f}")

    # Plunge
    lines.append(f"G1 Z{z_depth:.3f} F{cfg.plunge_rate:.0f}")

    # Cut around path
    for pt in path[1:]:
        lines.append(f"G1 X{pt[0]:.3f} Y{pt[1]:.3f} F{cfg.feed_rate:.0f}")

    # Close path
    lines.append(f"G1 X{start[0]:.3f} Y{start[1]:.3f} F{cfg.feed_rate:.0f}")

    # Retract
    lines.append(f"G0 Z{cfg.safe_z_mm:.3f}")
    lines.append("")

    # Footer
    lines.append("M5 (Spindle off)")
    lines.append(f"G0 Z{cfg.safe_z_mm:.3f} (Final retract)")
    lines.append("M30 (Program end)")

    return "\n".join(lines)


# =============================================================================
# OM-PURF-03: Neck-Specific Purfling Path
# =============================================================================

@dataclass
class NeckPurflingConfig:
    """
    Configuration for neck binding/purfling path.

    The neck has a different geometry than the body:
    - Binding runs along the fretboard edges (not around a closed polygon)
    - The path tapers from heel to nut
    - Uses neck taper angle from NeckDimensions
    """
    # Neck dimensions (mm)
    nut_width_mm: float = 43.0  # Width at nut
    heel_width_mm: float = 57.0  # Width at heel
    fretboard_length_mm: float = 480.0  # Nut to body joint

    # Binding parameters
    binding_width_mm: float = 1.5
    purfling_offset_mm: float = 2.0  # From fretboard edge

    # Ledge dimensions
    ledge_width_mm: float = 0.8
    ledge_depth_mm: float = 0.4

    # Tool
    tool_diameter_mm: float = 1.0

    # Feed rates
    feed_rate: float = 400.0
    plunge_rate: float = 80.0

    # Safety
    safe_z_mm: float = 5.0

    @property
    def taper_angle_degrees(self) -> float:
        """Calculate neck taper angle from nut/heel widths."""
        width_diff = self.heel_width_mm - self.nut_width_mm
        # Taper is on each side, so divide by 2
        return math.degrees(math.atan2(width_diff / 2, self.fretboard_length_mm))


@dataclass
class NeckPurflingResult:
    """Result of neck purfling path generation."""
    gcode: str
    left_edge_path: List[Pt]
    right_edge_path: List[Pt]
    taper_angle_degrees: float
    total_length_mm: float
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gcode": self.gcode,
            "left_edge_path": self.left_edge_path,
            "right_edge_path": self.right_edge_path,
            "taper_angle_degrees": round(self.taper_angle_degrees, 3),
            "total_length_mm": round(self.total_length_mm, 2),
            "warnings": self.warnings,
        }


def generate_neck_purfling_path(
    config: Optional[NeckPurflingConfig] = None,
) -> NeckPurflingResult:
    """
    Generate purfling path for neck binding.

    The neck purfling path runs along both edges of the fretboard,
    tapering from the wider heel to the narrower nut.

    Args:
        config: Neck purfling configuration

    Returns:
        NeckPurflingResult with G-code and path geometry

    Example:
        >>> cfg = NeckPurflingConfig(nut_width_mm=43, heel_width_mm=57)
        >>> result = generate_neck_purfling_path(cfg)
        >>> print(f"Taper angle: {result.taper_angle_degrees:.2f}deg")
    """
    cfg = config or NeckPurflingConfig()
    warnings = []

    # Validate
    if cfg.heel_width_mm <= cfg.nut_width_mm:
        warnings.append("Heel width should be greater than nut width for standard taper")

    taper_angle = cfg.taper_angle_degrees
    if abs(taper_angle) > 3:
        warnings.append(f"Taper angle {taper_angle:.2f} deg is unusually steep")

    # Calculate edge paths
    # Origin at nut center, Y along neck length
    half_nut = cfg.nut_width_mm / 2
    half_heel = cfg.heel_width_mm / 2
    length = cfg.fretboard_length_mm

    # Left edge (negative X)
    left_edge: List[Pt] = [
        (-half_nut - cfg.purfling_offset_mm, 0),  # Nut end
        (-half_heel - cfg.purfling_offset_mm, length),  # Heel end
    ]

    # Right edge (positive X)
    right_edge: List[Pt] = [
        (half_nut + cfg.purfling_offset_mm, 0),  # Nut end
        (half_heel + cfg.purfling_offset_mm, length),  # Heel end
    ]

    # Calculate total length
    def path_length(path: List[Pt]) -> float:
        total = 0.0
        for i in range(1, len(path)):
            dx = path[i][0] - path[i-1][0]
            dy = path[i][1] - path[i-1][1]
            total += (dx**2 + dy**2) ** 0.5
        return total

    total_length = path_length(left_edge) + path_length(right_edge)

    # Generate G-code
    lines = []
    lines.append("(Neck Purfling Path - OM-PURF-03)")
    lines.append(f"(Nut width: {cfg.nut_width_mm}mm, Heel width: {cfg.heel_width_mm}mm)")
    lines.append(f"(Taper angle: {taper_angle:.3f} deg)")
    lines.append(f"(Tool: {cfg.tool_diameter_mm}mm bit)")
    lines.append("")

    # Setup
    lines.append("G21 (Units: mm)")
    lines.append("G90 (Absolute positioning)")
    lines.append(f"G0 Z{cfg.safe_z_mm:.3f}")
    lines.append("M3 S22000")
    lines.append("")

    z_depth = -cfg.ledge_depth_mm

    # Left edge
    lines.append("(Left edge - nut to heel)")
    lines.append(f"G0 X{left_edge[0][0]:.3f} Y{left_edge[0][1]:.3f}")
    lines.append("G0 Z2.000")
    lines.append(f"G1 Z{z_depth:.3f} F{cfg.plunge_rate:.0f}")
    lines.append(f"G1 X{left_edge[1][0]:.3f} Y{left_edge[1][1]:.3f} F{cfg.feed_rate:.0f}")
    lines.append(f"G0 Z{cfg.safe_z_mm:.3f}")
    lines.append("")

    # Right edge
    lines.append("(Right edge - nut to heel)")
    lines.append(f"G0 X{right_edge[0][0]:.3f} Y{right_edge[0][1]:.3f}")
    lines.append("G0 Z2.000")
    lines.append(f"G1 Z{z_depth:.3f} F{cfg.plunge_rate:.0f}")
    lines.append(f"G1 X{right_edge[1][0]:.3f} Y{right_edge[1][1]:.3f} F{cfg.feed_rate:.0f}")
    lines.append(f"G0 Z{cfg.safe_z_mm:.3f}")
    lines.append("")

    # Footer
    lines.append("M5")
    lines.append("M30")

    return NeckPurflingResult(
        gcode="\n".join(lines),
        left_edge_path=left_edge,
        right_edge_path=right_edge,
        taper_angle_degrees=taper_angle,
        total_length_mm=total_length,
        warnings=warnings,
    )


def generate_neck_purfling_gcode(
    nut_width_mm: float = 43.0,
    heel_width_mm: float = 57.0,
    fretboard_length_mm: float = 480.0,
    ledge_depth_mm: float = 0.4,
    feed_rate: float = 400.0,
    tool_diameter_mm: float = 1.0,
) -> str:
    """
    Convenience function to generate neck purfling G-code.

    Uses neck taper angle calculated from nut/heel widths.

    Args:
        nut_width_mm: Width at nut
        heel_width_mm: Width at heel
        fretboard_length_mm: Length from nut to body joint
        ledge_depth_mm: Purfling ledge depth
        feed_rate: XY feed rate (mm/min)
        tool_diameter_mm: Tool diameter

    Returns:
        G-code string
    """
    config = NeckPurflingConfig(
        nut_width_mm=nut_width_mm,
        heel_width_mm=heel_width_mm,
        fretboard_length_mm=fretboard_length_mm,
        ledge_depth_mm=ledge_depth_mm,
        feed_rate=feed_rate,
        tool_diameter_mm=tool_diameter_mm,
    )
    return generate_neck_purfling_path(config).gcode
