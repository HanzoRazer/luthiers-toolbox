"""
Fret Slots CAM Calculator

Generates CAM toolpaths (DXF R12 + G-code) for fret slot cutting operations.
Integrates with RMOS context for material-aware feedrate calculations and
feasibility checking.

Wave 17: Phase C - Fretboard CAM Operations
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
from math import sqrt

from ..instrument_geometry.neck.fret_math import compute_fret_positions_mm
from ..instrument_geometry.body.fretboard_geometry import (
    compute_width_at_position_mm,
    compute_fret_slot_lines,
)
from ..instrument_geometry.neck.neck_profiles import FretboardSpec
from ..rmos.context import RmosContext, CutType


@dataclass
class FretSlotToolpath:
    """
    Complete CAM toolpath data for a single fret slot.
    
    Attributes:
        fret_number: Fret number (1-based).
        position_mm: Distance from nut to fret center (X coordinate).
        width_mm: Fretboard width at this position.
        bass_point: (x, y) coordinate of bass-side endpoint.
        treble_point: (x, y) coordinate of treble-side endpoint.
        slot_depth_mm: Cutting depth for this slot.
        slot_width_mm: Kerf width (typically 0.5-0.6mm for fret saws).
        feed_rate_mmpm: Material-aware cutting feedrate.
        plunge_rate_mmpm: Material-aware plunge feedrate.
    """
    fret_number: int
    position_mm: float
    width_mm: float
    bass_point: Tuple[float, float]
    treble_point: Tuple[float, float]
    slot_depth_mm: float
    slot_width_mm: float
    feed_rate_mmpm: float
    plunge_rate_mmpm: float


@dataclass
class FretSlotCAMOutput:
    """
    Complete CAM output bundle for fretboard operations.
    
    Attributes:
        toolpaths: List of per-fret toolpath data.
        dxf_content: DXF R12 formatted file content.
        gcode_content: G-code program content.
        statistics: Operation statistics (time, length, etc.).
    """
    toolpaths: List[FretSlotToolpath]
    dxf_content: str
    gcode_content: str
    statistics: Dict[str, Any]


def compute_radius_blended_depth(
    base_radius_mm: Optional[float],
    end_radius_mm: Optional[float],
    position_mm: float,
    scale_length_mm: float,
    nominal_depth_mm: float = 3.0,
) -> float:
    """
    Compute fret slot depth with compound radius blending.
    
    For compound radius fretboards (common taper: 9.5" nut → 12" heel),
    the slot depth varies slightly to maintain consistent fret crown height
    above the curved surface.
    
    Args:
        base_radius_mm: Radius at nut (e.g., 241.3mm for 9.5").
        end_radius_mm: Radius at heel (e.g., 304.8mm for 12").
        position_mm: Distance from nut to current fret.
        scale_length_mm: Full scale length.
        nominal_depth_mm: Standard slot depth (typically 2.5-3.5mm).
    
    Returns:
        Adjusted depth in mm accounting for radius blend.
    
    Notes:
        - If base_radius_mm is None → flat fretboard, return nominal depth.
        - If end_radius_mm is None → constant radius, return nominal depth.
        - Blending uses linear interpolation of radius over scale length.
    """
    if base_radius_mm is None or end_radius_mm is None:
        return nominal_depth_mm
    
    # Linear blend ratio
    blend_ratio = min(1.0, max(0.0, position_mm / scale_length_mm))
    current_radius_mm = base_radius_mm + (end_radius_mm - base_radius_mm) * blend_ratio
    
    # Radius correction factor (tighter radius → slightly deeper cut)
    # This is a second-order effect; nominal depth is primary
    base_factor = 1.0
    if base_radius_mm > 0:
        base_factor = current_radius_mm / base_radius_mm
    
    # Clamp adjustment to ±10% of nominal
    adjusted_depth = nominal_depth_mm * base_factor
    return max(nominal_depth_mm * 0.9, min(nominal_depth_mm * 1.1, adjusted_depth))


def generate_fret_slot_toolpaths(
    spec: FretboardSpec,
    context: RmosContext,
    slot_depth_mm: float = 3.0,
    slot_width_mm: float = 0.58,  # Standard fret saw kerf
) -> List[FretSlotToolpath]:
    """
    Generate CAM toolpaths for all fret slots.
    
    Args:
        spec: Fretboard geometric specification.
        context: RMOS context with material and tooling data.
        slot_depth_mm: Nominal slot depth (2.5-3.5mm typical).
        slot_width_mm: Kerf width (0.5-0.6mm for fret saws).
    
    Returns:
        List of FretSlotToolpath objects, one per fret.
    
    Notes:
        - Feedrates extracted from context.material.density and hardness.
        - Compound radius adjustments applied if spec.base_radius_mm present.
        - Slots generated bass-to-treble (left-to-right in standard orientation).
    """
    fret_positions = compute_fret_positions_mm(spec.scale_length_mm, spec.fret_count)
    slot_lines = compute_fret_slot_lines(spec)
    
    toolpaths: List[FretSlotToolpath] = []
    
    # Extract feedrates from context (default to conservative values)
    # Typical fret slot: 1200-2000 mm/min in hardwoods, 300-600 mm/min plunge
    base_feed_mmpm = 1500.0
    base_plunge_mmpm = 400.0
    
    if context.materials:
        # Adjust for density: denser wood → slower feed
        density_factor = 1.0
        if context.materials.density_kg_m3:
            # Typical: 500 kg/m³ (balsa) → 1.2x, 1200 kg/m³ (ebony) → 0.6x
            reference_density = 700.0  # kg/m³ (maple/mahogany)
            density_factor = reference_density / context.materials.density_kg_m3
            density_factor = max(0.5, min(1.5, density_factor))
        
        base_feed_mmpm *= density_factor
        base_plunge_mmpm *= density_factor
    
    for i, (pos, (bass_pt, treble_pt)) in enumerate(zip(fret_positions, slot_lines)):
        fret_num = i + 1
        
        # Compute width at this position
        width = compute_width_at_position_mm(
            spec.nut_width_mm,
            spec.heel_width_mm,
            spec.scale_length_mm,
            spec.fret_count,
            pos,
        )
        
        # Radius-blended depth
        depth = compute_radius_blended_depth(
            spec.base_radius_mm,
            spec.end_radius_mm,
            pos,
            spec.scale_length_mm,
            slot_depth_mm,
        )
        
        toolpath = FretSlotToolpath(
            fret_number=fret_num,
            position_mm=pos,
            width_mm=width,
            bass_point=bass_pt,
            treble_point=treble_pt,
            slot_depth_mm=depth,
            slot_width_mm=slot_width_mm,
            feed_rate_mmpm=base_feed_mmpm,
            plunge_rate_mmpm=base_plunge_mmpm,
        )
        toolpaths.append(toolpath)
    
    return toolpaths


def export_dxf_r12(toolpaths: List[FretSlotToolpath]) -> str:
    """
    Export fret slot toolpaths as DXF R12 (AC1009) format.
    
    Each slot is represented as a LINE entity on layer "FRET_SLOTS".
    Compatible with Fusion 360, VCarve, and most CAM software.
    
    Args:
        toolpaths: List of FretSlotToolpath objects.
    
    Returns:
        DXF R12 formatted string.
    
    Notes:
        - Uses LINE entities (bass_point → treble_point).
        - All slots on single layer for batch selection.
        - Units: millimeters (DXF standard).
    """
    lines = [
        "0",
        "SECTION",
        "2",
        "HEADER",
        "9",
        "$ACADVER",
        "1",
        "AC1009",  # DXF R12 version
        "9",
        "$INSUNITS",
        "70",
        "4",  # Millimeters
        "0",
        "ENDSEC",
        "0",
        "SECTION",
        "2",
        "TABLES",
        "0",
        "TABLE",
        "2",
        "LAYER",
        "70",
        "1",
        "0",
        "LAYER",
        "2",
        "FRET_SLOTS",
        "70",
        "0",
        "62",
        "7",  # White color
        "0",
        "ENDTAB",
        "0",
        "ENDSEC",
        "0",
        "SECTION",
        "2",
        "ENTITIES",
    ]
    
    # Add LINE entity for each fret slot
    for tp in toolpaths:
        x1, y1 = tp.bass_point
        x2, y2 = tp.treble_point
        
        lines.extend([
            "0",
            "LINE",
            "8",
            "FRET_SLOTS",
            "10",
            f"{x1:.4f}",
            "20",
            f"{y1:.4f}",
            "30",
            "0.0000",
            "11",
            f"{x2:.4f}",
            "21",
            f"{y2:.4f}",
            "31",
            "0.0000",
        ])
    
    lines.extend([
        "0",
        "ENDSEC",
        "0",
        "EOF",
    ])
    
    return "\n".join(lines)


def generate_gcode(
    toolpaths: List[FretSlotToolpath],
    safe_z_mm: float = 5.0,
    post_id: str = "GRBL",
) -> str:
    """
    Generate G-code program for fret slot cutting.
    
    Args:
        toolpaths: List of FretSlotToolpath objects.
        safe_z_mm: Safe retract height above workpiece.
        post_id: Post-processor identifier (GRBL, Mach4, etc.).
    
    Returns:
        G-code program string.
    
    Notes:
        - Each slot: rapid to position → plunge → cut across → retract.
        - Feed rates adjusted per material from toolpath data.
        - Units: millimeters (G21).
    """
    lines = [
        f"(Fret Slot Program - {len(toolpaths)} slots)",
        f"(POST={post_id};UNITS=mm)",
        "G21 (Millimeters)",
        "G90 (Absolute positioning)",
        "G17 (XY plane)",
        "",
        f"G0 Z{safe_z_mm:.4f} (Safe height)",
        "",
    ]
    
    for tp in toolpaths:
        x1, y1 = tp.bass_point
        x2, y2 = tp.treble_point
        
        # Slot length for time estimation
        slot_length = sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        lines.append(f"(Fret {tp.fret_number} - Position: {tp.position_mm:.2f}mm)")
        lines.append(f"G0 X{x1:.4f} Y{y1:.4f} (Rapid to slot start)")
        lines.append(f"G1 Z{-tp.slot_depth_mm:.4f} F{tp.plunge_rate_mmpm:.1f} (Plunge)")
        lines.append(f"G1 X{x2:.4f} Y{y2:.4f} F{tp.feed_rate_mmpm:.1f} (Cut slot)")
        lines.append(f"G0 Z{safe_z_mm:.4f} (Retract)")
        lines.append("")
    
    lines.extend([
        "M30 (Program end)",
        "",
    ])
    
    return "\n".join(lines)


def compute_cam_statistics(
    toolpaths: List[FretSlotToolpath],
    safe_z_mm: float = 5.0,
    rapid_feed_mmpm: float = 3000.0,
) -> Dict[str, Any]:
    """
    Compute operation statistics for fret slot cutting.
    
    Args:
        toolpaths: List of FretSlotToolpath objects.
        safe_z_mm: Safe retract height (for rapid time).
        rapid_feed_mmpm: Rapid traverse rate.
    
    Returns:
        Dict with keys: total_time_s, cutting_length_mm, plunge_depth_mm,
                        slot_count, avg_feed_mmpm, estimated_cost_usd.
    """
    total_cutting_mm = 0.0
    total_plunge_mm = 0.0
    total_time_s = 0.0
    
    for tp in toolpaths:
        # Slot length (bass to treble)
        slot_length = sqrt(
            (tp.treble_point[0] - tp.bass_point[0])**2 +
            (tp.treble_point[1] - tp.bass_point[1])**2
        )
        total_cutting_mm += slot_length
        total_plunge_mm += tp.slot_depth_mm
        
        # Time: rapid + plunge + cut + retract
        rapid_time = (safe_z_mm * 2) / rapid_feed_mmpm * 60.0  # Z moves
        plunge_time = tp.slot_depth_mm / tp.plunge_rate_mmpm * 60.0
        cut_time = slot_length / tp.feed_rate_mmpm * 60.0
        
        total_time_s += rapid_time + plunge_time + cut_time
    
    avg_feed = sum(tp.feed_rate_mmpm for tp in toolpaths) / len(toolpaths) if toolpaths else 0.0
    
    # Cost estimation (rough): $0.05/slot for tooling wear + setup
    estimated_cost = len(toolpaths) * 0.05
    
    return {
        "slot_count": len(toolpaths),
        "total_cutting_length_mm": round(total_cutting_mm, 2),
        "total_plunge_depth_mm": round(total_plunge_mm, 2),
        "total_time_s": round(total_time_s, 1),
        "total_time_min": round(total_time_s / 60.0, 2),
        "avg_feed_mmpm": round(avg_feed, 1),
        "estimated_cost_usd": round(estimated_cost, 2),
    }


def generate_fret_slot_cam(
    spec: FretboardSpec,
    context: RmosContext,
    slot_depth_mm: float = 3.0,
    slot_width_mm: float = 0.58,
    safe_z_mm: float = 5.0,
    post_id: str = "GRBL",
) -> FretSlotCAMOutput:
    """
    Generate complete CAM output for fret slot operations.
    
    This is the top-level function for Phase C, orchestrating all
    toolpath generation, export, and statistics.
    
    Args:
        spec: Fretboard geometric specification.
        context: RMOS context with material/tooling data.
        slot_depth_mm: Nominal slot depth (2.5-3.5mm typical).
        slot_width_mm: Kerf width (0.5-0.6mm for fret saws).
        safe_z_mm: Safe retract height above workpiece.
        post_id: Post-processor identifier.
    
    Returns:
        FretSlotCAMOutput with toolpaths, DXF, G-code, and statistics.
    
    Example:
        >>> from instrument_geometry.neck.neck_profiles import FretboardSpec
        >>> from rmos.context import RmosContext
        >>> spec = FretboardSpec(42.0, 56.0, 648.0, 22)
        >>> ctx = RmosContext.from_model_id("strat_25_5")
        >>> output = generate_fret_slot_cam(spec, ctx)
        >>> print(output.statistics["slot_count"])  # 22
    """
    # Generate toolpaths
    toolpaths = generate_fret_slot_toolpaths(spec, context, slot_depth_mm, slot_width_mm)
    
    # Export formats
    dxf_content = export_dxf_r12(toolpaths)
    gcode_content = generate_gcode(toolpaths, safe_z_mm, post_id)
    
    # Statistics
    statistics = compute_cam_statistics(toolpaths, safe_z_mm)
    
    return FretSlotCAMOutput(
        toolpaths=toolpaths,
        dxf_content=dxf_content,
        gcode_content=gcode_content,
        statistics=statistics,
    )
