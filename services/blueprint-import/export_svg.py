"""
SVG Export for Phase 3.7 Vectorizer
====================================

Exports classified contours to SVG with color-coded layers.
Ported from vectorizer_phase2._export_svg_with_layers() and adapted
for Phase 3.6 ContourCategory/ContourInfo data model.

Requires: svgwrite>=1.4.0 (already in requirements.txt)
"""
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import cv2

try:
    import svgwrite
    SVGWRITE_AVAILABLE = True
except ImportError:
    SVGWRITE_AVAILABLE = False

logger = logging.getLogger(__name__)

# SVG layer colors matching DXF layer convention
LAYER_COLORS = {
    'BODY_OUTLINE':     '#FF0000',  # Red
    'PICKGUARD':        '#FFFF00',  # Yellow
    'NECK_POCKET':      '#00FF00',  # Green
    'PICKUP_ROUTE':     '#00FFFF',  # Cyan
    'CONTROL_CAVITY':   '#0000FF',  # Blue
    'BRIDGE_ROUTE':     '#FF00FF',  # Magenta
    'JACK_ROUTE':       '#FFFFFF',  # White
    'RHYTHM_CIRCUIT':   '#808080',  # Gray
    'SOUNDHOLE':        '#FF0000',  # Red
    'D_HOLE':           '#FF0000',  # Red
    'F_HOLE':           '#FF0000',  # Red
    'ROSETTE':          '#FFFF00',  # Yellow
    'BRACING':          '#00FF00',  # Green
    'SMALL_FEATURE':    '#C0C0C0',  # Silver
}

DEFAULT_COLOR = '#FF6600'  # Orange for unknown layers


def export_to_svg(
    classified: dict,
    output_path: str,
    image_height: int,
    mm_per_px: float,
    center_on_body: bool = True,
    simplify_tolerance: float = 0.2,
    excluded_categories: Optional[list] = None,
    max_per_category: Optional[dict] = None,
    scale_factor: float = 1.0
) -> Tuple[float, float]:
    """
    Export classified contours to SVG with semantic layers.

    Mirrors export_to_dxf() signature for consistency.

    Args:
        classified: Dict of category -> contour list
        output_path: Output SVG path
        image_height: Source image height in pixels
        mm_per_px: Pixels to mm conversion
        center_on_body: If True, center all geometry on body outline
        simplify_tolerance: Douglas-Peucker tolerance in mm
        excluded_categories: Categories to skip
        max_per_category: Max contours per category
        scale_factor: Scale multiplier (from calibration)

    Returns:
        Tuple of (body_width_mm, body_height_mm)
    """
    if not SVGWRITE_AVAILABLE:
        raise ImportError("svgwrite is required for SVG export. Install with: pip install svgwrite")

    # Import ContourCategory for exclusion defaults
    try:
        from vectorizer_phase3 import ContourCategory
        if excluded_categories is None:
            excluded_categories = [
                ContourCategory.TEXT,
                ContourCategory.PAGE_BORDER,
                ContourCategory.UNKNOWN
            ]
    except ImportError:
        if excluded_categories is None:
            excluded_categories = []

    if max_per_category is None:
        max_per_category = {}

    # Compute body center and dimensions
    center_x, center_y = 0.0, 0.0
    body_width, body_height = 0.0, 0.0

    # Find body outline for centering
    body_key = None
    for cat in classified:
        cat_val = cat.value if hasattr(cat, 'value') else str(cat)
        if cat_val == 'body_outline':
            body_key = cat
            break

    if center_on_body and body_key and classified[body_key]:
        body = classified[body_key][0]
        pts = body.contour.reshape(-1, 2)
        xs = [p[0] * mm_per_px * scale_factor for p in pts]
        ys = [(image_height - p[1]) * mm_per_px * scale_factor for p in pts]
        center_x = (min(xs) + max(xs)) / 2
        center_y = (min(ys) + max(ys)) / 2
        body_width = max(xs) - min(xs)
        body_height = max(ys) - min(ys)

    # Collect all geometry to determine SVG canvas bounds
    all_points = []
    contour_data = []  # (layer_name, point_tuples)

    for category, contours in classified.items():
        if category in excluded_categories:
            continue

        cat_val = category.value if hasattr(category, 'value') else str(category)
        layer_name = cat_val.upper()
        max_count = max_per_category.get(category, 10)

        for i, info in enumerate(contours[:max_count]):
            pts = info.contour.reshape(-1, 2)
            mm_pts = []
            for px, py in pts:
                x_mm = px * mm_per_px * scale_factor - center_x
                y_mm = (image_height - py) * mm_per_px * scale_factor - center_y
                mm_pts.append([x_mm, y_mm])

            pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
            simplified = cv2.approxPolyDP(pts_array, simplify_tolerance, closed=True)
            simplified = simplified.reshape(-1, 2)

            if len(simplified) < 3:
                continue

            point_tuples = [(float(x), float(y)) for x, y in simplified]
            contour_data.append((layer_name, point_tuples))
            all_points.extend(point_tuples)

    if not all_points:
        logger.warning("No geometry to export to SVG")
        return body_width, body_height

    # Compute canvas bounds
    all_np = np.array(all_points)
    x_min, y_min = all_np.min(axis=0)
    x_max, y_max = all_np.max(axis=0)
    margin = 10.0
    svg_width = (x_max - x_min) + 2 * margin
    svg_height = (y_max - y_min) + 2 * margin
    offset_x = margin - x_min
    offset_y = margin - y_min

    # Create SVG document
    dwg = svgwrite.Drawing(
        output_path,
        size=(f"{svg_width:.1f}mm", f"{svg_height:.1f}mm"),
        viewBox=f"0 0 {svg_width:.1f} {svg_height:.1f}"
    )

    # Draw contours per layer
    exported_count = 0
    for layer_name, point_tuples in contour_data:
        color = LAYER_COLORS.get(layer_name, DEFAULT_COLOR)

        # Build SVG path data (M/L/Z)
        pts = [(x + offset_x, y + offset_y) for x, y in point_tuples]
        path_d = f"M {pts[0][0]:.2f},{pts[0][1]:.2f} "
        for x, y in pts[1:]:
            path_d += f"L {x:.2f},{y:.2f} "
        path_d += "Z"

        dwg.add(dwg.path(
            d=path_d,
            stroke=color,
            stroke_width=0.5,
            fill="none",
            id=f"{layer_name}_{exported_count}"
        ))
        exported_count += 1

    dwg.save()
    logger.info(f"Exported {exported_count} contours to SVG: {output_path}")
    return body_width, body_height
