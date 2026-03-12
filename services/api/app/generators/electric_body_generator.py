#!/usr/bin/env python3
"""Electric Body Outline Generator

GAP-07: Generic electric guitar body outline generator that supports
Stratocaster, Les Paul, and other electric guitar body styles.

Uses detailed outlines extracted from DXF files (instrument_geometry.body.detailed_outlines).
Provides SVG and DXF export for CAD/CAM workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Literal, Optional
from enum import Enum

# Import body outline data
from ..instrument_geometry.body.outlines import (
    get_body_outline,
    get_body_dimensions,
    get_body_metadata,
    get_available_outlines,
    list_bodies_by_category,
)


class ElectricBodyStyle(str, Enum):
    """Supported electric guitar body styles."""
    STRATOCASTER = "stratocaster"
    LES_PAUL = "les_paul"
    TELECASTER = "telecaster"
    JS1000 = "js1000"
    GIBSON_EXPLORER = "gibson_explorer"
    FLYING_V = "flying_v"
    HARMONY_H44 = "harmony_h44"
    SG = "sg"


@dataclass
class BodyOutlineResult:
    """Result of body outline generation."""

    style: str
    width_mm: float
    length_mm: float
    points: List[Tuple[float, float]]
    point_count: int
    centroid: Tuple[float, float]
    bounding_box: Dict[str, float]
    scale_factor: float = 1.0
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
            "notes": self.notes,
            "points": [(round(x, 3), round(y, 3)) for x, y in self.points],
        }

    def to_svg(self,
               stroke_color: str = "#333333",
               stroke_width: float = 0.5,
               fill: str = "none",
               include_centerline: bool = False) -> str:
        """Generate SVG representation of the body outline."""
        if not self.points:
            return ""

        # SVG viewBox with padding
        padding = 10
        min_x = self.bounding_box["min_x"] - padding
        min_y = self.bounding_box["min_y"] - padding
        width = self.width_mm + 2 * padding
        height = self.length_mm + 2 * padding

        # Build path data
        path_data = f"M {self.points[0][0]},{self.points[0][1]}"
        for x, y in self.points[1:]:
            path_data += f" L {x},{y}"
        path_data += " Z"

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {width} {height}" width="{width}mm" height="{height}mm">',
            f'  <path d="{path_data}" stroke="{stroke_color}" stroke-width="{stroke_width}" fill="{fill}" />',
        ]

        # Add centerline if requested
        if include_centerline:
            cx = self.centroid[0]
            svg_parts.append(
                f'  <line x1="{cx}" y1="{min_y + padding}" x2="{cx}" y2="{min_y + height - padding}" '
                f'stroke="#999999" stroke-width="0.25" stroke-dasharray="2,2" />'
            )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)


def generate_body_outline(
    style: ElectricBodyStyle | str = ElectricBodyStyle.STRATOCASTER,
    scale: float = 1.0,
    detailed: bool = True,
) -> BodyOutlineResult:
    """
    Generate an electric guitar body outline.

    Args:
        style: Body style (stratocaster, les_paul, telecaster, etc.)
        scale: Scale factor (default 1.0 = full size)
        detailed: If True, return detailed outline with many points;
                  if False, return simplified bounding box

    Returns:
        BodyOutlineResult with outline geometry and metadata.

    Examples:
        >>> result = generate_body_outline("stratocaster")
        >>> result.width_mm
        322.3
        >>> result = generate_body_outline(ElectricBodyStyle.LES_PAUL, scale=0.5)
        >>> result.scale_factor
        0.5
    """
    # Normalize style to string
    style_str = style.value if isinstance(style, ElectricBodyStyle) else str(style).lower()
    style_str = style_str.replace("-", "_").replace(" ", "_")

    # Get outline points
    points = get_body_outline(style_str, scale=scale, detailed=detailed)

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

    # Build notes
    notes = []
    meta = get_body_metadata(style_str)
    if meta:
        if "dxf" in meta:
            notes.append(f"Source DXF: {meta['dxf']}")

    if scale != 1.0:
        notes.append(f"Scaled to {scale * 100:.0f}%")

    if not detailed:
        notes.append("Simplified outline (bounding box only)")
    else:
        notes.append(f"Detailed outline with {len(points)} points")

    return BodyOutlineResult(
        style=style_str,
        width_mm=dims["width"] * scale,
        length_mm=dims["length"] * scale,
        points=points,
        point_count=len(points),
        centroid=centroid,
        bounding_box=bbox,
        scale_factor=scale,
        notes=notes,
    )


def list_available_styles() -> List[Dict[str, Any]]:
    """
    List all available electric body styles.

    Returns:
        List of dicts with style info (id, dimensions, category).
    """
    electric_bodies = list_bodies_by_category("electric")
    results = []

    for body_id in electric_bodies:
        meta = get_body_metadata(body_id)
        if meta:
            results.append({
                "id": body_id,
                "width_mm": meta.get("width_mm", 0),
                "height_mm": meta.get("height_mm", 0),
                "has_detailed_outline": True,  # All electric bodies have DXF-extracted outlines
            })

    # Add enum-defined styles that may not have metadata
    for style in ElectricBodyStyle:
        if style.value not in [r["id"] for r in results]:
            dims = get_body_dimensions(style.value)
            results.append({
                "id": style.value,
                "width_mm": dims.get("width", 0),
                "height_mm": dims.get("length", 0),
                "has_detailed_outline": False,
            })

    return sorted(results, key=lambda x: x["id"])


def get_stratocaster_outline(
    fret_count: int = 22,
    scale: float = 1.0,
) -> BodyOutlineResult:
    """
    Get Stratocaster body outline with fret-count-aware adjustments.

    For 24-fret Stratocasters, the neck pocket position shifts slightly
    to accommodate the extended fretboard.

    Args:
        fret_count: Number of frets (21, 22, or 24)
        scale: Scale factor

    Returns:
        BodyOutlineResult with Strat outline.
    """
    result = generate_body_outline(ElectricBodyStyle.STRATOCASTER, scale=scale)

    if fret_count >= 24:
        result.notes.append("24-fret configuration: neck pocket may require adjustment")
        result.notes.append("Extended fretboard reduces neck pickup clearance")

    return result


# Convenience aliases
def get_strat_outline(scale: float = 1.0) -> BodyOutlineResult:
    """Alias for Stratocaster outline."""
    return generate_body_outline(ElectricBodyStyle.STRATOCASTER, scale=scale)


def get_lespaul_outline(scale: float = 1.0) -> BodyOutlineResult:
    """Alias for Les Paul outline."""
    return generate_body_outline(ElectricBodyStyle.LES_PAUL, scale=scale)


def get_telecaster_outline(scale: float = 1.0) -> BodyOutlineResult:
    """Alias for Telecaster outline."""
    return generate_body_outline(ElectricBodyStyle.TELECASTER, scale=scale)
