"""
extract_body_grid_v5.py — Final Clean Body Outline Extraction
==============================================================

Uses aggressive morphological closing to fill the soundhole,
then extracts the body outline.
"""

import cv2
import numpy as np
import ezdxf
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def extract_guitar_foreground(image: np.ndarray) -> np.ndarray:
    """Extract guitar silhouette."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def fill_soundhole_morph(binary: np.ndarray, soundhole_radius_px: int = 60) -> np.ndarray:
    """
    Fill the soundhole using morphological close with large kernel.

    The soundhole on a guitar is roughly circular and ~100mm diameter.
    In the image, estimate ~80-120 pixels diameter.
    """
    # Use a circular kernel slightly larger than the soundhole
    kernel_size = soundhole_radius_px * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

    # Close (dilate then erode) - fills gaps smaller than kernel
    filled = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return filled


def find_guitar_bbox(binary: np.ndarray) -> tuple:
    """Find guitar bounding box."""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    return cv2.boundingRect(largest)


def extract_body_region(
    filled: np.ndarray,
    guitar_bbox: tuple,
    neck_cutoff: float = 0.42
) -> np.ndarray:
    """Extract body region (left portion for horizontal guitar)."""
    gx, gy, gw, gh = guitar_bbox
    is_horizontal = gw > gh

    h, w = filled.shape

    if is_horizontal:
        cut_x = int(gx + gw * neck_cutoff)
        body_mask = np.zeros((h, w), dtype=np.uint8)
        body_mask[:, :cut_x] = 255
    else:
        cut_y = int(gy + gh * (1.0 - neck_cutoff))
        body_mask = np.zeros((h, w), dtype=np.uint8)
        body_mask[cut_y:, :] = 255

    body = cv2.bitwise_and(filled, filled, mask=body_mask)
    return body


def extract_and_smooth_contour(binary: np.ndarray, smooth_iter: int = 3) -> np.ndarray:
    """Extract and smooth the outer contour."""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)

    # Smooth via blur and re-extract
    x, y, w, h = cv2.boundingRect(largest)
    pad = 30
    mask = np.zeros((h + 2*pad, w + 2*pad), dtype=np.uint8)

    shifted = largest.copy()
    shifted[:, :, 0] -= (x - pad)
    shifted[:, :, 1] -= (y - pad)
    cv2.drawContours(mask, [shifted], -1, 255, -1)

    for _ in range(smooth_iter):
        mask = cv2.GaussianBlur(mask, (9, 9), 0)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return largest

    smoothed = max(contours, key=cv2.contourArea)
    smoothed[:, :, 0] += (x - pad)
    smoothed[:, :, 1] += (y - pad)

    return smoothed


def simplify_contour(contour: np.ndarray, target_points: int = 50) -> np.ndarray:
    """Simplify to target point count."""
    perimeter = cv2.arcLength(contour, closed=True)
    lo, hi = 0.0001, 0.03
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

        if abs(n - target_points) < 5:
            break

    return best


def contour_to_dxf(contour: np.ndarray, output_path: Path,
                   target_height_mm: float = 470.0) -> dict:
    """Export to DXF R12."""
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
    }


def process_guitar(
    image_path: str,
    output_dir: str,
    neck_cutoff: float = 0.40,
    soundhole_radius_px: int = 70,
    target_height_mm: float = 470.0,
    target_points: int = 50,
    debug: bool = True
) -> dict:
    """Process guitar image to extract clean body outline."""

    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load: {image_path}")

    h, w = image.shape[:2]
    logger.info(f"Image: {w}x{h}")

    # Step 1: Threshold
    binary = extract_guitar_foreground(image)
    if debug:
        cv2.imwrite(str(output_dir / "01_binary.png"), binary)

    # Step 2: Fill soundhole with large morphological close
    filled = fill_soundhole_morph(binary, soundhole_radius_px)
    if debug:
        cv2.imwrite(str(output_dir / "02_filled.png"), filled)

    # Step 3: Find guitar bbox
    guitar_bbox = find_guitar_bbox(filled)
    if guitar_bbox is None:
        raise ValueError("No guitar found")

    gx, gy, gw, gh = guitar_bbox
    is_horiz = gw > gh
    logger.info(f"Guitar: {gw}x{gh} {'HORIZONTAL' if is_horiz else 'VERTICAL'}")

    # Step 4: Extract body region
    body = extract_body_region(filled, guitar_bbox, neck_cutoff)
    if debug:
        cv2.imwrite(str(output_dir / "03_body.png"), body)

    # Step 5: Extract and smooth contour
    smoothed = extract_and_smooth_contour(body, smooth_iter=4)
    if smoothed is None:
        raise ValueError("No contour found")

    logger.info(f"Smoothed contour: {len(smoothed)} points")

    # Step 6: Simplify
    simplified = simplify_contour(smoothed, target_points)
    logger.info(f"Simplified: {len(simplified)} points")

    # Debug overlay
    if debug:
        debug_img = image.copy()
        cv2.rectangle(debug_img, (gx, gy), (gx+gw, gy+gh), (0, 255, 0), 2)

        if is_horiz:
            cut_x = int(gx + gw * neck_cutoff)
            cv2.line(debug_img, (cut_x, gy), (cut_x, gy+gh), (0, 0, 255), 2)

        cv2.drawContours(debug_img, [simplified], -1, (255, 0, 255), 3)
        cv2.imwrite(str(output_dir / "04_result.png"), debug_img)

    # Step 7: Export DXF
    dxf_path = output_dir / f"{image_path.stem}_body_v5.dxf"
    dxf_info = contour_to_dxf(simplified, dxf_path, target_height_mm)

    logger.info(f"DXF: {dxf_path}")
    logger.info(f"  Dimensions: {dxf_info['width_mm']:.1f}mm x {dxf_info['height_mm']:.1f}mm")
    logger.info(f"  Points: {dxf_info['points']}")

    return {
        "dxf_path": str(dxf_path),
        "dimensions_mm": (dxf_info['width_mm'], dxf_info['height_mm']),
        "points": dxf_info['points'],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_body_grid_v5.py <image> [output_dir] [neck_cutoff]")
        print("  neck_cutoff: 0.40 = keep left 40% as body (default)")
        sys.exit(1)

    result = process_guitar(
        image_path=sys.argv[1],
        output_dir=sys.argv[2] if len(sys.argv) > 2 else "./live_test_output/grid_v5",
        neck_cutoff=float(sys.argv[3]) if len(sys.argv) > 3 else 0.40,
        soundhole_radius_px=70,
        target_height_mm=470.0,
        target_points=50,
        debug=True
    )

    print("\nResult:")
    for k, v in result.items():
        print(f"  {k}: {v}")
