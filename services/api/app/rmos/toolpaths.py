"""
RMOS Toolpaths Module - Canonical Toolpath Generation

Provides server-side toolpath generation wired to:
- Rosette CAM engine (cam/rosette/cnc/)
- Saw Lab toolpath builder (saw_lab/)

Registry Declaration:
    impl="app.rmos.toolpaths:generate_toolpaths_server_side"

Governance:
- All toolpath generation requires authoritative feasibility
- Outputs include hashes for audit trail
- Post-processors are selected by machine profile
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _sha256(data: Any) -> str:
    """Compute SHA256 hash of data."""
    if isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload = data
    else:
        payload = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def generate_toolpaths_server_side(
    *,
    mode: str,
    design: Dict[str, Any],
    context: Dict[str, Any],
    feasibility: Dict[str, Any],
    post_processor_id: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Canonical server-side toolpath generation.
    
    This is the function registered in the engine registry as:
        impl="app.rmos.toolpaths:generate_toolpaths_server_side"
    
    Args:
        mode: Operation mode ("saw", "rosette", "vcarve", etc.)
        design: Design parameters (rosette spec, saw cut spec, etc.)
        context: Machine context (tool_id, material_id, machine_id)
        feasibility: Server-computed feasibility (REQUIRED)
        post_processor_id: Optional post-processor ("grbl_post_v2", "fanuc_post_v1")
        options: Additional generation options
    
    Returns:
        Dict with:
            - toolpaths: Toolpath geometry data
            - gcode_text: Generated G-code (if post-processor applied)
            - opplan: Operation plan summary
            - hashes: SHA256 hashes of all outputs
            - meta: Generation metadata
    
    Raises:
        ValueError: If mode is unsupported or feasibility missing
    """
    if not feasibility:
        raise ValueError("Authoritative feasibility is required per governance contract")
    
    options = options or {}
    
    logger.info(
        "toolpaths.generate_server_side",
        extra={
            "mode": mode,
            "post_processor_id": post_processor_id,
            "has_feasibility": bool(feasibility),
        }
    )
    
    # Dispatch to mode-specific generator
    if mode == "saw":
        result = _generate_saw_toolpaths(design, context, feasibility, options)
    elif mode == "rosette":
        result = _generate_rosette_toolpaths(design, context, feasibility, options)
    elif mode == "vcarve":
        result = _generate_vcarve_toolpaths(design, context, feasibility, options)
    else:
        raise ValueError(f"Unsupported mode: {mode}")
    
    # Apply post-processor if specified
    if post_processor_id and result.get("toolpaths"):
        result = _apply_post_processor(result, post_processor_id, context)
    
    # Compute hashes for audit
    result["hashes"] = {
        "toolpaths_sha256": _sha256(result.get("toolpaths", {})),
        "gcode_sha256": _sha256(result.get("gcode_text", "")) if result.get("gcode_text") else None,
        "opplan_sha256": _sha256(result.get("opplan", {})),
    }
    
    result["meta"] = {
        "mode": mode,
        "post_processor_id": post_processor_id,
        "generator_version": "1.0.0",
    }
    
    return result


