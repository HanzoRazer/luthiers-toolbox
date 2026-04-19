"""
extract_body_grid_v2.py — Grid-Based Body Extraction (Horizontal Orientation)
==============================================================================

For guitars photographed/rendered horizontally (neck on right, body on left).

Strategy:
1. Detect the full guitar silhouette
2. Determine orientation (horizontal vs vertical)
3. Create zone mask excluding the neck region (RIGHT side for horizontal)
4. Extract body from left/center zones
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

    # Use adaptive threshold for better handling of gradients
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

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


def create_body_zone_mask_horizontal(
    shape: tuple,
    guitar_bbox: tuple,
    neck_cutoff: float = 0.55  # Right 45% is neck, left 55% is body
) -> np.ndarray:
    """
    Create mask for horizontal guitar (neck on RIGHT).

    For a typical guitar photographed from the front with neck on right:
    - Left portion (0% - 55%) = BODY = INCLUDE
    - Right portion (55% - 100%) = NECK = EXCLUDE
    """
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    gx, gy, gw, gh = guitar_bbox

    # Body is on the LEFT side
    body_end_x = int(gx + gw * neck_cutoff)

    # Fill the body region (full height, left portion width)
    mask[gy:gy+gh, gx:body_end_x] = 255

    return mask


def create_body_zone_mask_vertical(
    shape: tuple,
    guitar_bbox: tuple,
    neck_cutoff: float = 0.35
) -> np.ndarray:
    """
    Create mask for vertical guitar (neck on TOP).

    - Upper portion (0% - 35%) = NECK = EXCLUDE
    - Lower portion (35% - 100%) = BODY = INCLUDE
    """
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    gx, gy, gw, gh = guitar_bbox

    body_start_y = int(gy + gh * neck_cutoff)

    mask[body_start_y:gy+gh, gx:gx+gw] = 255

    return mask


def extract_body_contour(binary: np.ndarray, body_mask: np.ndarray) -> np.ndarray:
    """Extract body outline from masked region."""
    body_only = cv2.bitwise_and(binary, binary, mask=body_mask)

    contours, _ = cv2.findContours(body_only, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Get largest contour
    body_contour = max(contours, key=cv2.contourArea)
    return body_contour


def fill_internal_holes(contour: np.ndarray, shape: tuple) -> np.ndarray:
    """Fill internal holes in the body (soundhole, frets captured, etc.)."""
    # Draw filled contour on a blank mask
    mask = np.zeros(shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)  # -1 = filled

    # Find external contour of the filled shape
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        return max(contours, key=cv2.contourArea)
    return contour


def simplify_contour(contour: np.ndarray, epsilon_ratio: float = 0.002) -> np.ndarray:
    """Simplify contour using Douglas-Peucker."""
    perimeter = cv2.arcLength(contour, closed=True)
    epsilon = epsilon_ratio * perimeter
    return cv2.approxPolyDP(contour, epsilon, closed=True)


def smooth_contour(contour: np.ndarray, window: int = 5) -> np.ndarray:
    """Apply moving average smoothing to contour points."""
    points = contour.reshape(-1, 2).astype(float)
    n = len(points)

    smoothed = np.zeros_like(points)
    for i in range(n):
        # Circular window
        indices = [(i + j - window//2) % n for j in range(window)]
        smoothed[i] = np.mean(points[indices], axis=0)

    return smoothed.astype(np.int32).reshape(-1, 1, 2)


def contour_to_dxf(contour: np.ndarray, output_path: Path,
                   target_height_mm: float = 470.0,
                   is_horizontal: bool = False) -> None:
    """
    Export contour to DXF with proper scaling.

    For horizontal guitars, use target_height_mm as the WIDTH dimension.
    """
    points = contour.reshape(-1, 2).astype(float)

    # Calculate scale
    x_range = np.max(points[:, 0]) - np.min(points[:, 0])
    y_range = np.max(points[:, 1]) - np.min(points[:, 1])

    if is_horizontal:
        # For horizontal, scale based on Y (which is the body height)
        mm_per_px = target_height_mm / y_range if y_range > 0 else 1.0
    else:
        # For vertical, scale based on Y
        mm_per_px = target_height_mm / y_range if y_range > 0 else 1.0

    # Convert to mm
    points_mm = points * mm_per_px

    # Flip Y for CAD convention
    points_mm[:, 1] = -points_mm[:, 1]

    # Center on origin
    center = np.mean(points_mm, axis=0)
    points_mm -= center

    # Create DXF R12
    doc = ezdxf.new('R12')
    msp = doc.modelspace()
    doc.layers.add('BODY', color=7)

    # Add LINE entities
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

    # Calculate final dimensions
    x_mm = x_range * mm_per_px
    y_mm = y_range * mm_per_px

    logger.info(f"DXF saved: {output_path}")
    logger.info(f"  Points: {n}, Scale: {mm_per_px:.4f} mm/px")
    logger.info(f"  Dimensions: {x_mm:.1f}mm x {y_mm:.1f}mm")


def process_ai_guitar_image(
    image_path: str,
    output_dir: str,
    neck_cutoff: float = 0.55,  # For horizontal: right portion to exclude
    target_height_mm: float = 470.0,
    debug: bool = True
) -> dict:
    """
    Process an AI-generated guitar image to extract body outline.
    Automatically detects orientation (horizontal vs vertical).
    """
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    h, w = image.shape[:2]
    logger.info(f"Image: {w}x{h}")

    # Step 1: Extract foreground
    binary = extract_guitar_foreground(image)
    if debug:
        cv2.imwrite(str(output_dir / "01_binary.png"), binary)

    # Step 2: Find guitar bbox
    guitar_bbox = find_guitar_bbox(binary)
    if guitar_bbox is None:
        raise ValueError("Could not find guitar in image")

    gx, gy, gw, gh = guitar_bbox
    is_horizontal = is_horizontal_orientation(guitar_bbox)

    orientation = "HORIZONTAL" if is_horizontal else "VERTICAL"
    logger.info(f"Guitar bbox: {gw}x{gh} at ({gx},{gy}) - {orientation}")

    # Step 3: Create body zone mask based on orientation
    if is_horizontal:
        body_mask = create_body_zone_mask_horizontal(image.shape, guitar_bbox, neck_cutoff)
    else:
        body_mask = create_body_zone_mask_vertical(image.shape, guitar_bbox, 1.0 - neck_cutoff)

    if debug:
        cv2.imwrite(str(output_dir / "02_body_mask.png"), body_mask)

    # Step 4: Extract body contour
    body_contour = extract_body_contour(binary, body_mask)
    if body_contour is None:
        raise ValueError("Could not extract body contour")

    logger.info(f"Body contour: {len(body_contour)} raw points")

    # Step 5: Fill internal holes
    body_contour = fill_internal_holes(body_contour, image.shape)
    logger.info(f"After hole fill: {len(body_contour)} points")

    # Step 6: Smooth and simplify
    body_contour = smooth_contour(body_contour, window=7)
    simplified = simplify_contour(body_contour, epsilon_ratio=0.003)
    logger.info(f"Simplified: {len(simplified)} points")

    # Debug visualization
    if debug:
        debug_img = image.copy()

        # Draw guitar bbox
        cv2.rectangle(debug_img, (gx, gy), (gx+gw, gy+gh), (0, 255, 0), 2)

        # Draw grid (3x3)
        for i in range(1, 3):
            if is_horizontal:
                x = int(gx + gw * i / 3)
                cv2.line(debug_img, (x, gy), (x, gy+gh), (0, 255, 0), 1)
                y = int(gy + gh * i / 3)
                cv2.line(debug_img, (gx, y), (gx+gw, y), (0, 255, 0), 1)
            else:
                y = int(gy + gh * i / 3)
                cv2.line(debug_img, (gx, y), (gx+gw, y), (0, 255, 0), 1)
                x = int(gx + gw * i / 3)
                cv2.line(debug_img, (x, gy), (x, gy+gh), (0, 255, 0), 1)

        # Draw cutoff line
        if is_horizontal:
            cut_x = int(gx + gw * neck_cutoff)
            cv2.line(debug_img, (cut_x, gy), (cut_x, gy+gh), (0, 0, 255), 2)
            cv2.putText(debug_img, "NECK CUTOFF", (cut_x+5, gy+20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(debug_img, "BODY", (gx+10, gy+gh//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(debug_img, "NECK", (cut_x+10, gy+gh//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            cut_y = int(gy + gh * (1.0 - neck_cutoff))
            cv2.line(debug_img, (gx, cut_y), (gx+gw, cut_y), (0, 0, 255), 2)
            cv2.putText(debug_img, "NECK", (gx+10, cut_y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Draw extracted contour
        cv2.drawContours(debug_img, [simplified], -1, (255, 0, 255), 2)

        cv2.imwrite(str(output_dir / "03_grid_overlay.png"), debug_img)

    # Step 7: Export DXF
    dxf_path = output_dir / f"{image_path.stem}_body_v2.dxf"
    contour_to_dxf(simplified, dxf_path,
                   target_height_mm=target_height_mm,
                   is_horizontal=is_horizontal)

    # Calculate dimensions
    points = simplified.reshape(-1, 2)
    px_width = np.max(points[:, 0]) - np.min(points[:, 0])
    px_height = np.max(points[:, 1]) - np.min(points[:, 1])

    # Scale based on height dimension
    scale = target_height_mm / px_height if px_height > 0 else 1.0

    result = {
        "image_path": str(image_path),
        "dxf_path": str(dxf_path),
        "orientation": orientation,
        "guitar_bbox_px": guitar_bbox,
        "body_points": len(simplified),
        "px_dimensions": (int(px_width), int(px_height)),
        "mm_dimensions": (px_width * scale, px_height * scale),
        "scale_mm_per_px": scale,
        "neck_cutoff": neck_cutoff,
    }

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_body_grid_v2.py <image_path> [output_dir] [neck_cutoff]")
        print("\nFor horizontal guitars (neck on right):")
        print("  neck_cutoff = 0.55 means right 45% is neck")
        print("\nExample:")
        print("  python extract_body_grid_v2.py guitar.png ./output 0.55")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./live_test_output/grid_v2"
    neck_cutoff = float(sys.argv[3]) if len(sys.argv) > 3 else 0.55

    result = process_ai_guitar_image(
        image_path=image_path,
        output_dir=output_dir,
        neck_cutoff=neck_cutoff,
        target_height_mm=470.0,  # Gibson L-1 body height
        debug=True
    )

    print(f"\nResult:")
    for k, v in result.items():
        print(f"  {k}: {v}")
