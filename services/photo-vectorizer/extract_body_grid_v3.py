"""
extract_body_grid_v3.py — Clean Body Outline Extraction
========================================================

Refined version that:
1. Extracts guitar silhouette
2. Masks to body region only (excludes neck)
3. Fills ALL internal holes (soundhole, bridge, frets)
4. Produces clean outer boundary only
"""

import cv2
import numpy as np
import ezdxf
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def extract_guitar_foreground(image: np.ndarray) -> np.ndarray:
    """Extract guitar silhouette from dark background."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Aggressive closing to connect fragmented areas
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

    return binary


def find_guitar_bbox(binary: np.ndarray) -> tuple:
    """Find bounding box of the largest connected component."""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    return cv2.boundingRect(largest)


def is_horizontal_orientation(bbox: tuple) -> bool:
    """Determine if guitar is horizontal (wider than tall)."""
    _, _, w, h = bbox
    return w > h


def create_body_mask_horizontal(shape: tuple, guitar_bbox: tuple,
                                 neck_cutoff: float = 0.52) -> np.ndarray:
    """Create mask for horizontal guitar body (left portion)."""
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    gx, gy, gw, gh = guitar_bbox
    body_end_x = int(gx + gw * neck_cutoff)
    mask[gy:gy+gh, gx:body_end_x] = 255
    return mask


def fill_holes_morphological(binary: np.ndarray) -> np.ndarray:
    """Fill ALL holes in binary image using flood fill from borders."""
    # Pad image to allow flood fill from edges
    padded = cv2.copyMakeBorder(binary, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)

    # Flood fill from top-left corner (outside the object)
    h, w = padded.shape
    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    cv2.floodFill(padded, flood_mask, (0, 0), 255)

    # Invert: now holes are white, object is black
    inverted = cv2.bitwise_not(padded)

    # OR with original: object + holes = solid object
    filled = cv2.bitwise_or(binary, inverted[1:-1, 1:-1])

    return filled


def extract_outer_contour(filled: np.ndarray) -> np.ndarray:
    """Extract just the outer boundary contour."""
    contours, hierarchy = cv2.findContours(
        filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def smooth_contour(contour: np.ndarray, iterations: int = 2) -> np.ndarray:
    """Smooth contour by drawing and re-extracting with blur."""
    # Get bounding box
    x, y, w, h = cv2.boundingRect(contour)
    padding = 20

    # Create a mask with some padding
    mask = np.zeros((h + 2*padding, w + 2*padding), dtype=np.uint8)

    # Shift contour to local coordinates
    shifted = contour.copy()
    shifted[:, :, 0] -= (x - padding)
    shifted[:, :, 1] -= (y - padding)

    # Draw filled contour
    cv2.drawContours(mask, [shifted], -1, 255, -1)

    # Apply Gaussian blur to smooth edges
    for _ in range(iterations):
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    # Extract smoothed contour
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return contour

    smoothed = max(contours, key=cv2.contourArea)

    # Shift back to original coordinates
    smoothed[:, :, 0] += (x - padding)
    smoothed[:, :, 1] += (y - padding)

    return smoothed


def simplify_contour(contour: np.ndarray, target_points: int = 40) -> np.ndarray:
    """Simplify contour to approximately target_points vertices."""
    perimeter = cv2.arcLength(contour, closed=True)

    # Binary search for epsilon that gives ~target_points
    lo, hi = 0.0001, 0.05
    best = contour
    best_diff = float('inf')

    for _ in range(20):
        mid = (lo + hi) / 2
        epsilon = mid * perimeter
        simplified = cv2.approxPolyDP(contour, epsilon, closed=True)
        n = len(simplified)

        diff = abs(n - target_points)
        if diff < best_diff:
            best_diff = diff
            best = simplified

        if n > target_points:
            lo = mid
        else:
            hi = mid

        if diff < 3:
            break

    return best


def contour_to_dxf(contour: np.ndarray, output_path: Path,
                   target_height_mm: float = 470.0) -> dict:
    """Export contour to DXF R12 with LINE entities."""
    points = contour.reshape(-1, 2).astype(float)

    # Calculate scale based on height
    y_range = np.max(points[:, 1]) - np.min(points[:, 1])
    x_range = np.max(points[:, 0]) - np.min(points[:, 0])
    mm_per_px = target_height_mm / y_range if y_range > 0 else 1.0

    # Convert to mm
    points_mm = points * mm_per_px

    # Flip Y for CAD
    points_mm[:, 1] = -points_mm[:, 1]

    # Center on origin
    center = np.mean(points_mm, axis=0)
    points_mm -= center

    # Create DXF
    doc = ezdxf.new('R12')
    msp = doc.modelspace()
    doc.layers.add('BODY', color=7)

    n = len(points_mm)
    for i in range(n):
        p1 = points_mm[i]
        p2 = points_mm[(i + 1) % n]
        msp.add_line(
            start=(float(p1[0]), float(p1[1])),
            end=(float(p2[0]), float(p2[1])),
            dxfattribs={'layer': 'BODY'}
        )

    doc.saveas(str(output_path))

    width_mm = x_range * mm_per_px
    height_mm = y_range * mm_per_px

    return {
        "points": n,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "scale": mm_per_px
    }


def process_gibson_l1(
    image_path: str,
    output_dir: str,
    neck_cutoff: float = 0.52,
    target_height_mm: float = 470.0,
    target_points: int = 40,
    debug: bool = True
) -> dict:
    """Process Gibson L-1 AI image to extract clean body outline."""

    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load: {image_path}")

    h, w = image.shape[:2]
    logger.info(f"Image: {w}x{h}")

    # Step 1: Binary threshold
    binary = extract_guitar_foreground(image)
    if debug:
        cv2.imwrite(str(output_dir / "01_binary.png"), binary)

    # Step 2: Find guitar bbox (full guitar)
    guitar_bbox = find_guitar_bbox(binary)
    if guitar_bbox is None:
        raise ValueError("No guitar found")

    gx, gy, gw, gh = guitar_bbox
    is_horiz = is_horizontal_orientation(guitar_bbox)
    logger.info(f"Guitar: {gw}x{gh} at ({gx},{gy}) {'HORIZONTAL' if is_horiz else 'VERTICAL'}")

    # Step 3: Create body mask
    if is_horiz:
        body_mask = create_body_mask_horizontal(image.shape, guitar_bbox, neck_cutoff)
    else:
        # Vertical: exclude top portion
        body_mask = np.zeros((h, w), dtype=np.uint8)
        body_start_y = int(gy + gh * (1.0 - neck_cutoff))
        body_mask[body_start_y:gy+gh, gx:gx+gw] = 255

    if debug:
        cv2.imwrite(str(output_dir / "02_body_mask.png"), body_mask)

    # Step 4: Apply mask to get body region only
    body_binary = cv2.bitwise_and(binary, binary, mask=body_mask)
    if debug:
        cv2.imwrite(str(output_dir / "03_body_binary.png"), body_binary)

    # Step 5: Fill ALL internal holes
    body_filled = fill_holes_morphological(body_binary)
    if debug:
        cv2.imwrite(str(output_dir / "04_body_filled.png"), body_filled)

    # Step 6: Extract outer contour
    outer_contour = extract_outer_contour(body_filled)
    if outer_contour is None:
        raise ValueError("Could not extract outer contour")

    logger.info(f"Raw contour: {len(outer_contour)} points")

    # Step 7: Smooth
    smoothed = smooth_contour(outer_contour, iterations=3)
    logger.info(f"Smoothed: {len(smoothed)} points")

    # Step 8: Simplify
    simplified = simplify_contour(smoothed, target_points=target_points)
    logger.info(f"Simplified: {len(simplified)} points")

    # Debug overlay
    if debug:
        debug_img = image.copy()

        # Guitar bbox
        cv2.rectangle(debug_img, (gx, gy), (gx+gw, gy+gh), (0, 255, 0), 2)

        # Cutoff line
        if is_horiz:
            cut_x = int(gx + gw * neck_cutoff)
            cv2.line(debug_img, (cut_x, gy), (cut_x, gy+gh), (0, 0, 255), 2)
            cv2.putText(debug_img, "BODY", (gx+20, gy+gh//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(debug_img, "NECK", (cut_x+20, gy+gh//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # Body outline
        cv2.drawContours(debug_img, [simplified], -1, (255, 0, 255), 3)

        cv2.imwrite(str(output_dir / "05_result_overlay.png"), debug_img)

    # Step 9: Export DXF
    dxf_path = output_dir / f"{image_path.stem}_body_v3.dxf"
    dxf_info = contour_to_dxf(simplified, dxf_path, target_height_mm)

    logger.info(f"DXF: {dxf_path}")
    logger.info(f"  Dimensions: {dxf_info['width_mm']:.1f}mm x {dxf_info['height_mm']:.1f}mm")
    logger.info(f"  Points: {dxf_info['points']}")

    return {
        "dxf_path": str(dxf_path),
        "dimensions_mm": (dxf_info['width_mm'], dxf_info['height_mm']),
        "points": dxf_info['points'],
        "scale_mm_per_px": dxf_info['scale'],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_body_grid_v3.py <image> [output_dir] [neck_cutoff]")
        sys.exit(1)

    result = process_gibson_l1(
        image_path=sys.argv[1],
        output_dir=sys.argv[2] if len(sys.argv) > 2 else "./live_test_output/grid_v3",
        neck_cutoff=float(sys.argv[3]) if len(sys.argv) > 3 else 0.52,
        target_height_mm=470.0,
        target_points=40,
        debug=True
    )

    print("\nResult:")
    for k, v in result.items():
        print(f"  {k}: {v}")
