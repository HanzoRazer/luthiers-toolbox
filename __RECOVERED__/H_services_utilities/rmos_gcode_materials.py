"""
RMOS G-code Emission with CAM Profiles (MM-2)

Reference implementation for emitting G-code with per-material CAM settings.
This is a helper module that can be integrated into existing G-code emitters.
"""
from __future__ import annotations

from typing import Dict, Any, List

from ..schemas.strip_family import MaterialSpec
from .rmos_cam_materials import build_segment_cam_params


def emit_rosette_gcode_with_materials(
    plan: dict,
    strip_family: dict,
    machine_defaults: Dict[str, Any]
) -> str:
    """
    Emit G-code for rosette with per-material CAM settings.
    
    Args:
        plan: Geometry plan with segments (arcs, lines, etc.)
        strip_family: Mixed-material strip family from MM-0
        machine_defaults: Base machine parameters
    
    Returns:
        G-code string with material-aware feeds/speeds
    
    Example plan structure:
        {
            "segments": [
                {
                    "type": "line",
                    "x1": 0, "y1": 0, "x2": 10, "y2": 0,
                    "material_index": 0
                },
                {
                    "type": "arc",
                    "x1": 10, "y1": 0, "x2": 10, "y2": 10,
                    "cx": 10, "cy": 5, "r": 5,
                    "material_index": 1
                }
            ]
        }
    """
    materials = strip_family.get("materials") or []
    materials_specs: List[MaterialSpec] = [MaterialSpec(**m) for m in materials]

    segments = plan.get("segments") or []
    gcode_lines: List[str] = []

    # Header
    gcode_lines.append("(RMOS Rosette with MM-2 CAM Profiles)")
    gcode_lines.append("G21 (mm)")
    gcode_lines.append("G90 (absolute)")
    gcode_lines.append("")

    for seg_idx, seg in enumerate(segments):
        # Get material for this segment
        mat_index = seg.get("material_index", 0)
        if 0 <= mat_index < len(materials_specs):
            mat_spec = materials_specs[mat_index]
        else:
            # Fallback to first material
            mat_spec = materials_specs[0] if materials_specs else MaterialSpec(
                key="default",
                type="wood"  # type: ignore[arg-type]
            )

        # Get CAM parameters for this material
        cam_params = build_segment_cam_params(mat_spec, machine_defaults)

        # Emit segment with material-specific settings
        gcode_lines.append(f"(Segment {seg_idx}: {mat_spec.species or mat_spec.type})")
        gcode_lines.extend(emit_segment_with_params(seg, cam_params))
        gcode_lines.append("")

    # Footer
    gcode_lines.append("M30 (End)")
    
    return "\n".join(gcode_lines)


def emit_segment_with_params(segment: dict, params: Dict[str, Any]) -> List[str]:
    """
    Emit G-code for a segment using CAM parameters.
    
    Args:
        segment: Geometry segment (line, arc, etc.)
        params: CAM parameters from build_segment_cam_params
    
    Returns:
        List of G-code lines
    
    This is a reference stub - integrate with your actual G-code emitter.
    """
    lines: List[str] = []

    # Add CAM profile metadata as comments
    profile_id = params.get("cam_profile_id", "unknown")
    fragility = params.get("fragility_score", 0.0)
    lines.append(f"(CAM: {profile_id}, Fragility: {fragility:.2f})")

    # Set spindle speed if specified
    spindle_rpm = params.get("spindle_rpm")
    if spindle_rpm and spindle_rpm > 0:
        lines.append(f"M3 S{spindle_rpm} (Spindle on)")

    # Set feed rate
    feed_rate = params.get("feed_rate_mm_min", 1000)
    
    # Emit geometry based on type
    seg_type = segment.get("type")
    
    if seg_type == "line":
        x2 = segment.get("x2", 0)
        y2 = segment.get("y2", 0)
        lines.append(f"G1 X{x2:.4f} Y{y2:.4f} F{feed_rate}")
    
    elif seg_type == "arc":
        x2 = segment.get("x2", 0)
        y2 = segment.get("y2", 0)
        cx = segment.get("cx", 0)
        cy = segment.get("cy", 0)
        x1 = segment.get("x1", 0)
        y1 = segment.get("y1", 0)
        
        # Calculate I and J offsets
        i = cx - x1
        j = cy - y1
        
        # Determine arc direction (G2 CW or G3 CCW)
        # For now, use G3 (CCW) as default
        lines.append(f"G3 X{x2:.4f} Y{y2:.4f} I{i:.4f} J{j:.4f} F{feed_rate}")
    
    else:
        lines.append(f"(Unknown segment type: {seg_type})")

    # Add notes if present
    notes = params.get("notes")
    if notes:
        lines.append(f"({notes})")

    return lines


def get_cam_summary_for_job(strip_family: dict) -> Dict[str, Any]:
    """
    Get CAM summary for a strip family (used in job metadata).
    
    Args:
        strip_family: Strip family dict with materials
    
    Returns:
        Summary dict with profile_ids, feed rates, fragility, lane hint
    """
    from .cam_profile_registry import summarize_profiles_for_family
    return summarize_profiles_for_family(strip_family)
