"""
extract_body_grid.py — Grid-Based Body Extraction for AI Images
================================================================

Uses the 3x3 grid zone concept to isolate the guitar body from neck/headstock.

Strategy:
1. Detect the full guitar silhouette (foreground vs background)
2. Find the guitar's bounding box
3. Create a zone mask that EXCLUDES upper zones (UL/UC/UR = neck/headstock)
4. Extract body outline from middle+lower zones only (ML/MC/MR, LL/LC/LR)

This approach works because:
- AI images have clean backgrounds (easy foreground detection)
- Guitar orientation is consistent (neck at top)
- Grid zones provide semantic meaning to spatial regions
"""

import cv2
import numpy as np
import ezdxf
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def extract_guitar_foreground(image: np.ndarray) -> np.ndarray:
    """Extract guitar silhouette from dark background using thresholding."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # For AI images with dark background, the guitar is brighter
    # Use Otsu's method to find optimal threshold
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Clean up with morphology
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    return binary


def find_guitar_bbox(binary: np.ndarray) -> tuple:
    """Find bounding box of the largest connected component (guitar)."""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Get largest contour
    largest = max(contours, key=cv2.contourArea)
    return cv2.boundingRect(largest)


def create_body_zone_mask(shape: tuple, guitar_bbox: tuple,
                          upper_cutoff: float = 0.33) -> np.ndarray:
    """
    Create a mask that EXCLUDES the upper zone (neck/headstock).

    Parameters:
        shape: (height, width) of the image
        guitar_bbox: (x, y, w, h) of the guitar bounding box
        upper_cutoff: Fraction of guitar height to exclude (default 0.33 = upper third)

    Returns:
        Binary mask where body region = 255, neck region = 0
    """
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    gx, gy, gw, gh = guitar_bbox

    # The body region starts after the upper cutoff
    # Upper zones (UL/UC/UR) = neck/headstock = EXCLUDE
    # Middle + Lower zones = body = INCLUDE
    body_start_y = int(gy + gh * upper_cutoff)
    body_end_y = gy + gh

    # Fill the body region
    mask[body_start_y:body_end_y, gx:gx+gw] = 255

    return mask


def extract_body_contour(binary: np.ndarray, body_mask: np.ndarray) -> np.ndarray:
    """
    Extract the body outline by masking the guitar silhouette with body zones.
    """
    # Apply body zone mask to the binary image
    body_only = cv2.bitwise_and(binary, binary, mask=body_mask)

    # Find contours in the masked region
    contours, _ = cv2.findContours(body_only, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # Get largest contour (should be the body)
    body_contour = max(contours, key=cv2.contourArea)

    return body_contour


def close_body_top(contour: np.ndarray, guitar_bbox: tuple,
                   upper_cutoff: float = 0.33) -> np.ndarray:
    """
    Close the top of the body where it was cut from the neck.

    The cut creates an open edge at the neck joint. We need to:
    1. Find the two endpoints at the top of the body region
    2. Connect them with a straight line (simplified neck pocket)
    """
    gx, gy, gw, gh = guitar_bbox
    cut_y = int(gy + gh * upper_cutoff)

    # Find points near the cut line
    points = contour.reshape(-1, 2)

    # Points near the top cut (within 20 pixels)
    top_indices = np.where(np.abs(points[:, 1] - cut_y) < 20)[0]

    if len(top_indices) < 2:
        # No modification needed, contour is already closed
        return contour

    # Get the leftmost and rightmost points near the cut
    top_points = points[top_indices]
    left_point = top_points[np.argmin(top_points[:, 0])]
    right_point = top_points[np.argmax(top_points[:, 0])]

    # The contour is already closed by OpenCV, just return it
    return contour


def simplify_contour(contour: np.ndarray, epsilon_ratio: float = 0.001) -> np.ndarray:
    """Simplify contour using Douglas-Peucker algorithm."""
    perimeter = cv2.arcLength(contour, closed=True)
    epsilon = epsilon_ratio * perimeter
    simplified = cv2.approxPolyDP(contour, epsilon, closed=True)
    return simplified


def contour_to_dxf(contour: np.ndarray, output_path: Path,
                   mm_per_px: float = 1.0, target_height_mm: float = None) -> None:
    """
    Export contour to DXF file using R12 format with LINE entities only.

    Parameters:
        contour: OpenCV contour array
        output_path: Path for DXF output
        mm_per_px: Conversion factor from pixels to mm
        target_height_mm: If provided, scale to this target height
    """
    points = contour.reshape(-1, 2)

    # Calculate actual scale if target height is provided
    if target_height_mm:
        y_coords = points[:, 1]
        px_height = np.max(y_coords) - np.min(y_coords)
        if px_height > 0:
            mm_per_px = target_height_mm / px_height

    # Convert to mm and flip Y (OpenCV Y is inverted)
    points_mm = points.astype(float) * mm_per_px
    points_mm[:, 1] = -points_mm[:, 1]  # Flip Y

    # Center on origin
    center = np.mean(points_mm, axis=0)
    points_mm -= center

    # Create DXF
    doc = ezdxf.new('R12')
    msp = doc.modelspace()

    # Add layer
    doc.layers.add('BODY', color=7)

    # Add LINE entities (closed polyline)
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
    logger.info(f"DXF saved: {output_path} ({n} points, {n} LINE entities)")


def process_ai_guitar_image(
    image_path: str,
    output_dir: str,
    upper_cutoff: float = 0.33,
    target_height_mm: float = 470.0,  # Gibson L-1 body height
    debug: bool = True
) -> dict:
    """
    Process an AI-generated guitar image to extract body outline.

    Parameters:
        image_path: Path to input image
        output_dir: Directory for outputs
        upper_cutoff: Fraction of guitar to exclude as neck (0.33 = upper third)
        target_height_mm: Target body height in mm for scaling
        debug: Save debug images

    Returns:
        Dict with results and file paths
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

    # Step 1: Extract guitar foreground
    binary = extract_guitar_foreground(image)
    if debug:
        cv2.imwrite(str(output_dir / "01_binary.png"), binary)

    # Step 2: Find guitar bounding box
    guitar_bbox = find_guitar_bbox(binary)
    if guitar_bbox is None:
        raise ValueError("Could not find guitar in image")

    gx, gy, gw, gh = guitar_bbox
    logger.info(f"Guitar bbox: x={gx}, y={gy}, w={gw}, h={gh}")

    # Step 3: Create body zone mask (exclude upper zones)
    body_mask = create_body_zone_mask(image.shape, guitar_bbox, upper_cutoff)
    if debug:
        cv2.imwrite(str(output_dir / "02_body_mask.png"), body_mask)

    # Step 4: Extract body contour
    body_contour = extract_body_contour(binary, body_mask)
    if body_contour is None:
        raise ValueError("Could not extract body contour")

    logger.info(f"Body contour: {len(body_contour)} points")

    # Step 5: Close the top (neck joint region)
    body_contour = close_body_top(body_contour, guitar_bbox, upper_cutoff)

    # Step 6: Simplify contour
    simplified = simplify_contour(body_contour, epsilon_ratio=0.002)
    logger.info(f"Simplified: {len(simplified)} points")

    # Debug: Draw grid overlay
    if debug:
        debug_img = image.copy()

        # Draw guitar bbox
        cv2.rectangle(debug_img, (gx, gy), (gx+gw, gy+gh), (0, 255, 0), 2)

        # Draw grid lines
        for i in range(1, 3):
            # Horizontal lines (zone boundaries)
            y = int(gy + gh * i / 3)
            cv2.line(debug_img, (gx, y), (gx+gw, y), (0, 255, 0), 1)

            # Vertical lines
            x = int(gx + gw * i / 3)
            cv2.line(debug_img, (x, gy), (x, gy+gh), (0, 255, 0), 1)

        # Draw zone labels
        zones = [
            ("UL", 0, 0), ("UC", 1, 0), ("UR", 2, 0),
            ("ML", 0, 1), ("MC", 1, 1), ("MR", 2, 1),
            ("LL", 0, 2), ("LC", 1, 2), ("LR", 2, 2),
        ]
        for name, col, row in zones:
            zx = int(gx + gw * (col + 0.5) / 3)
            zy = int(gy + gh * (row + 0.5) / 3)
            cv2.putText(debug_img, name, (zx-10, zy),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Draw cutoff line (body/neck boundary)
        cut_y = int(gy + gh * upper_cutoff)
        cv2.line(debug_img, (gx, cut_y), (gx+gw, cut_y), (0, 0, 255), 2)
        cv2.putText(debug_img, "BODY CUTOFF", (gx+5, cut_y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Draw extracted body contour
        cv2.drawContours(debug_img, [simplified], -1, (255, 0, 255), 2)

        cv2.imwrite(str(output_dir / "03_grid_overlay.png"), debug_img)

    # Step 7: Export to DXF
    dxf_path = output_dir / f"{image_path.stem}_body.dxf"
    contour_to_dxf(simplified, dxf_path, target_height_mm=target_height_mm)

    # Calculate dimensions
    points = simplified.reshape(-1, 2)
    px_width = np.max(points[:, 0]) - np.min(points[:, 0])
    px_height = np.max(points[:, 1]) - np.min(points[:, 1])

    # Scale factor used
    scale = target_height_mm / px_height if px_height > 0 else 1.0

    result = {
        "image_path": str(image_path),
        "dxf_path": str(dxf_path),
        "guitar_bbox_px": guitar_bbox,
        "body_points": len(simplified),
        "px_dimensions": (px_width, px_height),
        "mm_dimensions": (px_width * scale, px_height * scale),
        "scale_mm_per_px": scale,
        "upper_cutoff": upper_cutoff,
    }

    logger.info(f"Body dimensions: {px_width * scale:.0f}mm x {px_height * scale:.0f}mm")

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_body_grid.py <image_path> [output_dir] [upper_cutoff]")
        print("\nExample:")
        print("  python extract_body_grid.py guitar.png ./output 0.35")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./live_test_output/grid_extract"
    upper_cutoff = float(sys.argv[3]) if len(sys.argv) > 3 else 0.33

    result = process_ai_guitar_image(
        image_path=image_path,
        output_dir=output_dir,
        upper_cutoff=upper_cutoff,
        target_height_mm=470.0,  # Gibson L-1
        debug=True
    )

    print(f"\nResult:")
    for k, v in result.items():
        print(f"  {k}: {v}")
