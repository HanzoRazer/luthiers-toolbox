#!/usr/bin/env python3
"""
Rosette Pattern Renderer

Renders actual pattern geometry from matrix formulas with realistic wood textures.
This demonstrates that the formulas work - not AI artistic interpretation.

The renderer takes the mathematical pattern definition and creates a true
visualization of what the rosette will look like when built.
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import io

try:
    from PIL import Image, ImageDraw, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from .pattern_generator import (
    MatrixFormula,
    RosettePatternEngine,
    PRESET_MATRICES,
)


# Wood color palettes (RGB) - realistic wood tones
WOOD_COLORS: Dict[str, Tuple[int, int, int]] = {
    # Standard black/white
    "black": (25, 20, 15),        # Ebony - very dark brown-black
    "white": (245, 235, 220),     # Holly/Maple - creamy white

    # Browns
    "brown": (101, 67, 33),       # Walnut - medium brown
    "mahogany": (103, 49, 36),    # Mahogany - reddish brown
    "rosewood": (65, 25, 15),     # Rosewood - dark reddish brown
    "walnut": (78, 55, 40),       # Walnut
    "cherry": (150, 85, 60),      # Cherry - pinkish tan
    "cedar": (165, 100, 70),      # Cedar - warm tan

    # Lights
    "maple": (235, 215, 180),     # Maple - light tan
    "spruce": (240, 225, 195),    # Spruce - pale yellow
    "holly": (250, 245, 235),     # Holly - near white
    "natural": (210, 180, 140),   # Generic light wood

    # Dyed colors
    "red": (165, 42, 42),         # Dyed red veneer
    "green": (34, 85, 51),        # Dyed green veneer
    "blue": (35, 55, 95),         # Dyed blue veneer
}


@dataclass
class RenderConfig:
    """Configuration for pattern rendering."""
    image_size: int = 800              # Output image size in pixels
    outer_diameter_mm: float = 101.6   # 4 inches
    ring_width_mm: float = 8.0         # Width of pattern ring
    background_color: Tuple[int, int, int] = (240, 230, 210)  # Spruce top
    soundhole_color: Tuple[int, int, int] = (30, 25, 20)      # Dark interior
    border_color: Tuple[int, int, int] = (20, 15, 10)         # Thin black lines
    add_grain_texture: bool = True     # Add wood grain effect
    add_border_lines: bool = True      # Add thin lines between tiles
    dpi: int = 150                     # Output DPI


class PatternRenderer:
    """
    Renders rosette patterns from matrix formulas.

    Creates accurate visualizations of the actual pattern geometry,
    demonstrating that the mathematical formulas produce real designs.
    """

    def __init__(self, config: Optional[RenderConfig] = None):
        if not HAS_PIL:
            raise ImportError("PIL/Pillow required for pattern rendering. Install with: pip install Pillow")
        self.config = config or RenderConfig()

    def _get_wood_color(self, material: str) -> Tuple[int, int, int]:
        """Get RGB color for a wood/material name."""
        material_lower = material.lower()
        if material_lower in WOOD_COLORS:
            return WOOD_COLORS[material_lower]
        # Try partial match
        for key, color in WOOD_COLORS.items():
            if key in material_lower or material_lower in key:
                return color
        # Default to natural wood
        return WOOD_COLORS["natural"]

    def _add_grain_texture(self, img: Image.Image, color: Tuple[int, int, int]) -> Image.Image:
        """Add subtle wood grain texture to a solid color."""
        import random
        pixels = img.load()
        width, height = img.size

        # Add subtle vertical grain lines
        for x in range(width):
            # Vary intensity along x for grain effect
            grain_intensity = random.randint(-15, 15)
            for y in range(height):
                if pixels[x, y][3] > 0:  # Only modify non-transparent pixels
                    r, g, b, a = pixels[x, y]
                    # Add subtle variation
                    r = max(0, min(255, r + grain_intensity + random.randint(-5, 5)))
                    g = max(0, min(255, g + grain_intensity + random.randint(-5, 5)))
                    b = max(0, min(255, b + grain_intensity + random.randint(-5, 5)))
                    pixels[x, y] = (r, g, b, a)

        return img

    def render_matrix_pattern(
        self,
        formula: MatrixFormula,
        show_labels: bool = False,
    ) -> Image.Image:
        """
        Render a matrix formula as a rectangular pattern strip.

        This shows the pattern as it would appear before being bent
        into a ring - useful for understanding the matrix structure.

        Args:
            formula: The matrix formula to render
            show_labels: Add row/column labels

        Returns:
            PIL Image of the pattern strip
        """
        # Calculate dimensions
        cell_size = 40  # pixels per cell
        cols = formula.column_count
        rows = max(sum(row.values()) for row in formula.rows)

        width = cols * cell_size + (40 if show_labels else 0)
        height = rows * cell_size + (40 if show_labels else 0)

        img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        x_offset = 40 if show_labels else 0
        y_offset = 40 if show_labels else 0

        # Draw each column based on sequence
        for col_idx, row_ref in enumerate(formula.column_sequence):
            row_data = formula.rows[row_ref - 1]  # 1-indexed

            # Get materials and counts for this row
            y_pos = y_offset
            for material, count in row_data.items():
                color = self._get_wood_color(material)
                for _ in range(count):
                    x = x_offset + col_idx * cell_size
                    y = y_pos

                    # Draw filled rectangle
                    draw.rectangle(
                        [x, y, x + cell_size - 1, y + cell_size - 1],
                        fill=color,
                        outline=(50, 50, 50) if self.config.add_border_lines else None
                    )
                    y_pos += cell_size

        # Add labels if requested
        if show_labels:
            # Column numbers
            for col_idx, row_ref in enumerate(formula.column_sequence):
                x = x_offset + col_idx * cell_size + cell_size // 2
                draw.text((x, 10), str(row_ref), fill=(0, 0, 0), anchor="mm")

            # Row numbers
            for row_idx in range(rows):
                y = y_offset + row_idx * cell_size + cell_size // 2
                draw.text((15, y), str(row_idx + 1), fill=(0, 0, 0), anchor="mm")

        return img

    def render_rosette_ring(
        self,
        formula: MatrixFormula,
        num_repeats: int = 1,
    ) -> Image.Image:
        """
        Render a matrix formula as a circular rosette ring.

        This shows the pattern bent into the actual ring shape
        as it would appear on a guitar.

        Args:
            formula: The matrix formula to render
            num_repeats: How many times to repeat the pattern around the ring

        Returns:
            PIL Image of the rosette ring
        """
        size = self.config.image_size
        center = size // 2

        # Calculate radii
        scale = size / (self.config.outer_diameter_mm + 20)  # pixels per mm
        outer_r = (self.config.outer_diameter_mm / 2) * scale
        inner_r = outer_r - (self.config.ring_width_mm * scale)

        # Create image with background (simulating spruce top)
        img = Image.new('RGBA', (size, size), self.config.background_color + (255,))
        draw = ImageDraw.Draw(img)

        # Draw soundhole (dark circle in center)
        soundhole_r = inner_r - 5
        draw.ellipse(
            [center - soundhole_r, center - soundhole_r,
             center + soundhole_r, center + soundhole_r],
            fill=self.config.soundhole_color + (255,)
        )

        # Calculate pattern segments
        total_cols = formula.column_count * num_repeats
        angle_per_col = 2 * math.pi / total_cols

        # Get max strips in any row (pattern height)
        max_strips = max(sum(row.values()) for row in formula.rows)
        strip_height = (outer_r - inner_r) / max_strips

        # Draw each segment
        for repeat in range(num_repeats):
            for col_idx, row_ref in enumerate(formula.column_sequence):
                row_data = formula.rows[row_ref - 1]

                global_col = repeat * formula.column_count + col_idx
                start_angle = global_col * angle_per_col - math.pi / 2  # Start from top
                end_angle = start_angle + angle_per_col

                # Draw strips for this column
                current_r = inner_r
                for material, count in row_data.items():
                    color = self._get_wood_color(material)

                    for _ in range(count):
                        # Draw arc segment
                        self._draw_arc_segment(
                            draw, center, center,
                            current_r, current_r + strip_height,
                            start_angle, end_angle,
                            color
                        )
                        current_r += strip_height

        # Draw border circles
        if self.config.add_border_lines:
            draw.ellipse(
                [center - outer_r, center - outer_r,
                 center + outer_r, center + outer_r],
                outline=self.config.border_color + (255,), width=1
            )
            draw.ellipse(
                [center - inner_r, center - inner_r,
                 center + inner_r, center + inner_r],
                outline=self.config.border_color + (255,), width=1
            )

        return img

    def _draw_arc_segment(
        self,
        draw: ImageDraw.Draw,
        cx: float, cy: float,
        inner_r: float, outer_r: float,
        start_angle: float, end_angle: float,
        color: Tuple[int, int, int],
        steps: int = 8
    ):
        """Draw a filled arc segment (pie slice of an annulus)."""
        # Build polygon points
        points = []

        # Outer arc (forward)
        for i in range(steps + 1):
            angle = start_angle + (end_angle - start_angle) * i / steps
            x = cx + outer_r * math.cos(angle)
            y = cy + outer_r * math.sin(angle)
            points.append((x, y))

        # Inner arc (backward)
        for i in range(steps, -1, -1):
            angle = start_angle + (end_angle - start_angle) * i / steps
            x = cx + inner_r * math.cos(angle)
            y = cy + inner_r * math.sin(angle)
            points.append((x, y))

        draw.polygon(points, fill=color + (255,), outline=self.config.border_color + (200,) if self.config.add_border_lines else None)

    def render_preset(
        self,
        preset_id: str,
        as_ring: bool = True,
        num_repeats: int = 4,
    ) -> Image.Image:
        """
        Render a preset pattern by ID.

        Args:
            preset_id: Key from PRESET_MATRICES
            as_ring: If True, render as circular ring; if False, as flat strip
            num_repeats: For ring mode, how many pattern repeats

        Returns:
            PIL Image
        """
        if preset_id not in PRESET_MATRICES:
            available = ", ".join(PRESET_MATRICES.keys())
            raise ValueError(f"Unknown preset '{preset_id}'. Available: {available}")

        formula = PRESET_MATRICES[preset_id]

        if as_ring:
            return self.render_rosette_ring(formula, num_repeats)
        else:
            return self.render_matrix_pattern(formula, show_labels=True)

    def save_render(
        self,
        img: Image.Image,
        output_path: str,
        format: str = "PNG"
    ) -> str:
        """Save rendered image to file."""
        path = Path(output_path)
        img.save(path, format=format, dpi=(self.config.dpi, self.config.dpi))
        return str(path)


def render_formula_demo(preset_id: str = "torres_diamond_7x9") -> Tuple[Image.Image, Image.Image]:
    """
    Demo function: render a preset as both strip and ring.

    Returns:
        Tuple of (strip_image, ring_image)
    """
    renderer = PatternRenderer()
    formula = PRESET_MATRICES[preset_id]

    strip = renderer.render_matrix_pattern(formula, show_labels=True)
    ring = renderer.render_rosette_ring(formula, num_repeats=4)

    return strip, ring


if __name__ == "__main__":
    # Demo: render Torres diamond pattern
    print("Rendering Torres Diamond pattern...")

    renderer = PatternRenderer(RenderConfig(
        image_size=800,
        add_border_lines=True,
    ))

    # Render as ring
    ring_img = renderer.render_preset("torres_diamond_7x9", as_ring=True, num_repeats=4)
    ring_img.save("torres_diamond_ring_render.png")
    print("Saved: torres_diamond_ring_render.png")

    # Render as strip (shows matrix structure)
    strip_img = renderer.render_preset("torres_diamond_7x9", as_ring=False)
    strip_img.save("torres_diamond_strip_render.png")
    print("Saved: torres_diamond_strip_render.png")

    print("\nThese renders show the ACTUAL formula geometry, not AI interpretation.")
