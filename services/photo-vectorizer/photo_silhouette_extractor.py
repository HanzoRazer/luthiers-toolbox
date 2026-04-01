"""
Photo Silhouette Extractor

Extract guitar body outlines from photographs by:
1. Edge detection to find the perimeter
2. Flood fill from corners to identify background
3. Invert to get guitar silhouette mask
4. Extract and simplify outer contour

Works well with:
- Studio photos with dark/gradient backgrounds
- AI-generated guitar images
- Product photos with clean backgrounds

Contrast with light_line_body_extractor.py which is for blueprint PDFs.
"""
from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SilhouetteConfig:
    """Configuration for photo silhouette extraction."""
    # Edge detection
    blur_kernel: int = 5
    canny_low: int = 30
    canny_high: int = 100

    # Morphological operations
    close_kernel: int = 5
    close_iterations: int = 3

    # Flood fill
    fill_tolerance: int = 30  # How similar colors must be to fill

    # Body filtering (as fraction of image dimensions)
    min_width_ratio: float = 0.25
    max_width_ratio: float = 0.85
    min_height_ratio: float = 0.30
    max_height_ratio: float = 0.90

    # Region of interest (body only, exclude neck/headstock)
    body_top_ratio: float = 0.35  # Start from 35% down (skip neck)
    body_bottom_ratio: float = 1.0

    # Contour simplification
    simplify_epsilon: float = 0.002

    # Output scaling (mm)
    target_width_mm: Optional[float] = None
    target_height_mm: Optional[float] = None


@dataclass
class SilhouetteResult:
    """Result of silhouette extraction."""
    success: bool
    contour: Optional[np.ndarray] = None
    bbox_px: Tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h
    points: int = 0
    debug_images: Dict[str, np.ndarray] = field(default_factory=dict)
    error_message: str = ""


