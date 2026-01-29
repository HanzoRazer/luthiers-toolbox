"""
Smart Guitar Geometry Resolver (SG-SBX-0.1)
===========================================

Resolves CAM plan template IDs to actual DXF geometry and positions
them on the Les Paul body outline for G-code generation.

Usage:
    from app.sandboxes.smart_guitar.geometry_resolver import resolve_geometry

    plan = generate_plan(spec)
    geometry = resolve_geometry(plan, base_model="les_paul")
"""

from __future__ import annotations

import ezdxf
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from .templates import get_template_path, get_template_info, SMART_GUITAR_TEMPLATES
from .schemas import SmartCamPlan, CavityPlan, ChannelPlan


@dataclass
class ResolvedGeometry:
    """Resolved geometry with positioned templates."""

    # Base body outline
    body_outline: List[Tuple[float, float]]
    body_width_mm: float
    body_height_mm: float

    # Positioned cavity geometries (template_id -> positioned points)
    cavities: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Metadata
    base_model: str = "les_paul"
    handedness: str = "RH"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "base_model": self.base_model,
            "handedness": self.handedness,
            "body": {
                "width_mm": self.body_width_mm,
                "height_mm": self.body_height_mm,
                "point_count": len(self.body_outline),
            },
            "cavities": self.cavities,
        }


def load_dxf_geometry(template_id: str) -> List[Tuple[float, float]]:
    """
    Load geometry points from a DXF template.

    Args:
        template_id: Template identifier (e.g., "pod_rh_v1")

    Returns:
        List of (x, y) coordinate tuples
    """
    dxf_path = get_template_path(template_id)
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    points = []
    for entity in msp:
        if entity.dxftype() == "LWPOLYLINE":
            points = [(p[0], p[1]) for p in entity.get_points()]
            break

    return points


def get_les_paul_body_outline() -> Tuple[List[Tuple[float, float]], float, float]:
    """
    Get Les Paul body outline from instrument_geometry.

    Returns:
        (points, width_mm, height_mm)
    """
    try:
        # Try to load from body/outlines.py - BODY_OUTLINES dict
        from app.instrument_geometry.body.outlines import BODY_OUTLINES

        if "les_paul" in BODY_OUTLINES:
            outline = BODY_OUTLINES["les_paul"]
            xs = [p[0] for p in outline]
            ys = [p[1] for p in outline]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)
            return list(outline), width, height
    except (ImportError, KeyError):
        pass

    try:
        # Try to load from body/detailed_outlines.py
        from app.instrument_geometry.body.detailed_outlines import DETAILED_BODY_OUTLINES

        if "les_paul" in DETAILED_BODY_OUTLINES:
            outline = DETAILED_BODY_OUTLINES["les_paul"]
            xs = [p[0] for p in outline]
            ys = [p[1] for p in outline]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)
            return list(outline), width, height
    except (ImportError, KeyError):
        pass

    # Fallback: use catalog.json dimensions
    # Body: 383.5mm x 269.2mm from catalog (669 points in original)
    # Return a simplified Les Paul-style outline
    w, h = 383.5, 269.2
    # Simplified single-cutaway shape
    return [
        (0, h * 0.3),           # Left waist
        (0, h * 0.9),           # Left lower bout
        (w * 0.1, h),           # Bottom left corner
        (w * 0.9, h),           # Bottom right corner
        (w, h * 0.9),           # Right lower bout
        (w, h * 0.3),           # Right waist
        (w, h * 0.15),          # Right upper bout
        (w * 0.7, 0),           # Cutaway end
        (w * 0.5, h * 0.05),    # Cutaway curve
        (w * 0.4, h * 0.1),     # Neck heel
        (w * 0.35, 0),          # Neck
        (w * 0.15, 0),          # Headstock transition
        (0, h * 0.15),          # Left upper bout
    ], w, h


def position_cavity(
    points: List[Tuple[float, float]],
    zone: str,
    body_width: float,
    body_height: float,
    handedness: str = "RH",
) -> List[Tuple[float, float]]:
    """
    Position cavity geometry within the body based on zone.

    Args:
        points: Template geometry points (centered at origin)
        zone: Position zone (bass_side, treble_side, upper_bout, etc.)
        body_width: Body width in mm
        body_height: Body height in mm
        handedness: RH or LH

    Returns:
        Positioned points
    """
    # Calculate template bounds
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    template_w = max(xs) - min(xs)
    template_h = max(ys) - min(ys)

    # Zone positioning offsets (relative to body center)
    # Les Paul body: ~383mm wide, ~269mm tall (or ~330x440 nominal)
    center_x = body_width / 2
    center_y = body_height / 2

    # Spine width: ~38mm, so cavities start ~20mm from center
    spine_offset = 20

    zone_positions = {
        # Hollow chambers - back surface
        "bass_side": (center_x - spine_offset - template_w/2 - 30, center_y - 20),
        "treble_side": (center_x + spine_offset + template_w/2 + 30, center_y - 20),
        "tail_wing": (center_x, body_height - template_h/2 - 30),

        # Electronics pod - upper bout
        "upper_bout_treble": (center_x + 60, 80),
        "upper_bout_bass": (center_x - 60, 80),

        # Pickups - top surface, centered on scale
        "neck_position": (center_x, center_y - 40),
        "bridge_position": (center_x, center_y + 80),

        # Control cavity - lower bout
        "lower_bout_treble": (body_width - template_w/2 - 25, body_height - 60),
        "lower_bout_bass": (template_w/2 + 25, body_height - 60),
    }

    # Flip for left-handed if needed
    if handedness == "LH":
        # Mirror across center X
        zone_positions = {
            k: (body_width - v[0], v[1])
            for k, v in zone_positions.items()
        }

    # Get position for this zone (default to center)
    offset_x, offset_y = zone_positions.get(zone, (center_x, center_y))

    # Translate points
    return [(p[0] + offset_x, p[1] + offset_y) for p in points]


