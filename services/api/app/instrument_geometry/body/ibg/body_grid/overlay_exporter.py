"""
Overlay Exporter — PNG Overlay Generation for Human Review
===========================================================

Generates visual overlays showing:
- Grid zones
- Centerline
- Assigned primitives
- Missing regions
- Confidence/uncertainty

Author: Production Shop
Date: 2026-05-15
Sprint: IBG Body Grid Semantic Encoding
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from .body_grid_schema import NormalizedPoint
from .morphology_descriptor import MorphologyDescriptor
from .primitives import MorphologyPrimitive, PrimitiveType, CurvatureClass
from .zones import ZoneId, ZONE_DEFINITIONS
from .grid_normalizer import GridNormalizer


# Zone colors (RGB)
ZONE_COLORS: Dict[str, Tuple[int, int, int]] = {
    ZoneId.BUTT_END.value: (139, 69, 19),       # Brown
    ZoneId.LOWER_BOUT.value: (34, 139, 34),     # Forest green
    ZoneId.WAIST.value: (255, 165, 0),          # Orange
    ZoneId.UPPER_BOUT.value: (65, 105, 225),    # Royal blue
    ZoneId.HORN_LEFT.value: (148, 0, 211),      # Violet
    ZoneId.HORN_RIGHT.value: (148, 0, 211),     # Violet
    ZoneId.CUTAWAY_LEFT.value: (220, 20, 60),   # Crimson
    ZoneId.CUTAWAY_RIGHT.value: (220, 20, 60),  # Crimson
    ZoneId.NECK_POCKET.value: (70, 130, 180),   # Steel blue
    ZoneId.SHOULDER.value: (100, 149, 237),     # Cornflower blue
    ZoneId.BRIDGE_REGION.value: (128, 128, 0),  # Olive
    ZoneId.LEFT_FLANK.value: (169, 169, 169),   # Dark gray
    ZoneId.RIGHT_FLANK.value: (169, 169, 169),  # Dark gray
    ZoneId.CENTERLINE.value: (255, 0, 0),       # Red
}

PRIMITIVE_COLORS: Dict[PrimitiveType, Tuple[int, int, int]] = {
    PrimitiveType.CONVEX_BOUT: (0, 200, 0),
    PrimitiveType.CONCAVE_WAIST: (255, 140, 0),
    PrimitiveType.HORN_PROJECTION: (180, 0, 180),
    PrimitiveType.CUTAWAY_INTRUSION: (200, 0, 0),
    PrimitiveType.FLAT_SLAB_EDGE: (128, 128, 128),
    PrimitiveType.LINE_SEGMENT: (100, 100, 100),
    PrimitiveType.ARC_SEGMENT: (0, 150, 150),
    PrimitiveType.BUTT_TERMINATION: (139, 69, 19),
    PrimitiveType.NECK_JUNCTION: (70, 130, 180),
    PrimitiveType.SHOULDER_TRANSITION: (100, 149, 237),
}


@dataclass
class OverlayConfig:
    """Configuration for overlay generation."""
    width: int = 800
    height: int = 1000
    margin: int = 50
    show_zones: bool = True
    show_primitives: bool = True
    show_centerline: bool = True
    show_missing: bool = True
    show_labels: bool = True
    show_legend: bool = True
    zone_alpha: int = 80
    primitive_line_width: int = 3
    font_size: int = 12


class OverlayExporter:
    """
    Generates PNG overlay images for human review.

    Visualizes Body Grid analysis results including zones,
    primitives, centerline, and missing regions.
    """

    def __init__(self, config: Optional[OverlayConfig] = None):
        if not HAS_PIL:
            raise ImportError("PIL (Pillow) is required for overlay generation. Install with: pip install Pillow")
        self.config = config or OverlayConfig()
        self._font = None

    def export(
        self,
        descriptor: MorphologyDescriptor,
        output_path: Optional[str] = None,
        background: Optional[Image.Image] = None
    ) -> Image.Image:
        """
        Generate overlay image from MorphologyDescriptor.

        Args:
            descriptor: MorphologyDescriptor to visualize
            output_path: Optional path to save PNG
            background: Optional background image to overlay on

        Returns:
            PIL Image object
        """
        # Create or use background
        if background:
            img = background.copy().convert("RGBA")
            # Resize if needed
            if img.size != (self.config.width, self.config.height):
                img = img.resize((self.config.width, self.config.height))
        else:
            img = Image.new("RGBA", (self.config.width, self.config.height), (255, 255, 255, 255))

        draw = ImageDraw.Draw(img, "RGBA")

        # Draw layers in order
        if self.config.show_zones:
            self._draw_zones(draw, descriptor)

        if self.config.show_centerline:
            self._draw_centerline(draw, descriptor)

        if self.config.show_primitives:
            self._draw_primitives(draw, descriptor)

        if self.config.show_missing:
            self._draw_missing_regions(draw, descriptor)

        if self.config.show_labels:
            self._draw_labels(draw, descriptor)

        if self.config.show_legend:
            self._draw_legend(draw, descriptor)

        # Save if path provided
        if output_path:
            # Convert to RGB for PNG save
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
            rgb_img.save(output_path)

        return img

    def _norm_to_pixel(self, x_norm: float, y_norm: float) -> Tuple[int, int]:
        """Convert normalized coordinates to pixel coordinates."""
        # Account for margin
        draw_width = self.config.width - 2 * self.config.margin
        draw_height = self.config.height - 2 * self.config.margin

        # x_norm is -1 to 1 (centerline at 0)
        # y_norm is 0 to 1 (butt at 0, neck at 1)
        px = int(self.config.margin + (x_norm + 1) / 2 * draw_width)
        py = int(self.config.margin + (1 - y_norm) * draw_height)  # Flip Y

        return (px, py)

    def _draw_zones(self, draw: ImageDraw.Draw, descriptor: MorphologyDescriptor):
        """Draw zone regions as semi-transparent overlays."""
        for zone_id, zone_def in ZONE_DEFINITIONS.items():
            if zone_id in (ZoneId.CENTERLINE, ZoneId.LEFT_FLANK, ZoneId.RIGHT_FLANK):
                continue  # Skip full-span zones

            y_min, y_max = zone_def.y_range
            color = ZONE_COLORS.get(zone_id.value, (128, 128, 128))

            # Draw zone as rectangle (simplified)
            x1, y1 = self._norm_to_pixel(-1.0, y_max)
            x2, y2 = self._norm_to_pixel(1.0, y_min)

            fill_color = (*color, self.config.zone_alpha)
            draw.rectangle([x1, y1, x2, y2], fill=fill_color, outline=color)

    def _draw_centerline(self, draw: ImageDraw.Draw, descriptor: MorphologyDescriptor):
        """Draw centerline."""
        color = ZONE_COLORS[ZoneId.CENTERLINE.value]
        x1, y1 = self._norm_to_pixel(0.0, 0.0)
        x2, y2 = self._norm_to_pixel(0.0, 1.0)
        draw.line([x1, y1, x2, y2], fill=color, width=2)

        # Draw symmetry indicator
        sym_score = descriptor.centerline.symmetry_score
        label = f"Sym: {sym_score:.2f}"
        draw.text((x1 + 5, y1 + 10), label, fill=color)

    def _draw_primitives(self, draw: ImageDraw.Draw, descriptor: MorphologyDescriptor):
        """Draw detected primitives."""
        for prim in descriptor.primitives:
            if len(prim.points) < 2:
                continue

            color = PRIMITIVE_COLORS.get(prim.primitive_type, (100, 100, 100))

            # Draw as polyline
            pixels = [self._norm_to_pixel(p.x_norm, p.y_norm) for p in prim.points]
            if len(pixels) >= 2:
                draw.line(pixels, fill=color, width=self.config.primitive_line_width)

            # Draw curvature indicator at midpoint
            if len(pixels) >= 3:
                mid_idx = len(pixels) // 2
                mx, my = pixels[mid_idx]

                if prim.curvature_class == CurvatureClass.CONVEX_OUTWARD:
                    # Small outward arrow
                    draw.ellipse([mx-3, my-3, mx+3, my+3], fill=(0, 200, 0))
                elif prim.curvature_class == CurvatureClass.CONCAVE_INWARD:
                    # Small inward arrow
                    draw.ellipse([mx-3, my-3, mx+3, my+3], fill=(255, 140, 0))

    def _draw_missing_regions(self, draw: ImageDraw.Draw, descriptor: MorphologyDescriptor):
        """Highlight missing regions."""
        for zone_name in descriptor.missing_regions:
            # Find zone definition
            zone_id = None
            for zid in ZoneId:
                if zid.value == zone_name:
                    zone_id = zid
                    break

            if zone_id and zone_id in ZONE_DEFINITIONS:
                zone_def = ZONE_DEFINITIONS[zone_id]
                y_min, y_max = zone_def.y_range

                x1, y1 = self._norm_to_pixel(-0.8, y_max)
                x2, y2 = self._norm_to_pixel(0.8, y_min)

                # Draw hatched pattern to indicate missing
                for i in range(0, x2 - x1, 10):
                    draw.line([(x1 + i, y1), (x1 + i + 20, y2)], fill=(255, 0, 0, 100), width=1)

    def _draw_labels(self, draw: ImageDraw.Draw, descriptor: MorphologyDescriptor):
        """Draw zone labels."""
        for zone_id, zone_def in ZONE_DEFINITIONS.items():
            if zone_id in (ZoneId.LEFT_FLANK, ZoneId.RIGHT_FLANK, ZoneId.OUTER_BOUNDARY):
                continue

            y_mid = (zone_def.y_range[0] + zone_def.y_range[1]) / 2
            x, y = self._norm_to_pixel(0.85, y_mid)

            coverage = descriptor.zone_coverage.get(zone_id.value, 0.0)
            label = f"{zone_def.name}: {coverage:.0%}"
            color = ZONE_COLORS.get(zone_id.value, (0, 0, 0))
            draw.text((x, y), label, fill=color)

    def _draw_legend(self, draw: ImageDraw.Draw, descriptor: MorphologyDescriptor):
        """Draw legend with classification info."""
        x, y = 10, 10
        line_height = 18

        # Title
        draw.text((x, y), "Body Grid Analysis", fill=(0, 0, 0))
        y += line_height * 1.5

        # Variant info
        draw.text((x, y), f"Class: {descriptor.variant_match.morphology_class.value}", fill=(0, 0, 128))
        y += line_height

        draw.text((x, y), f"Horns: {descriptor.variant_match.horn_behavior.value}", fill=(0, 0, 128))
        y += line_height

        draw.text((x, y), f"Waist: {descriptor.variant_match.waist_behavior.value}", fill=(0, 0, 128))
        y += line_height

        # Asymmetry
        asym = descriptor.asymmetry
        draw.text((x, y), f"Asymmetry: {asym.asymmetry_score:.2f}", fill=(128, 0, 0))
        y += line_height

        if asym.asymmetry_type:
            draw.text((x, y), f"Type: {asym.asymmetry_type}", fill=(128, 0, 0))
            y += line_height

        # Confidence
        y += line_height
        draw.text((x, y), f"Confidence: {descriptor.confidence:.2f}", fill=(0, 128, 0))
        y += line_height

        # Primitive count
        draw.text((x, y), f"Primitives: {len(descriptor.primitives)}", fill=(0, 0, 0))


def export_overlay(
    descriptor: MorphologyDescriptor,
    output_path: str,
    config: Optional[OverlayConfig] = None
) -> str:
    """
    Convenience function to export overlay.

    Args:
        descriptor: MorphologyDescriptor to visualize
        output_path: Path for output PNG
        config: Optional overlay configuration

    Returns:
        Output path
    """
    exporter = OverlayExporter(config)
    exporter.export(descriptor, output_path)
    return output_path
