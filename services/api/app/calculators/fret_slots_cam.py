"""Fret Slots CAM Calculator - generates toolpaths for fret slot cutting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional, Literal
from math import sqrt, pi

from ..core.safety import safety_critical

from ..instrument_geometry.neck.fret_math import compute_fret_positions_mm
from ..instrument_geometry.body.fretboard_geometry import (
    compute_width_at_position_mm,
    compute_fret_slot_lines,
)
from ..instrument_geometry.neck.neck_profiles import FretboardSpec
from ..rmos.context import RmosContext
from ..data_registry import Registry


@dataclass
class FretSlotToolpath:
    """CAM toolpath data for a single fret slot."""
    fret_number: int
    position_mm: float
    width_mm: float
    bass_point: Tuple[float, float]
    treble_point: Tuple[float, float]
    slot_depth_mm: float
    slot_width_mm: float
    feed_rate_mmpm: float
    plunge_rate_mmpm: float
    angle_rad: float = 0.0
    is_perpendicular: bool = False


@dataclass
class FretSlotCAMOutput:
    """Complete CAM output bundle for fretboard operations."""
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


@safety_critical
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
            # Get reference density from registry (maple/mahogany baseline)
            # Default to 700 kg/m³ if registry not available
            reference_density = 700.0
            try:
                # Try to get from system tier (all editions)
                registry = Registry(edition="express")  # Use minimal edition for system data
                woods = registry.get_wood_species()
                if woods and "species" in woods:
                    # Use maple_hard as reference (most common neck material)
                    maple = woods["species"].get("maple_hard", {})
                    reference_density = maple.get("density_kg_m3", 700.0)
            except (ImportError, KeyError, TypeError, AttributeError):  # WP-1
                pass  # Fall back to hardcoded 700.0
            
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




def export_dxf_r12(toolpaths: List[FretSlotToolpath], mode: str = 'standard') -> str:
    """
    Export fret slot toolpaths as DXF R12 (AC1009) format.
    
    Each slot is represented as a LINE entity on layer "FRET_SLOTS" (standard)
    or "FRET_SLOTS_FAN" (fan-fret mode).
    Compatible with Fusion 360, VCarve, and most CAM software.
    
    Args:
        toolpaths: List of FretSlotToolpath objects.
        mode: 'standard' or 'fan' (determines layer name).
    
    Returns:
        DXF R12 formatted string.
    
    Notes:
        - Uses LINE entities (bass_point → treble_point).
        - All slots on single layer for batch selection.
        - Units: millimeters (DXF standard).
        - Fan-fret slots include angle metadata in comments.
    """
    layer_name = "FRET_SLOTS" if mode == 'standard' else "FRET_SLOTS_FAN"
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
        layer_name,
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
        
        # Add comment for fan-fret angles
        if mode == 'fan' and abs(tp.angle_rad) > 0.001:
            angle_deg = tp.angle_rad * 180.0 / pi
            lines.extend([
                "999",
                f"FRET_{tp.fret_number}_ANGLE_{angle_deg:.2f}_DEG",
            ])
        
        lines.extend([
            "0",
            "LINE",
            "8",
            layer_name,
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


@safety_critical
def generate_gcode(
    toolpaths: List[FretSlotToolpath],
    safe_z_mm: float = 5.0,
    post_id: str = "GRBL",
    mode: str = 'standard',
) -> str:
    """
    Generate G-code program for fret slot cutting.
    
    Args:
        toolpaths: List of FretSlotToolpath objects.
        safe_z_mm: Safe retract height above workpiece.
        post_id: Post-processor identifier (GRBL, Mach4, etc.).
        mode: 'standard' or 'fan' (affects angle handling).
    
    Returns:
        G-code program string.
    
    Notes:
        - Each slot: rapid to position → plunge → cut across → retract.
        - Feed rates adjusted per material from toolpath data.
        - Units: millimeters (G21).
        - Fan-fret mode includes angle information in comments.
    """
    lines = [
        f"(Fret Slot Program - {len(toolpaths)} slots)",
        f"(POST={post_id};UNITS=mm;MODE={mode})",
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
        
        # Add angle info for fan-fret
        if mode == 'fan' and abs(tp.angle_rad) > 0.001:
            angle_deg = tp.angle_rad * 180.0 / pi
            lines.append(f"(Fret {tp.fret_number} - Position: {tp.position_mm:.2f}mm - Angle: {angle_deg:.2f}°)")
        else:
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
    
    # Calculate max angle for fan-fret (in degrees)
    max_angle_rad = max((abs(tp.angle_rad) for tp in toolpaths), default=0.0)
    max_angle_deg = max_angle_rad * 180.0 / pi
    
    return {
        "slot_count": len(toolpaths),
        "max_angle_deg": max_angle_deg,
        "total_cutting_length_mm": round(total_cutting_mm, 2),
        "total_plunge_depth_mm": round(total_plunge_mm, 2),
        "total_time_s": round(total_time_s, 1),
        "total_time_min": round(total_time_s / 60.0, 2),
        "avg_feed_mmpm": round(avg_feed, 1),
        "estimated_cost_usd": round(estimated_cost, 2),
    }


@safety_critical
def generate_fret_slot_cam(
    spec: FretboardSpec,
    context: RmosContext,
    slot_depth_mm: float = 3.0,
    slot_width_mm: float = 0.58,
    safe_z_mm: float = 5.0,
    post_id: str = "GRBL",
    mode: Literal["standard", "fan"] = "standard",
    treble_scale_mm: Optional[float] = None,
    bass_scale_mm: Optional[float] = None,
    perpendicular_fret: Optional[int] = None,
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
        mode: "standard" for regular fretting, "fan" for multi-scale.
        treble_scale_mm: Scale length on treble side (fan mode only).
        bass_scale_mm: Scale length on bass side (fan mode only).
        perpendicular_fret: Perpendicular fret number (fan mode only).
    
    Returns:
        FretSlotCAMOutput with toolpaths, DXF, G-code, and statistics.
    
    Example (Standard):
        >>> from instrument_geometry.neck.neck_profiles import FretboardSpec
        >>> from rmos.context import RmosContext
        >>> spec = FretboardSpec(42.0, 56.0, 648.0, 22)
        >>> ctx = RmosContext.from_model_id("strat_25_5")
        >>> output = generate_fret_slot_cam(spec, ctx)
        >>> print(output.statistics["slot_count"])  # 22
    
    Example (Fan-Fret):
        >>> output = generate_fret_slot_cam(
        ...     spec, ctx, mode="fan",
        ...     treble_scale_mm=648.0, bass_scale_mm=686.0,
        ...     perpendicular_fret=7
        ... )
        >>> print(output.statistics["slot_count"])  # 22
    """
    if mode == "fan":
        # Fan-fret mode (extracted to fret_slots_fan_cam.py)
        from .fret_slots_fan_cam import generate_fan_fret_cam
        return generate_fan_fret_cam(
            spec=spec,
            context=context,
            treble_scale_mm=treble_scale_mm,
            bass_scale_mm=bass_scale_mm,
            perpendicular_fret=perpendicular_fret or 7,
            slot_depth_mm=slot_depth_mm,
            slot_width_mm=slot_width_mm,
            safe_z_mm=safe_z_mm,
            post_id=post_id,
        )
    else:
        # Standard mode (existing code)
        toolpaths = generate_fret_slot_toolpaths(spec, context, slot_depth_mm, slot_width_mm)
        dxf_content = export_dxf_r12(toolpaths)
        gcode_content = generate_gcode(toolpaths, safe_z_mm, post_id)
        statistics = compute_cam_statistics(toolpaths, safe_z_mm)
        
        return FretSlotCAMOutput(
            toolpaths=toolpaths,
            dxf_content=dxf_content,
            gcode_content=gcode_content,
            statistics=statistics,
        )
