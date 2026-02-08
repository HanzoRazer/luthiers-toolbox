"""Fan-fret (multi-scale) CAM generation.

Extracted from ``fret_slots_cam.py`` (WP-3 decomposition).
Provides fan-fret toolpath generation, DXF R12 export, and
the top-level ``generate_fan_fret_cam()`` orchestrator.
"""
from __future__ import annotations

from math import pi
from typing import Callable, List, Optional

from ..instrument_geometry.neck.fret_math import (
    compute_fan_fret_positions,
    validate_fan_fret_geometry,
    FanFretPoint,
)
from ..instrument_geometry.body.fretboard_geometry import (
    compute_width_at_position_mm,
)
from ..instrument_geometry.neck.neck_profiles import FretboardSpec
from ..rmos.context import RmosContext


def generate_fan_fret_cam(
    spec: FretboardSpec,
    context: RmosContext,
    treble_scale_mm: Optional[float],
    bass_scale_mm: Optional[float],
    perpendicular_fret: int,
    slot_depth_mm: float,
    slot_width_mm: float,
    safe_z_mm: float,
    post_id: str,
) -> "FretSlotCAMOutput":
    """Fan-fret CAM generation orchestrator.

    Validates geometry, computes fan-fret positions, generates toolpaths,
    DXF content, G-code, and statistics.
    """
    # Lazy imports to avoid circular dependency with fret_slots_cam.py
    from .fret_slots_cam import (
        FretSlotToolpath as _TP,
        FretSlotCAMOutput as _Out,
        compute_radius_blended_depth,
        generate_gcode,
        compute_cam_statistics,
    )

    # Validate fan-fret parameters
    if treble_scale_mm is None or bass_scale_mm is None:
        raise ValueError("Fan-fret mode requires treble_scale_mm and bass_scale_mm")

    is_valid, error_msg = validate_fan_fret_geometry(
        treble_scale_mm, bass_scale_mm, perpendicular_fret, spec.fret_count
    )
    if not is_valid:
        raise ValueError(f"Invalid fan-fret geometry: {error_msg}")

    # Compute fan-fret positions
    fret_points = compute_fan_fret_positions(
        treble_scale_mm=treble_scale_mm,
        bass_scale_mm=bass_scale_mm,
        fret_count=spec.fret_count,
        perpendicular_fret=perpendicular_fret,
        nut_width_mm=spec.nut_width_mm,
        heel_width_mm=spec.heel_width_mm,
        scale_length_reference_mm=treble_scale_mm,
    )

    # Generate toolpaths from fan-fret points
    toolpaths = _generate_fan_fret_toolpaths(
        fret_points=fret_points,
        spec=spec,
        context=context,
        treble_scale_mm=treble_scale_mm,
        slot_depth_mm=slot_depth_mm,
        slot_width_mm=slot_width_mm,
        compute_radius_blended_depth_fn=compute_radius_blended_depth,
        FretSlotToolpath_cls=_TP,
    )

    # Export with fan-fret layer
    dxf_content = export_fan_fret_dxf_r12(toolpaths)
    gcode_content = generate_gcode(toolpaths, safe_z_mm, post_id, mode="fan")
    statistics = compute_cam_statistics(toolpaths, safe_z_mm)

    # Add fan-fret metadata to statistics
    statistics["mode"] = "fan"
    statistics["treble_scale_mm"] = treble_scale_mm
    statistics["bass_scale_mm"] = bass_scale_mm
    statistics["perpendicular_fret"] = perpendicular_fret
    statistics["max_angle_deg"] = max(
        abs(tp.angle_rad) * 180.0 / pi for tp in toolpaths
    )

    return _Out(
        toolpaths=toolpaths,
        dxf_content=dxf_content,
        gcode_content=gcode_content,
        statistics=statistics,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _generate_fan_fret_toolpaths(
    fret_points: List[FanFretPoint],
    spec: FretboardSpec,
    context: RmosContext,
    treble_scale_mm: float,
    slot_depth_mm: float,
    slot_width_mm: float,
    *,
    compute_radius_blended_depth_fn: Callable,
    FretSlotToolpath_cls: type,
) -> List["FretSlotToolpath"]:
    """Generate toolpaths from FanFretPoint geometry."""
    toolpaths: List["FretSlotToolpath"] = []

    # Calculate base feedrates (material-aware)
    base_feed_mmpm = 1200.0  # Default for hardwood
    base_plunge_mmpm = 300.0

    if context.materials:
        density_factor = 1.0
        if context.materials.density_kg_m3:
            reference_density = 700.0  # kg/m³
            density_factor = reference_density / context.materials.density_kg_m3
            density_factor = max(0.5, min(1.5, density_factor))

        base_feed_mmpm *= density_factor
        base_plunge_mmpm *= density_factor

    # Skip fret 0 (nut) - start from fret 1
    for fret_point in fret_points[1:]:
        # Average X position for width/depth calculations
        avg_x = (fret_point.treble_pos_mm + fret_point.bass_pos_mm) / 2.0

        # Compute width at this position
        width = compute_width_at_position_mm(
            spec.nut_width_mm,
            spec.heel_width_mm,
            treble_scale_mm,  # Use treble scale as reference
            spec.fret_count,
            avg_x,
        )

        # Radius-blended depth
        depth = compute_radius_blended_depth_fn(
            spec.base_radius_mm,
            spec.end_radius_mm,
            avg_x,
            treble_scale_mm,
            slot_depth_mm,
        )

        # Bass and treble endpoints
        half_width = width / 2.0
        bass_pt = (fret_point.bass_pos_mm, fret_point.center_y + half_width)
        treble_pt = (fret_point.treble_pos_mm, fret_point.center_y - half_width)

        toolpath = FretSlotToolpath_cls(
            fret_number=fret_point.fret_number,
            position_mm=avg_x,
            width_mm=width,
            bass_point=bass_pt,
            treble_point=treble_pt,
            slot_depth_mm=depth,
            slot_width_mm=slot_width_mm,
            feed_rate_mmpm=base_feed_mmpm,
            plunge_rate_mmpm=base_plunge_mmpm,
            angle_rad=fret_point.angle_rad,
        )
        toolpaths.append(toolpath)

    return toolpaths


def export_fan_fret_dxf_r12(toolpaths: List["FretSlotToolpath"]) -> str:
    """Export fan-fret toolpaths as DXF R12 with FRET_SLOTS_FAN layer."""
    lines = [
        "0", "SECTION",
        "2", "HEADER",
        "9", "$ACADVER",
        "1", "AC1009",        # DXF R12
        "9", "$INSUNITS",
        "70", "4",            # Millimeters
        "0", "ENDSEC",
        "0", "SECTION",
        "2", "TABLES",
        "0", "TABLE",
        "2", "LAYER",
        "70", "1",
        "0", "LAYER",
        "2", "FRET_SLOTS_FAN",
        "70", "0",
        "62", "7",            # White color
        "0", "ENDTAB",
        "0", "ENDSEC",
        "0", "SECTION",
        "2", "ENTITIES",
    ]

    for tp in toolpaths:
        angle_deg = tp.angle_rad * 180.0 / pi
        color = "4" if tp.is_perpendicular else "7"

        lines.extend([
            "0", "LINE",
            "8", "FRET_SLOTS_FAN",
            "62", color,
            "10", f"{tp.bass_point[0]:.4f}",
            "20", f"{tp.bass_point[1]:.4f}",
            "30", "0.0",
            "11", f"{tp.treble_point[0]:.4f}",
            "21", f"{tp.treble_point[1]:.4f}",
            "31", "0.0",
            "999", f"FRET_{tp.fret_number}_ANGLE_{angle_deg:.2f}deg",
        ])

    lines.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(lines)
