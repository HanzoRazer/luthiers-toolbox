#!/usr/bin/env python3
"""Acoustic Body Outline & G-code Generator

GEN-6: Orchestrates acoustic guitar body CAM operations including:
- Body perimeter outline
- Soundhole routing
- Binding channel routing
- Bracing pocket references

Supports styles: dreadnought, jumbo, OM, OO, 000, parlor, classical
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum

# Import body outline data
from ..instrument_geometry.body.outlines import (
    get_body_outline,
    get_body_dimensions,
    get_body_metadata,
    list_bodies_by_category,
)

# Import acoustic specs for reference dimensions
from ..calculators.acoustic_body_volume import (
    REFERENCE_MODELS,
    GuitarBodySpecs,
    calculate_body_volume,
    calculate_helmholtz_frequency,
)


class AcousticBodyStyle(str, Enum):
    """Supported acoustic guitar body styles."""
    DREADNOUGHT = "dreadnought"
    JUMBO = "jumbo"
    OM = "om_000"  # Orchestra Model / 000
    OO = "oo"       # Double-O (Martin 00 style)
    PARLOR = "parlor"
    CLASSICAL = "classical"
    J45 = "j45"     # Gibson J-45
    GIBSON_L00 = "gibson_l_00"


# Map styles to reference model specs (for dimensions not in outline)
STYLE_TO_REFERENCE = {
    AcousticBodyStyle.DREADNOUGHT: "martin_d28",
    AcousticBodyStyle.JUMBO: "generic_dreadnought",  # Scale up
    AcousticBodyStyle.OM: "martin_om28",
    AcousticBodyStyle.OO: "martin_00",
    AcousticBodyStyle.CLASSICAL: "martin_000",  # Similar size
    AcousticBodyStyle.J45: "martin_d28",  # Similar to dreadnought
    AcousticBodyStyle.GIBSON_L00: "martin_00",
}

# Fallback outline sources for styles with stub outlines
# Maps style -> outline_id to use, with optional scale factor
OUTLINE_FALLBACKS = {
    AcousticBodyStyle.OO: ("om_000", 0.943),  # OO is ~94.3% of 000 size (362/384)
    AcousticBodyStyle.PARLOR: ("gibson_l_00", 0.9),  # Parlor is smaller than L-00
}


@dataclass
class AcousticBodyResult:
    """Result of acoustic body outline generation."""

    style: str
    width_mm: float
    length_mm: float
    points: List[Tuple[float, float]]
    point_count: int
    centroid: Tuple[float, float]
    bounding_box: Dict[str, float]
    scale_factor: float = 1.0
    soundhole_center: Optional[Tuple[float, float]] = None
    soundhole_diameter_mm: float = 101.6  # 4" default
    depth_endblock_mm: float = 124.0
    depth_neck_mm: float = 105.0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "style": self.style,
            "width_mm": round(self.width_mm, 2),
            "length_mm": round(self.length_mm, 2),
            "point_count": self.point_count,
            "centroid": {"x": round(self.centroid[0], 2), "y": round(self.centroid[1], 2)},
            "bounding_box": {k: round(v, 2) for k, v in self.bounding_box.items()},
            "scale_factor": self.scale_factor,
            "soundhole": {
                "center": {"x": round(self.soundhole_center[0], 2), "y": round(self.soundhole_center[1], 2)} if self.soundhole_center else None,
                "diameter_mm": self.soundhole_diameter_mm,
            },
            "depth": {
                "endblock_mm": self.depth_endblock_mm,
                "neck_mm": self.depth_neck_mm,
            },
            "notes": self.notes,
            "points": [(round(x, 3), round(y, 3)) for x, y in self.points],
        }

    def to_svg(self,
               stroke_color: str = "#8B4513",  # Saddle brown for acoustic
               stroke_width: float = 0.5,
               fill: str = "none",
               include_soundhole: bool = True,
               include_centerline: bool = False) -> str:
        """Generate SVG representation of the acoustic body outline."""
        if not self.points:
            return ""

        # SVG viewBox with padding
        padding = 15
        min_x = self.bounding_box["min_x"] - padding
        min_y = self.bounding_box["min_y"] - padding
        width = self.width_mm + 2 * padding
        height = self.length_mm + 2 * padding

        # Build path data for body outline
        path_data = f"M {self.points[0][0]},{self.points[0][1]}"
        for x, y in self.points[1:]:
            path_data += f" L {x},{y}"
        path_data += " Z"

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {width} {height}" width="{width}mm" height="{height}mm">',
            f'  <path d="{path_data}" stroke="{stroke_color}" stroke-width="{stroke_width}" fill="{fill}" />',
        ]

        # Add soundhole if requested
        if include_soundhole and self.soundhole_center:
            cx, cy = self.soundhole_center
            r = self.soundhole_diameter_mm / 2
            svg_parts.append(
                f'  <circle cx="{cx}" cy="{cy}" r="{r}" stroke="{stroke_color}" stroke-width="{stroke_width}" fill="none" />'
            )

        # Add centerline if requested
        if include_centerline:
            cx = self.centroid[0]
            svg_parts.append(
                f'  <line x1="{cx}" y1="{min_y + padding}" x2="{cx}" y2="{min_y + height - padding}" '
                f'stroke="#999999" stroke-width="0.25" stroke-dasharray="2,2" />'
            )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)


@dataclass
class AcousticBodyGenerator:
    """
    Factory for generating acoustic guitar body outlines and G-code.

    Usage:
        generator = AcousticBodyGenerator.from_style("dreadnought")
        result = generator.generate_outline()
        gcode = generator.generate_perimeter_gcode(tool_diameter=6.35, stepdown=3.0)
    """

    style: AcousticBodyStyle
    scale: float = 1.0
    soundhole_diameter_mm: float = 101.6  # 4" default
    soundhole_offset_from_neck_mm: float = 80.0  # Distance from neck joint to soundhole center

    # Machine settings (mm)
    safe_z: float = 10.0
    rapid_z: float = 3.0
    feed_xy: float = 1500.0  # mm/min
    feed_z: float = 500.0    # mm/min plunge
    spindle_rpm: int = 18000

    @classmethod
    def from_style(cls, style: str | AcousticBodyStyle, **kwargs) -> "AcousticBodyGenerator":
        """Create generator from style name."""
        if isinstance(style, str):
            style_lower = style.lower().replace("-", "_").replace(" ", "_")
            # Handle aliases
            if style_lower in ("om", "000", "triple_o"):
                style_enum = AcousticBodyStyle.OM
            elif style_lower in ("oo", "00", "double_o"):
                style_enum = AcousticBodyStyle.OO
            else:
                try:
                    style_enum = AcousticBodyStyle(style_lower)
                except ValueError:
                    # Try matching by key
                    for s in AcousticBodyStyle:
                        if style_lower in s.value:
                            style_enum = s
                            break
                    else:
                        raise ValueError(f"Unknown acoustic style: {style}. Available: {[s.value for s in AcousticBodyStyle]}")
        else:
            style_enum = style

        return cls(style=style_enum, **kwargs)

    @classmethod
    def from_project(cls, project: Dict[str, Any]) -> "AcousticBodyGenerator":
        """
        Create generator from project configuration.

        Expected project structure:
        {
            "body_style": "dreadnought" | "om" | "oo" | etc.,
            "scale": 1.0,
            "soundhole_diameter_mm": 101.6,
            "machine": {
                "safe_z": 10.0,
                "feed_xy": 1500.0,
                "feed_z": 500.0,
                "spindle_rpm": 18000
            }
        }
        """
        style = project.get("body_style", "dreadnought")

        machine = project.get("machine", {})

        return cls.from_style(
            style,
            scale=project.get("scale", 1.0),
            soundhole_diameter_mm=project.get("soundhole_diameter_mm", 101.6),
            safe_z=machine.get("safe_z", 10.0),
            feed_xy=machine.get("feed_xy", 1500.0),
            feed_z=machine.get("feed_z", 500.0),
            spindle_rpm=machine.get("spindle_rpm", 18000),
        )

    def _get_reference_specs(self) -> Optional[GuitarBodySpecs]:
        """Get reference specs for this style."""
        ref_key = STYLE_TO_REFERENCE.get(self.style)
        if ref_key and ref_key in REFERENCE_MODELS:
            return REFERENCE_MODELS[ref_key]
        return None

    def generate_outline(self) -> AcousticBodyResult:
        """Generate acoustic body outline."""
        style_str = self.style.value
        fallback_note = None

        # Get outline points
        points = get_body_outline(style_str, scale=self.scale, detailed=True)

        # Check if outline is a stub (less than 10 points) and use fallback
        if len(points) < 10 and self.style in OUTLINE_FALLBACKS:
            fallback_id, fallback_scale = OUTLINE_FALLBACKS[self.style]
            fallback_points = get_body_outline(fallback_id, scale=self.scale * fallback_scale, detailed=True)
            if len(fallback_points) >= 10:
                points = fallback_points
                fallback_note = f"Using {fallback_id} outline scaled to {fallback_scale * 100:.1f}%"

        # Get dimensions
        dims = get_body_dimensions(style_str)

        # Calculate bounding box from points
        if points:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            bbox = {
                "min_x": min(xs),
                "max_x": max(xs),
                "min_y": min(ys),
                "max_y": max(ys),
            }
            centroid = (sum(xs) / len(xs), sum(ys) / len(ys))
        else:
            bbox = {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}
            centroid = (0.0, 0.0)

        # Get reference specs for depth and soundhole
        ref_specs = self._get_reference_specs()
        depth_end = ref_specs.depth_endblock_mm if ref_specs else 124.0
        depth_neck = ref_specs.depth_neck_mm if ref_specs else 105.0

        # Calculate soundhole center (relative to body)
        # Typically positioned in upper bout region, on centerline
        if points:
            # Soundhole is typically 1/3 from neck end
            soundhole_y = bbox["min_y"] + (bbox["max_y"] - bbox["min_y"]) * 0.30
            soundhole_center = (centroid[0], soundhole_y)
        else:
            soundhole_center = None

        # Build notes
        notes = []

        # Add fallback note if using alternative outline
        if fallback_note:
            notes.append(fallback_note)

        meta = get_body_metadata(style_str)
        if meta:
            if "dxf" in meta:
                notes.append(f"Source DXF: {meta['dxf']}")

        if self.scale != 1.0:
            notes.append(f"Scaled to {self.scale * 100:.0f}%")

        notes.append(f"Detailed outline with {len(points)} points")

        if ref_specs:
            vol = calculate_body_volume(ref_specs)
            hz = calculate_helmholtz_frequency(ref_specs, vol.volume_liters)
            notes.append(f"Reference: {ref_specs.name}")
            notes.append(f"Est. volume: {vol.volume_liters:.1f}L ({vol.volume_cubic_inches:.0f} in³)")
            notes.append(f"Helmholtz resonance: ~{hz:.0f} Hz")

        return AcousticBodyResult(
            style=style_str,
            width_mm=dims.get("width", bbox["max_x"] - bbox["min_x"]) * self.scale,
            length_mm=dims.get("length", bbox["max_y"] - bbox["min_y"]) * self.scale,
            points=points,
            point_count=len(points),
            centroid=centroid,
            bounding_box=bbox,
            scale_factor=self.scale,
            soundhole_center=soundhole_center,
            soundhole_diameter_mm=self.soundhole_diameter_mm * self.scale,
            depth_endblock_mm=depth_end * self.scale,
            depth_neck_mm=depth_neck * self.scale,
            notes=notes,
        )

    def generate_perimeter_gcode(
        self,
        tool_diameter_mm: float = 6.35,  # 1/4"
        total_depth_mm: float = 12.7,     # 1/2" stock
        stepdown_mm: float = 3.0,
        tab_count: int = 8,
        tab_width_mm: float = 15.0,
        tab_height_mm: float = 3.0,
        offset_direction: str = "outside",  # or "inside"
    ) -> str:
        """
        Generate G-code for body perimeter cut.

        Args:
            tool_diameter_mm: End mill diameter
            total_depth_mm: Total cut depth (stock thickness)
            stepdown_mm: Depth per pass
            tab_count: Number of holding tabs
            tab_width_mm: Tab width
            tab_height_mm: Tab height
            offset_direction: "outside" for perimeter, "inside" for pocket

        Returns:
            G-code string for perimeter operation
        """
        outline = self.generate_outline()

        if not outline.points:
            return "; ERROR: No outline points available for this style"

        # Calculate tool offset
        offset = tool_diameter_mm / 2
        if offset_direction == "inside":
            offset = -offset

        # Offset the path
        path = self._offset_path(outline.points, offset)

        # Calculate passes
        num_passes = max(1, math.ceil(total_depth_mm / stepdown_mm))

        # Calculate tab positions along path
        perimeter = self._path_length(path)
        tab_spacing = perimeter / tab_count
        tab_positions = [(i + 0.5) * tab_spacing for i in range(tab_count)]

        lines = []

        # Header
        lines.append(f"( ACOUSTIC BODY PERIMETER - {outline.style.upper()} )")
        lines.append(f"( Generated by AcousticBodyGenerator - GEN-6 )")
        lines.append(f"( Tool: {tool_diameter_mm}mm end mill )")
        lines.append(f"( Depth: {total_depth_mm}mm in {num_passes} passes )")
        lines.append(f"( Stepdown: {stepdown_mm}mm per pass )")
        lines.append(f"( Tabs: {tab_count} x {tab_width_mm}mm wide x {tab_height_mm}mm tall )")
        lines.append(f"( Body size: {outline.width_mm:.1f}mm W x {outline.length_mm:.1f}mm L )")
        lines.append("")

        # Setup
        lines.append("G21 (Units: mm)")
        lines.append("G90 (Absolute positioning)")
        lines.append(f"G0 Z{self.safe_z:.3f} (Safe height)")
        lines.append(f"M3 S{self.spindle_rpm} (Spindle on)")
        lines.append("G4 P2 (Dwell for spindle)")
        lines.append("")

        # Start point
        start_x, start_y = path[0]

        for pass_num in range(num_passes):
            current_depth = -stepdown_mm * (pass_num + 1)
            if current_depth < -total_depth_mm:
                current_depth = -total_depth_mm

            is_tab_pass = pass_num >= num_passes - 2  # Last 2 passes get tabs
            tab_z = -total_depth_mm + tab_height_mm

            lines.append(f"( Pass {pass_num + 1}/{num_passes}: Z = {current_depth:.3f} )")

            # Move to start
            lines.append(f"G0 Z{self.safe_z:.3f}")
            lines.append(f"G0 X{start_x:.3f} Y{start_y:.3f}")
            lines.append(f"G0 Z{self.rapid_z:.3f}")

            # Plunge
            lines.append(f"G1 Z{current_depth:.3f} F{self.feed_z:.0f}")

            # Cut path with tabs
            accumulated_dist = 0.0
            tab_idx = 0

            for i in range(1, len(path)):
                x, y = path[i]
                px, py = path[i - 1]
                seg_len = math.sqrt((x - px)**2 + (y - py)**2)

                # Check for tab in this segment
                in_tab = False
                if is_tab_pass and tab_idx < len(tab_positions):
                    tab_pos = tab_positions[tab_idx]
                    if accumulated_dist <= tab_pos < accumulated_dist + seg_len:
                        # Tab is in this segment
                        in_tab = True
                        t = (tab_pos - accumulated_dist) / seg_len
                        tab_start_x = px + (x - px) * max(0, t - tab_width_mm / (2 * seg_len))
                        tab_start_y = py + (y - py) * max(0, t - tab_width_mm / (2 * seg_len))
                        tab_end_x = px + (x - px) * min(1, t + tab_width_mm / (2 * seg_len))
                        tab_end_y = py + (y - py) * min(1, t + tab_width_mm / (2 * seg_len))

                        # Cut to tab start
                        lines.append(f"G1 X{tab_start_x:.3f} Y{tab_start_y:.3f} F{self.feed_xy:.0f}")
                        # Lift for tab
                        lines.append(f"G1 Z{tab_z:.3f} F{self.feed_z:.0f}")
                        # Cross tab
                        lines.append(f"G1 X{tab_end_x:.3f} Y{tab_end_y:.3f} F{self.feed_xy:.0f}")
                        # Plunge back down
                        lines.append(f"G1 Z{current_depth:.3f} F{self.feed_z:.0f}")

                        tab_idx += 1

                if not in_tab:
                    lines.append(f"G1 X{x:.3f} Y{y:.3f} F{self.feed_xy:.0f}")

                accumulated_dist += seg_len

            # Close path
            lines.append(f"G1 X{start_x:.3f} Y{start_y:.3f}")
            lines.append("")

        # Retract
        lines.append(f"G0 Z{self.safe_z:.3f}")
        lines.append("M5 (Spindle off)")
        lines.append("M30 (Program end)")

        return "\n".join(lines)

    def generate_soundhole_gcode(
        self,
        tool_diameter_mm: float = 6.35,
        depth_mm: float = 3.5,  # Top thickness
        stepdown_mm: float = 1.0,
    ) -> str:
        """
        Generate G-code for soundhole routing.

        Args:
            tool_diameter_mm: End mill diameter
            depth_mm: Soundhole depth (top thickness)
            stepdown_mm: Depth per pass

        Returns:
            G-code string for soundhole operation
        """
        outline = self.generate_outline()

        if not outline.soundhole_center:
            return "; ERROR: No soundhole center defined for this outline"

        cx, cy = outline.soundhole_center
        radius = (outline.soundhole_diameter_mm - tool_diameter_mm) / 2

        num_passes = max(1, math.ceil(depth_mm / stepdown_mm))

        lines = []

        # Header
        lines.append(f"( SOUNDHOLE ROUTING - {outline.style.upper()} )")
        lines.append(f"( Diameter: {outline.soundhole_diameter_mm:.1f}mm )")
        lines.append(f"( Tool: {tool_diameter_mm}mm end mill )")
        lines.append(f"( Depth: {depth_mm}mm in {num_passes} passes )")
        lines.append("")

        # Setup
        lines.append("G21 (Units: mm)")
        lines.append("G90 (Absolute positioning)")
        lines.append(f"G0 Z{self.safe_z:.3f}")
        lines.append(f"M3 S{self.spindle_rpm}")
        lines.append("G4 P2")
        lines.append("")

        # Move to start (3 o'clock position)
        start_x = cx + radius
        start_y = cy

        for pass_num in range(num_passes):
            current_depth = -stepdown_mm * (pass_num + 1)
            if current_depth < -depth_mm:
                current_depth = -depth_mm

            lines.append(f"( Pass {pass_num + 1}/{num_passes}: Z = {current_depth:.3f} )")

            # Move to start
            lines.append(f"G0 X{start_x:.3f} Y{start_y:.3f}")
            lines.append(f"G0 Z{self.rapid_z:.3f}")
            lines.append(f"G1 Z{current_depth:.3f} F{self.feed_z:.0f}")

            # Full circle using G2 (clockwise)
            # G2 X Y I J - I and J are relative to current position
            lines.append(f"G2 X{start_x:.3f} Y{start_y:.3f} I{-radius:.3f} J0 F{self.feed_xy:.0f}")
            lines.append("")

        # Retract
        lines.append(f"G0 Z{self.safe_z:.3f}")
        lines.append("M5")
        lines.append("M30")

        return "\n".join(lines)

    def generate_binding_channel_gcode(
        self,
        channel_width_mm: float = 2.0,
        channel_depth_mm: float = 2.0,
        tool_diameter_mm: float = 2.0,  # Match channel width
        stepdown_mm: float = 0.5,
    ) -> str:
        """
        Generate G-code for binding channel routing.

        Args:
            channel_width_mm: Binding channel width
            channel_depth_mm: Binding channel depth
            tool_diameter_mm: Slot cutter or end mill diameter
            stepdown_mm: Depth per pass

        Returns:
            G-code string for binding channel operation
        """
        outline = self.generate_outline()

        if not outline.points:
            return "; ERROR: No outline points available"

        # Offset path inward by half tool diameter
        offset = -tool_diameter_mm / 2
        path = self._offset_path(outline.points, offset)

        num_passes = max(1, math.ceil(channel_depth_mm / stepdown_mm))

        lines = []

        # Header
        lines.append(f"( BINDING CHANNEL - {outline.style.upper()} )")
        lines.append(f"( Channel: {channel_width_mm}mm W x {channel_depth_mm}mm D )")
        lines.append(f"( Tool: {tool_diameter_mm}mm )")
        lines.append(f"( Passes: {num_passes} )")
        lines.append("")

        # Setup
        lines.append("G21")
        lines.append("G90")
        lines.append(f"G0 Z{self.safe_z:.3f}")
        lines.append(f"M3 S{self.spindle_rpm}")
        lines.append("G4 P2")
        lines.append("")

        start_x, start_y = path[0]

        for pass_num in range(num_passes):
            current_depth = -stepdown_mm * (pass_num + 1)
            if current_depth < -channel_depth_mm:
                current_depth = -channel_depth_mm

            lines.append(f"( Pass {pass_num + 1}/{num_passes}: Z = {current_depth:.3f} )")

            lines.append(f"G0 X{start_x:.3f} Y{start_y:.3f}")
            lines.append(f"G0 Z{self.rapid_z:.3f}")
            lines.append(f"G1 Z{current_depth:.3f} F{self.feed_z:.0f}")

            for x, y in path[1:]:
                lines.append(f"G1 X{x:.3f} Y{y:.3f} F{self.feed_xy * 0.6:.0f}")  # Slower for binding

            # Close path
            lines.append(f"G1 X{start_x:.3f} Y{start_y:.3f}")
            lines.append("")

        lines.append(f"G0 Z{self.safe_z:.3f}")
        lines.append("M5")
        lines.append("M30")

        return "\n".join(lines)

    def _offset_path(self, points: List[Tuple[float, float]], offset: float) -> List[Tuple[float, float]]:
        """Offset a closed path by the given distance (positive = outward)."""
        if len(points) < 3:
            return points

        result = []
        n = len(points)

        for i in range(n):
            # Get adjacent points
            p0 = points[(i - 1) % n]
            p1 = points[i]
            p2 = points[(i + 1) % n]

            # Calculate normals for both edges
            dx1 = p1[0] - p0[0]
            dy1 = p1[1] - p0[1]
            len1 = math.sqrt(dx1**2 + dy1**2) or 1
            n1 = (-dy1 / len1, dx1 / len1)

            dx2 = p2[0] - p1[0]
            dy2 = p2[1] - p1[1]
            len2 = math.sqrt(dx2**2 + dy2**2) or 1
            n2 = (-dy2 / len2, dx2 / len2)

            # Average normal
            nx = (n1[0] + n2[0]) / 2
            ny = (n1[1] + n2[1]) / 2
            nlen = math.sqrt(nx**2 + ny**2) or 1
            nx, ny = nx / nlen, ny / nlen

            # Offset point
            result.append((p1[0] + nx * offset, p1[1] + ny * offset))

        return result

    def _path_length(self, points: List[Tuple[float, float]]) -> float:
        """Calculate total path length."""
        total = 0.0
        for i in range(1, len(points)):
            dx = points[i][0] - points[i-1][0]
            dy = points[i][1] - points[i-1][1]
            total += math.sqrt(dx**2 + dy**2)
        # Close path
        if points:
            dx = points[0][0] - points[-1][0]
            dy = points[0][1] - points[-1][1]
            total += math.sqrt(dx**2 + dy**2)
        return total


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_acoustic_outline(
    style: AcousticBodyStyle | str = AcousticBodyStyle.DREADNOUGHT,
    scale: float = 1.0,
) -> AcousticBodyResult:
    """
    Generate an acoustic guitar body outline.

    Args:
        style: Body style (dreadnought, om, oo, jumbo, etc.)
        scale: Scale factor (default 1.0 = full size)

    Returns:
        AcousticBodyResult with outline geometry and metadata.
    """
    generator = AcousticBodyGenerator.from_style(style, scale=scale)
    return generator.generate_outline()


def list_acoustic_styles() -> List[Dict[str, Any]]:
    """
    List all available acoustic body styles.

    Returns:
        List of dicts with style info (id, dimensions, has_outline).
    """
    acoustic_bodies = list_bodies_by_category("acoustic")
    results = []

    for body_id in acoustic_bodies:
        meta = get_body_metadata(body_id)
        if meta:
            results.append({
                "id": body_id,
                "width_mm": meta.get("width_mm", 0),
                "height_mm": meta.get("height_mm", 0),
                "has_detailed_outline": True,
            })

    # Add enum-defined styles
    for style in AcousticBodyStyle:
        if style.value not in [r["id"] for r in results]:
            dims = get_body_dimensions(style.value)
            results.append({
                "id": style.value,
                "width_mm": dims.get("width", 0),
                "height_mm": dims.get("length", 0),
                "has_detailed_outline": False,
            })

    return sorted(results, key=lambda x: x["id"])


def get_dreadnought_outline(scale: float = 1.0) -> AcousticBodyResult:
    """Alias for Dreadnought outline."""
    return generate_acoustic_outline(AcousticBodyStyle.DREADNOUGHT, scale=scale)


def get_om_outline(scale: float = 1.0) -> AcousticBodyResult:
    """Alias for OM/000 outline."""
    return generate_acoustic_outline(AcousticBodyStyle.OM, scale=scale)


def get_oo_outline(scale: float = 1.0) -> AcousticBodyResult:
    """Alias for 00 (Martin OO) outline."""
    return generate_acoustic_outline(AcousticBodyStyle.OO, scale=scale)
