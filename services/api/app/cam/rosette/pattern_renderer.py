"""SVG and DXF R12 rendering for modern rosette pattern paths.

Also provides PatternRenderer class for generating PIL Image previews
of traditional matrix-based rosette patterns.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .pattern_schemas import PathSegment

if TYPE_CHECKING:
    from PIL import Image as PILImage

# Lazy PIL import — only load when rendering is requested
_PIL_AVAILABLE: Optional[bool] = None


def _get_pil():
    """Lazy-load PIL and return (Image, ImageDraw) modules."""
    global _PIL_AVAILABLE
    if _PIL_AVAILABLE is False:
        raise ImportError("PIL/Pillow is required for pattern rendering")
    try:
        from PIL import Image, ImageDraw
        _PIL_AVAILABLE = True
        return Image, ImageDraw
    except ImportError:
        _PIL_AVAILABLE = False
        raise ImportError("PIL/Pillow is required for pattern rendering")


# ============================================================================
# RENDER CONFIG
# ============================================================================

@dataclass
class RenderConfig:
    """Configuration for pattern rendering."""

    size: int = 512
    background_color: Tuple[int, int, int] = (255, 255, 255)
    line_color: Tuple[int, int, int] = (0, 0, 0)
    line_width: float = 1.0
    dpi: int = 96
    material_colors: Dict[str, Tuple[int, int, int]] = field(default_factory=lambda: {
        "black": (30, 30, 30),
        "white": (245, 240, 230),
        "brown": (139, 90, 43),
        "natural": (210, 180, 140),
        "red": (180, 50, 30),
        "green": (50, 130, 60),
        "blue": (40, 80, 160),
        # Wood species aliases
        "ebony": (30, 30, 30),
        "holly": (245, 240, 230),
        "maple": (240, 225, 200),
        "rosewood": (101, 67, 33),
        "walnut": (90, 60, 40),
        "padauk": (170, 60, 30),
        "purpleheart": (100, 50, 100),
        "mahogany": (120, 60, 40),
        "cherry": (150, 80, 60),
        "spruce": (235, 225, 200),
        "boxwood": (220, 200, 150),
        "wenge": (50, 40, 35),
        "dyed_black": (20, 20, 20),
        "dyed_red": (160, 30, 30),
        "dyed_green": (30, 100, 40),
        "dyed_blue": (30, 60, 140),
    })

    def get_color(self, material: str) -> Tuple[int, int, int]:
        """Get RGB color for a material, with fallback."""
        material_lower = material.lower().replace(" ", "_")
        if material_lower in self.material_colors:
            return self.material_colors[material_lower]
        # Fallback: hash-based color for unknown materials
        h = hash(material_lower) % 360
        # HSV to RGB (simplified, S=0.6, V=0.7)
        c = 0.42  # 0.6 * 0.7
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = 0.28  # 0.7 - c
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


# ============================================================================
# PATTERN RENDERER CLASS
# ============================================================================

class PatternRenderer:
    """
    Renders traditional matrix-based rosette patterns to PIL Images.

    Supports two visualization modes:
    - Strip view (default): Shows the assembled pattern as a flat ribbon
    - Ring view: Shows the pattern bent into a circular rosette ring
    """

    def __init__(self, config: Optional[RenderConfig] = None):
        """
        Initialize renderer with optional configuration.

        Args:
            config: RenderConfig instance, or None for defaults
        """
        self.config = config or RenderConfig()

    def render_preset(
        self,
        pattern_id: str,
        as_ring: bool = False,
        num_repeats: int = 4,
        size: int = 512,
    ) -> "PILImage.Image":
        """
        Render a preset pattern by ID.

        Args:
            pattern_id: Key from PRESET_MATRICES (e.g., "torres_diamond_7x9")
            as_ring: If True, render as circular ring; if False, as flat strip
            num_repeats: Number of pattern repeats around ring (only if as_ring=True)
            size: Output image size in pixels (width for strip, diameter for ring)

        Returns:
            PIL Image showing the pattern visualization

        Raises:
            ValueError: If pattern_id is not found in presets
            ImportError: If PIL/Pillow is not available
        """
        from .presets import PRESET_MATRICES

        if pattern_id not in PRESET_MATRICES:
            raise ValueError(f"Unknown pattern preset: {pattern_id}")

        formula = PRESET_MATRICES[pattern_id]
        return self.render_pattern(formula, as_ring=as_ring, num_repeats=num_repeats, size=size)

    def render_pattern(
        self,
        formula,  # MatrixFormula, but avoid circular import
        as_ring: bool = False,
        num_repeats: int = 4,
        size: int = 512,
    ) -> "PILImage.Image":
        """
        Render a MatrixFormula pattern.

        Args:
            formula: MatrixFormula instance defining the pattern
            as_ring: If True, render as circular ring; if False, as flat strip
            num_repeats: Number of pattern repeats around ring (only if as_ring=True)
            size: Output image size in pixels

        Returns:
            PIL Image showing the pattern visualization
        """
        if as_ring:
            return self._render_ring(formula, num_repeats, size)
        else:
            return self._render_strip(formula, size)

    def _render_strip(self, formula, size: int) -> "PILImage.Image":
        """Render pattern as a flat horizontal strip."""
        Image, ImageDraw = _get_pil()

        # Calculate grid dimensions
        num_cols = len(formula.column_sequence)
        num_rows = max(sum(row.values()) for row in formula.rows)

        # Compute cell size to fit within requested size
        # Strip is wider than tall typically
        aspect = num_cols / num_rows if num_rows > 0 else 1
        if aspect > 1:
            width = size
            height = max(int(size / aspect), 50)
        else:
            height = size
            width = max(int(size * aspect), 50)

        cell_w = width / num_cols
        cell_h = height / num_rows

        # Create image
        img = Image.new("RGB", (width, height), self.config.background_color)
        draw = ImageDraw.Draw(img)

        # Draw each column (chip) based on column_sequence
        for col_idx, row_ref in enumerate(formula.column_sequence):
            row_data = formula.rows[row_ref - 1]  # column_sequence is 1-indexed

            # Build the vertical stack of strips for this chip
            strips = []
            for material, count in row_data.items():
                for _ in range(count):
                    strips.append(material)

            # Draw each strip in the column
            x0 = col_idx * cell_w
            x1 = x0 + cell_w
            for strip_idx, material in enumerate(strips):
                y0 = strip_idx * cell_h
                y1 = y0 + cell_h
                color = self.config.get_color(material)
                draw.rectangle([x0, y0, x1, y1], fill=color)

        # Draw grid lines
        line_color = self.config.line_color
        line_width = max(1, int(self.config.line_width))

        # Vertical lines (between columns)
        for col_idx in range(num_cols + 1):
            x = col_idx * cell_w
            draw.line([(x, 0), (x, height)], fill=line_color, width=line_width)

        # Horizontal lines (between strips)
        for row_idx in range(num_rows + 1):
            y = row_idx * cell_h
            draw.line([(0, y), (width, y)], fill=line_color, width=line_width)

        return img

    def _render_ring(self, formula, num_repeats: int, size: int) -> "PILImage.Image":
        """Render pattern as a circular ring around a soundhole."""
        Image, ImageDraw = _get_pil()

        # Create square image
        img = Image.new("RGB", (size, size), self.config.background_color)
        draw = ImageDraw.Draw(img)

        center_x = size / 2
        center_y = size / 2

        # Ring dimensions (as fractions of image size)
        outer_radius = size * 0.45
        inner_radius = size * 0.30
        ring_width = outer_radius - inner_radius

        # Calculate pattern dimensions
        num_cols = len(formula.column_sequence)
        num_rows = max(sum(row.values()) for row in formula.rows)

        if num_cols == 0 or num_rows == 0:
            return img

        # Total chips around the ring
        total_chips = num_cols * num_repeats
        angle_per_chip = 2 * math.pi / total_chips

        # Height of each strip within the ring
        strip_height = ring_width / num_rows

        # Draw each chip around the ring
        for repeat in range(num_repeats):
            for col_idx, row_ref in enumerate(formula.column_sequence):
                chip_idx = repeat * num_cols + col_idx
                start_angle = chip_idx * angle_per_chip
                end_angle = start_angle + angle_per_chip

                row_data = formula.rows[row_ref - 1]

                # Build strip stack for this chip
                strips = []
                for material, count in row_data.items():
                    for _ in range(count):
                        strips.append(material)

                # Draw each strip as an arc segment
                for strip_idx, material in enumerate(strips):
                    r_inner = inner_radius + strip_idx * strip_height
                    r_outer = r_inner + strip_height
                    color = self.config.get_color(material)

                    # Draw filled arc segment (polygon approximation)
                    self._draw_arc_segment(
                        draw, center_x, center_y,
                        r_inner, r_outer,
                        start_angle, end_angle,
                        color
                    )

        # Draw ring outlines
        line_color = self.config.line_color
        line_width = max(1, int(self.config.line_width))

        # Inner circle
        draw.ellipse(
            [center_x - inner_radius, center_y - inner_radius,
             center_x + inner_radius, center_y + inner_radius],
            outline=line_color, width=line_width
        )
        # Outer circle
        draw.ellipse(
            [center_x - outer_radius, center_y - outer_radius,
             center_x + outer_radius, center_y + outer_radius],
            outline=line_color, width=line_width
        )

        return img

    def _draw_arc_segment(
        self,
        draw,
        cx: float, cy: float,
        r_inner: float, r_outer: float,
        angle_start: float, angle_end: float,
        color: Tuple[int, int, int],
        steps: int = 8
    ):
        """Draw a filled arc segment (wedge between two radii)."""
        # Build polygon points: outer arc, then inner arc reversed
        points = []

        # Outer arc (from start to end)
        for i in range(steps + 1):
            t = i / steps
            angle = angle_start + t * (angle_end - angle_start)
            x = cx + r_outer * math.cos(angle)
            y = cy + r_outer * math.sin(angle)
            points.append((x, y))

        # Inner arc (from end back to start)
        for i in range(steps, -1, -1):
            t = i / steps
            angle = angle_start + t * (angle_end - angle_start)
            x = cx + r_inner * math.cos(angle)
            y = cy + r_inner * math.sin(angle)
            points.append((x, y))

        draw.polygon(points, fill=color)


# ============================================================================
# PATH EXPORT FUNCTIONS (preserved from original)
# ============================================================================

def export_paths_to_dxf(paths: List[PathSegment]) -> str:
    """Export paths to DXF R12 format."""
    lines = []
    lines.extend([
        "0", "SECTION",
        "2", "HEADER",
        "9", "$ACADVER",
        "1", "AC1009",
        "9", "$INSUNITS",
        "70", "4",
        "0", "ENDSEC",
    ])
    lines.extend(["0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER"])
    layers = set(p.layer for p in paths)
    for layer in layers:
        lines.extend(
            ["0", "LAYER", "2", layer, "70", "0", "62", "7", "6", "CONTINUOUS"]
        )
    lines.extend(["0", "ENDTAB", "0", "ENDSEC"])
    lines.extend(["0", "SECTION", "2", "ENTITIES"])

    for path in paths:
        if len(path.points) < 2:
            continue
        if path.is_closed and len(path.points) >= 3:
            lines.extend(
                ["0", "POLYLINE", "8", path.layer, "66", "1", "70", "1"]
            )
            for pt in path.points:
                lines.extend([
                    "0", "VERTEX",
                    "8", path.layer,
                    "10", f"{pt.x:.6f}",
                    "20", f"{pt.y:.6f}",
                ])
            lines.extend(["0", "SEQEND"])
        else:
            for i in range(len(path.points) - 1):
                p1, p2 = path.points[i], path.points[i + 1]
                lines.extend([
                    "0", "LINE",
                    "8", path.layer,
                    "10", f"{p1.x:.6f}",
                    "20", f"{p1.y:.6f}",
                    "11", f"{p2.x:.6f}",
                    "21", f"{p2.y:.6f}",
                ])
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(lines)


def export_paths_to_svg(
    paths: List[PathSegment],
    title: str = "Rosette Pattern",
) -> str:
    """Export paths to SVG format."""
    all_x = [p.x for path in paths for p in path.points]
    all_y = [p.y for path in paths for p in path.points]
    if not all_x:
        min_x, max_x, min_y, max_y = -50, 50, -50, 50
    else:
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
    padding = 5
    width = max_x - min_x + 2 * padding
    height = max_y - min_y + 2 * padding

    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" ',
        f'     viewBox="{min_x - padding} {min_y - padding} {width} {height}"',
        f'     width="{width}mm" height="{height}mm">',
        f"  <title>{title}</title>",
        "  <desc>Generated by The Production Shop</desc>",
    ]
    for path in paths:
        if len(path.points) < 2:
            continue
        points_str = " ".join(f"{p.x:.3f},{p.y:.3f}" for p in path.points)
        if path.is_closed:
            svg_lines.append(
                f'  <polygon points="{points_str}" '
                f'fill="none" stroke="{path.color}" stroke-width="0.2"/>'
            )
        else:
            svg_lines.append(
                f'  <polyline points="{points_str}" '
                f'fill="none" stroke="{path.color}" stroke-width="0.2"/>'
            )
    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


__all__ = [
    "export_paths_to_dxf",
    "export_paths_to_svg",
    "PatternRenderer",
    "RenderConfig",
]