def resolve_geometry(
    plan: SmartCamPlan,
    base_model: str = "les_paul",
) -> ResolvedGeometry:
    """
    Resolve all template IDs in a CAM plan to positioned geometry.

    Args:
        plan: The CAM plan with template_ids
        base_model: Base guitar model for body outline

    Returns:
        ResolvedGeometry with all positioned templates
    """
    # Get body outline
    body_outline, body_width, body_height = get_les_paul_body_outline()

    # Zone mapping for cavity kinds
    cavity_zones = {
        "bass_main": "bass_side",
        "treble_main": "treble_side",
        "tail_wing": "tail_wing",
        "pod": "upper_bout_treble",
    }

    # Resolve cavities
    cavities = {}
    for cavity in plan.cavities:
        template_id = cavity.template_id

        if template_id not in SMART_GUITAR_TEMPLATES:
            # Skip if template doesn't exist
            cavities[template_id] = {
                "status": "missing_template",
                "kind": cavity.kind.value,
                "depth_in": cavity.depth_in,
            }
            continue

        # Load template geometry
        points = load_dxf_geometry(template_id)
        template_info = get_template_info(template_id)

        # Get zone for positioning
        zone = cavity_zones.get(cavity.kind.value, "center")

        # Position the cavity
        positioned = position_cavity(
            points, zone, body_width, body_height, plan.handedness.value
        )

        cavities[template_id] = {
            "status": "resolved",
            "kind": cavity.kind.value,
            "depth_in": cavity.depth_in,
            "depth_mm": cavity.depth_in * 25.4,
            "template_info": template_info,
            "geometry": {
                "points": positioned,
                "point_count": len(positioned),
                "bounds": {
                    "x_min": min(p[0] for p in positioned),
                    "x_max": max(p[0] for p in positioned),
                    "y_min": min(p[1] for p in positioned),
                    "y_max": max(p[1] for p in positioned),
                },
            },
        }

    # Resolve channels
    for channel in plan.channels:
        template_id = channel.template_id

        if template_id not in SMART_GUITAR_TEMPLATES:
            cavities[template_id] = {
                "status": "missing_template",
                "kind": channel.kind.value,
            }
            continue

        points = load_dxf_geometry(template_id)
        template_info = get_template_info(template_id)

        # Channels are positioned along routing paths (simplified for now)
        cavities[template_id] = {
            "status": "resolved",
            "kind": channel.kind.value,
            "template_info": template_info,
            "geometry": {
                "points": points,  # Not positioned yet - needs routing path
                "point_count": len(points),
            },
            "notes": channel.notes,
        }

    return ResolvedGeometry(
        body_outline=body_outline,
        body_width_mm=body_width,
        body_height_mm=body_height,
        cavities=cavities,
        base_model=base_model,
        handedness=plan.handedness.value,
    )


def generate_combined_dxf(
    geometry: ResolvedGeometry,
    output_path: Path,
) -> Path:
    """
    Generate a combined DXF file with body outline and all cavities.

    Args:
        geometry: Resolved geometry from resolve_geometry()
        output_path: Output DXF file path

    Returns:
        Path to generated DXF file
    """
    doc = ezdxf.new(dxfversion="R2000")
    msp = doc.modelspace()

    # Add layers
    doc.layers.add("BODY_OUTLINE", color=7)
    doc.layers.add("CAVITY_BACK", color=1)  # Red
    doc.layers.add("CAVITY_TOP", color=3)   # Green
    doc.layers.add("CHANNELS", color=5)     # Blue

    # Add body outline
    if geometry.body_outline:
        msp.add_lwpolyline(
            geometry.body_outline,
            close=True,
            dxfattribs={"layer": "BODY_OUTLINE"}
        )

    # Add cavities
    for template_id, cavity_data in geometry.cavities.items():
        if cavity_data.get("status") != "resolved":
            continue

        points = cavity_data.get("geometry", {}).get("points", [])
        if not points:
            continue

        kind = cavity_data.get("kind", "")

        # Determine layer based on kind
        if kind in ("bass_main", "treble_main", "tail_wing", "pod", "route", "drill"):
            layer = "CAVITY_BACK"
        elif kind in ("pickup",):
            layer = "CAVITY_TOP"
        else:
            layer = "CHANNELS"

        msp.add_lwpolyline(
            points,
            close=True,
            dxfattribs={"layer": layer}
        )

    doc.saveas(output_path)
    return output_path
