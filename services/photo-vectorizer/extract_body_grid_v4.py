"""
extract_body_grid_v4.py — Clean Body Outline (Fixed Soundhole Handling)
=======================================================================

Key fix: Fill internal holes BEFORE applying the body mask cutoff,
so the soundhole doesn't create a notch at the waist.
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

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

    return binary


def fill_all_holes(binary: np.ndarray) -> np.ndarray:
    """Fill ALL internal holes using flood fill from borders."""
    padded = cv2.copyMakeBorder(binary, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    h, w = padded.shape
    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    cv2.floodFill(padded, flood_mask, (0, 0), 255)
    inverted = cv2.bitwise_not(padded)
    filled = cv2.bitwise_or(binary, inverted[1:-1, 1:-1])
    return filled


def find_guitar_contour(binary: np.ndarray) -> tuple:
    """Find the guitar contour and bounding box."""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None
    largest = max(contours, key=cv2.contourArea)
    bbox = cv2.boundingRect(largest)
    return largest, bbox


def extract_body_from_filled_guitar(
    filled: np.ndarray,
    guitar_contour: np.ndarray,
    guitar_bbox: tuple,
    neck_cutoff: float = 0.42
) -> np.ndarray:
    """
    Cut the body from the filled guitar silhouette.

    For horizontal guitar (neck on right):
    - Keep left portion (body)
    - Cut right portion (neck)
    - Close the cut edge with a straight line
    """
    gx, gy, gw, gh = guitar_bbox
    is_horizontal = gw > gh

    h, w = filled.shape

    if is_horizontal:
        # Cut at neck_cutoff from left
        cut_x = int(gx + gw * neck_cutoff)

        # Create body mask
        body_mask = np.zeros((h, w), dtype=np.uint8)
        body_mask[:, :cut_x] = 255

        # Apply mask
        body = cv2.bitwise_and(filled, filled, mask=body_mask)

        # Find the cut edge points on the guitar contour
        points = guitar_contour.reshape(-1, 2)
        # Points near the cut line
        near_cut = np.abs(points[:, 0] - cut_x) < 30
        if np.any(near_cut):
            cut_points = points[near_cut]
            top_y = np.min(cut_points[:, 1])
            bot_y = np.max(cut_points[:, 1])

            # Draw a vertical line to close the body at the neck joint
            cv2.line(body, (cut_x, top_y), (cut_x, bot_y), 255, 3)

            # Fill any remaining gaps with morphological close
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            body = cv2.morphologyEx(body, cv2.MORPH_CLOSE, kernel)

    else:
        # Vertical: cut at top
        cut_y = int(gy + gh * (1.0 - neck_cutoff))
        body_mask = np.zeros((h, w), dtype=np.uint8)
        body_mask[cut_y:, :] = 255
        body = cv2.bitwise_and(filled, filled, mask=body_mask)

    return body


def extract_outer_contour(binary: np.ndarray) -> np.ndarray:
    """Extract the outer boundary contour."""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def smooth_contour(contour: np.ndarray, iterations: int = 2) -> np.ndarray:
    """Smooth contour via blur and re-extract."""
    x, y, w, h = cv2.boundingRect(contour)
    pad = 20
    mask = np.zeros((h + 2*pad, w + 2*pad), dtype=np.uint8)

    shifted = contour.copy()
    shifted[:, :, 0] -= (x - pad)
    shifted[:, :, 1] -= (y - pad)
    cv2.drawContours(mask, [shifted], -1, 255, -1)

    for _ in range(iterations):
        mask = cv2.GaussianBlur(mask, (7, 7), 0)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return contour

    smoothed = max(contours, key=cv2.contourArea)
    smoothed[:, :, 0] += (x - pad)
    smoothed[:, :, 1] += (y - pad)
    return smoothed


def simplify_contour(contour: np.ndarray, target_points: int = 40) -> np.ndarray:
    """Simplify contour to ~target_points vertices."""
    perimeter = cv2.arcLength(contour, closed=True)
    lo, hi = 0.0001, 0.05
    best = contour

    for _ in range(20):
        mid = (lo + hi) / 2
        simplified = cv2.approxPolyDP(contour, mid * perimeter, closed=True)
        n = len(simplified)

        if abs(n - target_points) < abs(len(best) - target_points):
            best = simplified

        if n > target_points:
            lo = mid
        else:
            hi = mid

        if abs(n - target_points) < 3:
            break

    return best


def contour_to_dxf(contour: np.ndarray, output_path: Path,
                   target_height_mm: float = 470.0) -> dict:
    """Export to DXF R12 with LINE entities."""
    points = contour.reshape(-1, 2).astype(float)

    y_range = np.max(points[:, 1]) - np.min(points[:, 1])
    x_range = np.max(points[:, 0]) - np.min(points[:, 0])
    mm_per_px = target_height_mm / y_range if y_range > 0 else 1.0

    points_mm = points * mm_per_px
    points_mm[:, 1] = -points_mm[:, 1]
    points_mm -= np.mean(points_mm, axis=0)

    doc = ezdxf.new('R12')
    msp = doc.modelspace()
    doc.layers.add('BODY', color=7)

    n = len(points_mm)
    for i in range(n):
        p1, p2 = points_mm[i], points_mm[(i + 1) % n]
        msp.add_line(
            start=(float(p1[0]), float(p1[1])),
            end=(float(p2[0]), float(p2[1])),
            dxfattribs={'layer': 'BODY'}
        )

    doc.saveas(str(output_path))

    return {
        "points": n,
        "width_mm": x_range * mm_per_px,
        "height_mm": y_range * mm_per_px,
        "scale": mm_per_px
    }


def process_guitar_image(
    image_path: str,
    output_dir: str,
    neck_cutoff: float = 0.42,
    target_height_mm: float = 470.0,
    target_points: int = 40,
    debug: bool = True
) -> dict:
    """
    Process guitar image to extract clean body outline.

    Key improvement: Fill holes BEFORE cutting to avoid soundhole notch.
    """
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load: {image_path}")

    h, w = image.shape[:2]
    logger.info(f"Image: {w}x{h}")

    # Step 1: Binary threshold
    binary = extract_guitar_foreground(image)
    if debug:
        cv2.imwrite(str(output_dir / "01_binary.png"), binary)

    # Step 2: Fill ALL holes FIRST (including soundhole)
    filled_guitar = fill_all_holes(binary)
    if debug:
        cv2.imwrite(str(output_dir / "02_filled_guitar.png"), filled_guitar)

    # Step 3: Find guitar contour from filled silhouette
    guitar_contour, guitar_bbox = find_guitar_contour(filled_guitar)
    if guitar_contour is None:
        raise ValueError("No guitar found")

    gx, gy, gw, gh = guitar_bbox
    is_horiz = gw > gh
    logger.info(f"Guitar: {gw}x{gh} {'HORIZONTAL' if is_horiz else 'VERTICAL'}")

    # Step 4: Extract body portion from filled guitar
    body = extract_body_from_filled_guitar(
        filled_guitar, guitar_contour, guitar_bbox, neck_cutoff
    )
    if debug:
        cv2.imwrite(str(output_dir / "03_body.png"), body)

    # Step 5: Extract outer contour
    body_contour = extract_outer_contour(body)
    if body_contour is None:
        raise ValueError("Could not extract body contour")

    logger.info(f"Raw contour: {len(body_contour)} points")

    # Step 6: Smooth
    smoothed = smooth_contour(body_contour, iterations=3)
    logger.info(f"Smoothed: {len(smoothed)} points")

    # Step 7: Simplify
    simplified = simplify_contour(smoothed, target_points)
    logger.info(f"Simplified: {len(simplified)} points")

    # Debug overlay
    if debug:
        debug_img = image.copy()
        cv2.rectangle(debug_img, (gx, gy), (gx+gw, gy+gh), (0, 255, 0), 2)

        if is_horiz:
            cut_x = int(gx + gw * neck_cutoff)
            cv2.line(debug_img, (cut_x, gy), (cut_x, gy+gh), (0, 0, 255), 2)
            cv2.putText(debug_img, "BODY", (gx+20, gy+gh//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(debug_img, "NECK", (cut_x+20, gy+gh//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.drawContours(debug_img, [simplified], -1, (255, 0, 255), 3)
        cv2.imwrite(str(output_dir / "04_result.png"), debug_img)

    # Step 8: Export DXF
    dxf_path = output_dir / f"{image_path.stem}_body_v4.dxf"
    dxf_info = contour_to_dxf(simplified, dxf_path, target_height_mm)

    logger.info(f"DXF: {dxf_path}")
    logger.info(f"  Dimensions: {dxf_info['width_mm']:.1f}mm x {dxf_info['height_mm']:.1f}mm")

    return {
        "dxf_path": str(dxf_path),
        "dimensions_mm": (dxf_info['width_mm'], dxf_info['height_mm']),
        "points": dxf_info['points'],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_body_grid_v4.py <image> [output_dir] [neck_cutoff]")
        sys.exit(1)

    result = process_guitar_image(
        image_path=sys.argv[1],
        output_dir=sys.argv[2] if len(sys.argv) > 2 else "./live_test_output/grid_v4",
        neck_cutoff=float(sys.argv[3]) if len(sys.argv) > 3 else 0.42,
        target_height_mm=470.0,
        target_points=40,
        debug=True
    )

    print("\nResult:")
    for k, v in result.items():
        print(f"  {k}: {v}")