def extract_silhouette(
    image: np.ndarray,
    config: Optional[SilhouetteConfig] = None,
    save_debug: bool = False,
) -> SilhouetteResult:
    """
    Extract guitar body silhouette from a photograph.

    Args:
        image: BGR image array
        config: Extraction configuration
        save_debug: Include debug images in result

    Returns:
        SilhouetteResult with contour and metadata
    """
    if config is None:
        config = SilhouetteConfig()

    result = SilhouetteResult(success=False)
    debug = {}

    h, w = image.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (config.blur_kernel, config.blur_kernel), 0)

    if save_debug:
        debug['01_gray'] = gray.copy()

    # Edge detection
    edges = cv2.Canny(blurred, config.canny_low, config.canny_high)

    if save_debug:
        debug['02_edges'] = edges.copy()

    # Close gaps in edges
    kernel = np.ones((config.close_kernel, config.close_kernel), np.uint8)
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=config.close_iterations)

    if save_debug:
        debug['03_closed'] = closed.copy()

    # Create mask and flood fill from corners (background)
    # Add 1px border for flood fill to work from edges
    mask = np.zeros((h + 2, w + 2), np.uint8)
    filled = closed.copy()

    # Flood fill from all four corners
    corners = [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]
    for cx, cy in corners:
        if filled[cy, cx] == 0:  # Only fill if corner is not an edge
            cv2.floodFill(
                filled, mask,
                (cx, cy),
                255,
                loDiff=config.fill_tolerance,
                upDiff=config.fill_tolerance,
            )

    if save_debug:
        debug['04_flood_filled'] = filled.copy()

    # Invert - guitar is now white, background black
    guitar_mask = cv2.bitwise_not(filled)

    # Clean up the mask
    guitar_mask = cv2.morphologyEx(guitar_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    guitar_mask = cv2.morphologyEx(guitar_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    if save_debug:
        debug['05_guitar_mask'] = guitar_mask.copy()

    # Find contours
    contours, _ = cv2.findContours(guitar_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        result.error_message = "No contours found"
        result.debug_images = debug if save_debug else {}
        return result

    # Filter for body-sized contours
    candidates = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 10000:
            continue

        x, y, cw, ch = cv2.boundingRect(cnt)
        w_ratio = cw / w
        h_ratio = ch / h

        if not (config.min_width_ratio < w_ratio < config.max_width_ratio):
            continue
        if not (config.min_height_ratio < h_ratio < config.max_height_ratio):
            continue

        candidates.append({
            'contour': cnt,
            'area': area,
            'bbox': (x, y, cw, ch),
        })

    if not candidates:
        result.error_message = "No body-sized contours found"
        result.debug_images = debug if save_debug else {}
        return result

    # Take largest candidate
    best = max(candidates, key=lambda c: c['area'])
    cnt = best['contour']

    # Crop to body region (exclude neck/headstock)
    x, y, cw, ch = best['bbox']
    body_top_y = int(h * config.body_top_ratio)

    # Filter points to body region only
    body_points = []
    for pt in cnt.reshape(-1, 2):
        if pt[1] >= body_top_y:
            body_points.append(pt)

    if len(body_points) < 10:
        # If filtering removed too many points, use full contour
        body_points = cnt.reshape(-1, 2)

    body_contour = np.array(body_points).reshape(-1, 1, 2)

    # Simplify
    epsilon = config.simplify_epsilon * cv2.arcLength(body_contour, True)
    simplified = cv2.approxPolyDP(body_contour, epsilon, True)

    # Get final bbox
    x, y, cw, ch = cv2.boundingRect(simplified)

    result.success = True
    result.contour = simplified.reshape(-1, 2)
    result.bbox_px = (x, y, cw, ch)
    result.points = len(simplified)

    if save_debug:
        # Create visualization
        vis = image.copy()
        cv2.drawContours(vis, [simplified], -1, (0, 255, 0), 3)
        cv2.rectangle(vis, (x, y), (x + cw, y + ch), (0, 0, 255), 2)
        cv2.putText(vis, f'{cw}x{ch}px, {len(simplified)} pts',
                    (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        debug['06_result'] = vis
        result.debug_images = debug

    return result


def extract_body_only(
    image: np.ndarray,
    config: Optional[SilhouetteConfig] = None,
    save_debug: bool = False,
) -> SilhouetteResult:
    """
    Extract just the guitar body (no neck/headstock) from a photograph.

    Uses convex hull analysis to find the body region and crops appropriately.
    """
    if config is None:
        config = SilhouetteConfig()

    # First get full silhouette
    full_result = extract_silhouette(image, config, save_debug=True)

    if not full_result.success:
        return full_result

    h, w = image.shape[:2]
    contour = full_result.contour

    # Analyze vertical distribution of points
    # Body has more points at bottom, neck is narrow at top
    y_coords = contour[:, 1]

    # Find where the contour widens (body starts)
    # Split into horizontal slices and measure width
    num_slices = 20
    slice_height = h // num_slices
    widths = []

    for i in range(num_slices):
        y_min = i * slice_height
        y_max = (i + 1) * slice_height

        # Points in this slice
        mask = (y_coords >= y_min) & (y_coords < y_max)
        slice_points = contour[mask]

        if len(slice_points) > 1:
            x_min = slice_points[:, 0].min()
            x_max = slice_points[:, 0].max()
            widths.append((i, x_max - x_min, (y_min + y_max) // 2))
        else:
            widths.append((i, 0, (y_min + y_max) // 2))

    # Find where width increases significantly (body start)
    # Body is typically 3-4x wider than neck
    max_width = max(w[1] for w in widths)
    body_threshold = max_width * 0.5

    body_start_y = 0
    for i, width, y_center in widths:
        if width > body_threshold:
            body_start_y = y_center
            break

    # Filter contour to body region
    body_mask = contour[:, 1] >= body_start_y
    body_points = contour[body_mask]

    if len(body_points) < 20:
        # Fallback to original
        body_points = contour

    # Create closed body contour
    body_contour = body_points.reshape(-1, 1, 2)

    # Simplify
    epsilon = config.simplify_epsilon * cv2.arcLength(body_contour, True)
    simplified = cv2.approxPolyDP(body_contour, epsilon, True)

    x, y, cw, ch = cv2.boundingRect(simplified)

    result = SilhouetteResult(
        success=True,
        contour=simplified.reshape(-1, 2),
        bbox_px=(x, y, cw, ch),
        points=len(simplified),
    )

    if save_debug:
        debug = full_result.debug_images.copy()
        vis = image.copy()
        cv2.drawContours(vis, [simplified], -1, (0, 255, 0), 3)
        cv2.rectangle(vis, (x, y), (x + cw, y + ch), (0, 0, 255), 2)
        cv2.line(vis, (0, body_start_y), (w, body_start_y), (255, 0, 0), 2)
        cv2.putText(vis, f'Body: {cw}x{ch}px', (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        debug['07_body_only'] = vis
        result.debug_images = debug

    return result


def scale_contour_to_mm(
    contour: np.ndarray,
    current_width_px: float,
    current_height_px: float,
    target_width_mm: float,
    target_height_mm: float,
) -> np.ndarray:
    """Scale contour from pixels to target mm dimensions."""
    # Calculate scale factors
    scale_x = target_width_mm / current_width_px
    scale_y = target_height_mm / current_height_px

    # Center the contour
    cx = contour[:, 0].mean()
    cy = contour[:, 1].mean()

    # Scale around center
    scaled = contour.astype(float).copy()
    scaled[:, 0] = (scaled[:, 0] - cx) * scale_x
    scaled[:, 1] = (scaled[:, 1] - cy) * scale_y

    return scaled


def save_to_dxf(
    contour_mm: np.ndarray,
    output_path: Path,
    layer_name: str = "BODY_OUTLINE",
) -> None:
    """Save mm-scaled contour to DXF."""
    import ezdxf

    doc = ezdxf.new('R2010')
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    doc.layers.add(layer_name, color=7)

    # Create closed polyline
    points_3d = [(p[0], p[1], 0.0) for p in contour_mm]
    points_3d.append(points_3d[0])  # Close

    msp.add_lwpolyline(points_3d, dxfattribs={'layer': layer_name})

    doc.saveas(str(output_path))
    logger.info(f"Saved DXF to {output_path}")


# Convenience function for common use case
def extract_guitar_body_from_photo(
    image_path: Path,
    target_width_mm: float = 477.0,
    target_height_mm: float = 522.0,
    output_dxf: Optional[Path] = None,
    save_debug: bool = False,
) -> SilhouetteResult:
    """
    One-shot extraction of guitar body from photo to DXF.

    Args:
        image_path: Path to photo
        target_width_mm: Target body width (default: jumbo 477mm)
        target_height_mm: Target body height (default: jumbo 522mm)
        output_dxf: Optional DXF output path
        save_debug: Save debug images alongside input

    Returns:
        SilhouetteResult
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return SilhouetteResult(success=False, error_message=f"Could not load {image_path}")

    config = SilhouetteConfig()
    result = extract_body_only(img, config, save_debug=save_debug)

    if not result.success:
        return result

    # Scale to mm
    x, y, cw, ch = result.bbox_px
    contour_mm = scale_contour_to_mm(
        result.contour,
        cw, ch,
        target_width_mm, target_height_mm
    )

    # Save debug images
    if save_debug and result.debug_images:
        debug_dir = image_path.parent / "debug"
        debug_dir.mkdir(exist_ok=True)
        for name, img_data in result.debug_images.items():
            cv2.imwrite(str(debug_dir / f"{name}.png"), img_data)

    # Save DXF
    if output_dxf:
        save_to_dxf(contour_mm, output_dxf)

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract guitar body from photo")
    parser.add_argument("image", type=Path, help="Input image")
    parser.add_argument("--output", type=Path, help="Output DXF")
    parser.add_argument("--width", type=float, default=477.0, help="Target width (mm)")
    parser.add_argument("--height", type=float, default=522.0, help="Target height (mm)")
    parser.add_argument("--debug", action="store_true", help="Save debug images")

    args = parser.parse_args()

    result = extract_guitar_body_from_photo(
        args.image,
        target_width_mm=args.width,
        target_height_mm=args.height,
        output_dxf=args.output,
        save_debug=args.debug,
    )

    if result.success:
        x, y, w, h = result.bbox_px
        print(f"Extracted body: {w}x{h} px, {result.points} points")
        if args.output:
            print(f"Saved to {args.output}")
    else:
        print(f"Failed: {result.error_message}")