def _generate_saw_toolpaths(
    design: Dict[str, Any],
    context: Dict[str, Any],
    feasibility: Dict[str, Any],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate saw toolpaths using saw_lab module."""
    try:
        from ..saw_lab.toolpath_builder import SawToolpathBuilder
        from ..saw_lab.models import SawContext
        
        # Build saw context from params
        saw_ctx = SawContext(
            kerf_width_mm=design.get("kerf_width_mm", 2.0),
            stock_thickness_mm=design.get("stock_thickness_mm", 10.0),
            feed_rate_mm_per_min=context.get("feed_rate", 500.0),
            max_rpm=context.get("spindle_rpm", 3000),
        )
        
        # Build segments from design
        segments = _design_to_saw_segments(design)
        
        builder = SawToolpathBuilder()
        plan = builder.build(segments, saw_ctx)
        
        # Convert plan to output format
        gcode_lines = []
        for move in plan.moves:
            line = move.code
            if move.x is not None:
                line += f" X{move.x}"
            if move.y is not None:
                line += f" Y{move.y}"
            if move.z is not None:
                line += f" Z{move.z}"
            if move.f is not None:
                line += f" F{move.f}"
            if move.comment:
                line += f" ; {move.comment}"
            gcode_lines.append(line)
        
        return {
            "mode": "saw",
            "toolpaths": {
                "moves": [m.model_dump() if hasattr(m, 'model_dump') else asdict(m) for m in plan.moves],
                "total_length_mm": plan.total_length_mm,
                "cut_count": plan.cut_count,
            },
            "gcode_text": "\n".join(gcode_lines),
            "opplan": {
                "kind": "saw",
                "estimated_time_seconds": plan.estimated_time_seconds,
                "material_removed_mm3": plan.material_removed_mm3,
                "warnings": plan.warnings,
            },
        }
    except ImportError as e:
        logger.warning(f"saw_lab import failed, using fallback: {e}")
        return _fallback_saw_toolpaths(design, context)


def _design_to_saw_segments(design: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert design spec to saw cut segments."""
    segments = []
    
    # Extract cuts from design
    cuts = design.get("cuts", [])
    if not cuts:
        # Generate default cut pattern
        num_cuts = design.get("num_cuts", 1)
        spacing = design.get("spacing_mm", 5.0)
        depth = design.get("depth_mm", -5.0)
        length = design.get("length_mm", 50.0)
        
        for i in range(num_cuts):
            x_pos = i * spacing
            segments.append({
                "type": "rapid",
                "start": {"x": x_pos, "y": 0, "z": 5},
                "end": {"x": x_pos, "y": 0, "z": 5},
                "comment": f"Position for cut {i+1}",
            })
            segments.append({
                "type": "plunge",
                "start": {"x": x_pos, "y": 0, "z": 5},
                "end": {"x": x_pos, "y": 0, "z": depth},
                "comment": f"Plunge cut {i+1}",
            })
            segments.append({
                "type": "cut",
                "start": {"x": x_pos, "y": 0, "z": depth},
                "end": {"x": x_pos, "y": length, "z": depth},
                "comment": f"Cut {i+1}",
            })
            segments.append({
                "type": "retract",
                "start": {"x": x_pos, "y": length, "z": depth},
                "end": {"x": x_pos, "y": length, "z": 5},
                "comment": f"Retract from cut {i+1}",
            })
    else:
        segments = cuts
    
    return segments


def _fallback_saw_toolpaths(
    design: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Fallback saw toolpath generator when saw_lab unavailable."""
    gcode = """G21 ; mm
G90 ; absolute
G0 Z5.0
; SAW TOOLPATH (FALLBACK)
G0 X0 Y0
G1 Z-5.0 F500
G1 Y50.0 F500
G0 Z5.0
M30
"""
    return {
        "mode": "saw",
        "toolpaths": {"fallback": True},
        "gcode_text": gcode,
        "opplan": {"kind": "saw", "fallback": True},
    }


def _generate_rosette_toolpaths(
    design: Dict[str, Any],
    context: Dict[str, Any],
    feasibility: Dict[str, Any],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate rosette toolpaths using cam/rosette/cnc module."""
    try:
        from ..cam.rosette.cnc.cnc_toolpath import build_linear_toolpaths, ToolpathPlan
        from ..cam.rosette.cnc.cnc_gcode_exporter import (
            generate_gcode_from_toolpaths,
            GCodePostConfig,
            MachineProfile,
        )
        
        # Extract parameters
        ring_id = design.get("ring_id", 1)
        slices = design.get("slices", [{"slice_index": i} for i in range(8)])
        feed_rate = context.get("feed_rate", 1000.0)
        origin_x = design.get("origin_x_mm", 0.0)
        origin_y = design.get("origin_y_mm", 0.0)
        z_depth = design.get("z_depth_mm", -1.0)
        
        # Build toolpaths
        plan = build_linear_toolpaths(
            ring_id=ring_id,
            slices=slices,
            feed_mm_per_min=feed_rate,
            origin_x_mm=origin_x,
            origin_y_mm=origin_y,
            z_depth_mm=z_depth,
        )
        
        # Determine profile from context
        machine_profile = context.get("machine_profile", "grbl")
        if machine_profile.lower() == "fanuc":
            profile = MachineProfile.FANUC
        else:
            profile = MachineProfile.GRBL
        
        # Generate G-code
        post_config = GCodePostConfig(
            profile=profile,
            safe_z_mm=options.get("safe_z_mm", 5.0),
            spindle_rpm=context.get("spindle_rpm", 12000),
            tool_id=context.get("tool_number", 1),
        )
        
        gcode = generate_gcode_from_toolpaths(plan, post_config)
        
        # Convert segments to serializable format
        segments_data = [
            {
                "x_start_mm": s.x_start_mm,
                "y_start_mm": s.y_start_mm,
                "z_start_mm": s.z_start_mm,
                "x_end_mm": s.x_end_mm,
                "y_end_mm": s.y_end_mm,
                "z_end_mm": s.z_end_mm,
                "feed_mm_per_min": s.feed_mm_per_min,
            }
            for s in plan.segments
        ]
        
        return {
            "mode": "rosette",
            "toolpaths": {
                "ring_id": plan.ring_id,
                "segments": segments_data,
                "segment_count": len(segments_data),
            },
            "gcode_text": gcode,
            "opplan": {
                "kind": "rosette",
                "ring_id": ring_id,
                "slice_count": len(slices),
                "profile": machine_profile,
            },
        }
    except ImportError as e:
        logger.warning(f"cam.rosette.cnc import failed, using fallback: {e}")
        return _fallback_rosette_toolpaths(design, context)


def _fallback_rosette_toolpaths(
    design: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Fallback rosette toolpath generator."""
    gcode = """G21 ; mm
G90 ; absolute
G0 Z5.0
; ROSETTE TOOLPATH (FALLBACK)
G0 X0 Y0
G1 Z-1.0 F1000
G1 X10.0 Y10.0 F1000
G0 Z5.0
M30
"""
    return {
        "mode": "rosette",
        "toolpaths": {"fallback": True},
        "gcode_text": gcode,
        "opplan": {"kind": "rosette", "fallback": True},
    }


def _generate_vcarve_toolpaths(
    design: Dict[str, Any],
    context: Dict[str, Any],
    feasibility: Dict[str, Any],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate V-carve toolpaths."""
    try:
        from ..toolpath.vcarve_toolpath import generate_vcarve_path
        
        # Extract parameters
        geometry = design.get("geometry", [])
        v_angle = design.get("v_angle_deg", 60.0)
        max_depth = design.get("max_depth_mm", 3.0)
        feed_rate = context.get("feed_rate", 800.0)
        
        paths = generate_vcarve_path(
            geometry=geometry,
            v_angle=v_angle,
            max_depth=max_depth,
            feed_rate=feed_rate,
        )
        
        return {
            "mode": "vcarve",
            "toolpaths": paths,
            "gcode_text": paths.get("gcode", ""),
            "opplan": {"kind": "vcarve", "path_count": len(paths.get("segments", []))},
        }
    except ImportError as e:
        logger.warning(f"vcarve_toolpath import failed: {e}")
        return {
            "mode": "vcarve",
            "toolpaths": {"fallback": True},
            "gcode_text": "; V-CARVE FALLBACK\nM30\n",
            "opplan": {"kind": "vcarve", "fallback": True},
        }


def _apply_post_processor(
    result: Dict[str, Any],
    post_processor_id: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Apply post-processor to regenerate G-code."""
    try:
        if post_processor_id == "grbl_post_v2":
            from .posts.grbl import render
        elif post_processor_id == "fanuc_post_v1":
            from .posts.fanuc import render
        else:
            logger.warning(f"Unknown post-processor: {post_processor_id}")
            return result
        
        gcode = render(
            toolpaths=result.get("toolpaths", {}),
            context=context,
        )
        result["gcode_text"] = gcode
        result["meta"]["post_processor_applied"] = post_processor_id
        
    except ImportError as e:
        logger.warning(f"Post-processor {post_processor_id} import failed: {e}")
    
    return result


# =============================================================================
# Convenience functions for direct import
# =============================================================================

def generate_saw_toolpaths(
    design: Dict[str, Any],
    context: Dict[str, Any],
    feasibility: Dict[str, Any],
) -> Dict[str, Any]:
    """Direct saw toolpath generation."""
    return generate_toolpaths_server_side(
        mode="saw",
        design=design,
        context=context,
        feasibility=feasibility,
    )


def generate_rosette_toolpaths(
    design: Dict[str, Any],
    context: Dict[str, Any],
    feasibility: Dict[str, Any],
) -> Dict[str, Any]:
    """Direct rosette toolpath generation."""
    return generate_toolpaths_server_side(
        mode="rosette",
        design=design,
        context=context,
        feasibility=feasibility,
    )
