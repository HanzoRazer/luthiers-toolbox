#!/usr/bin/env python3
"""
Generate DXF files from Carlos Jumbo blueprints - ENHANCED EDGE DETECTION.

Uses multi-scale edge fusion and contrast enhancement to capture
light gray body outline lines that standard thresholding misses.

Now incorporates instrument spec database (carlos_jumbo.json) for accurate
scaling based on actual body dimensions (520mm length, 430mm width).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np


def load_carlos_jumbo_spec(repo_root: Path) -> dict:
    """Load Carlos Jumbo spec from instrument database."""
    spec_path = repo_root / "services" / "api" / "app" / "instrument_geometry" / "specs" / "carlos_jumbo.json"
    if spec_path.exists():
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# Default dimensions from 1:1 blueprint calibration (soundhole = 102mm reference)
# Volume validated: 14.65 liters (within jumbo range 14-19L)
CARLOS_JUMBO_BODY_LENGTH_MM = 522.0
CARLOS_JUMBO_BODY_WIDTH_MM = 477.0
CARLOS_JUMBO_LOWER_BOUT_MM = 477.0
CARLOS_JUMBO_UPPER_BOUT_MM = 372.0  # ratio 0.78 to lower bout
CARLOS_JUMBO_WAIST_MM = 324.0       # ratio 0.68 to lower bout

try:
    import fitz
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

from geometry_coach_v2 import GeometryCoachV2, CoachV2Config


def pdf_page_to_image(pdf_path: Path, page_num: int = 0, dpi: int = 300) -> np.ndarray:
    """Convert PDF to image at high DPI for detail."""
    doc = fitz.open(str(pdf_path))
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    doc.close()
    return img


def enhance_light_lines(gray: np.ndarray) -> np.ndarray:
    """
    Enhance light gray lines in blueprint images.

    Uses CLAHE and contrast stretching to make faint lines more visible.
    """
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Invert so lines become white on black (easier for edge detection)
    inverted = cv2.bitwise_not(enhanced)

    # Stretch contrast to full range
    min_val, max_val = inverted.min(), inverted.max()
    if max_val > min_val:
        stretched = ((inverted - min_val) * 255 / (max_val - min_val)).astype(np.uint8)
    else:
        stretched = inverted

    return stretched


def multi_scale_edge_detection(gray: np.ndarray) -> np.ndarray:
    """
    Multi-scale edge detection combining multiple Canny thresholds.

    Captures both strong dark lines and faint light lines.
    """
    # First enhance light lines
    enhanced = enhance_light_lines(gray)

    # Multi-scale Canny on enhanced image
    edge_levels = [
        (20, 60),    # Very sensitive - catches faint lines
        (30, 90),    # Sensitive
        (50, 150),   # Standard
        (80, 200),   # Strong edges only
    ]

    combined = np.zeros_like(gray)

    for low, high in edge_levels:
        # Apply slight blur before Canny
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        edges = cv2.Canny(blurred, low, high)
        combined = cv2.bitwise_or(combined, edges)

    # Also run on original (non-enhanced) for strong dark lines
    for low, high in [(30, 100), (50, 150)]:
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blurred, low, high)
        combined = cv2.bitwise_or(combined, edges)

    # Clean up with morphological operations
    kernel = np.ones((2, 2), np.uint8)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=1)

    return combined


def extract_contours_enhanced(image: np.ndarray, min_area_ratio: float = 0.01) -> list:
    """
    Extract contours using enhanced multi-scale edge detection.
    """
    h, w = image.shape[:2]
    total_area = h * w

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Get enhanced edges
    edges = multi_scale_edge_detection(gray)

    # Dilate slightly to connect nearby edges
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter by area
    significant = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area / total_area > min_area_ratio:
            # Simplify
            epsilon = 0.0005 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if len(approx) >= 3:
                significant.append(approx)

    # Sort by area
    significant.sort(key=lambda c: cv2.contourArea(c), reverse=True)

    return significant


def extract_all_edges_as_lines(image: np.ndarray) -> list:
    """
    Extract ALL edge pixels as polylines for maximum detail.

    This captures every visible line in the blueprint.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = multi_scale_edge_detection(gray)

    # Find contours from the edge image
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # Keep contours with at least 10 points
    polylines = [cnt for cnt in contours if len(cnt) >= 10]

    # Sort by length (perimeter)
    polylines.sort(key=lambda c: cv2.arcLength(c, False), reverse=True)

    return polylines


def calibrate_scale_from_soundhole(image: np.ndarray,
                                   soundhole_mm: float = 102.0) -> float | None:
    """
    Detect soundhole circle and calibrate mm/px scale.

    Returns mm_per_px or None if soundhole not detected.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Estimate expected soundhole radius from body proportions
    # Body ~520mm length, soundhole ~102mm diameter
    est_body_h_px = h * 0.65  # body occupies ~65% of height
    est_mm_per_px = 520.0 / est_body_h_px
    expected_sh_radius_px = (soundhole_mm / 2) / est_mm_per_px

    # Resize for faster HoughCircles (max 1500px width)
    scale = min(1.0, 1500 / w)
    if scale < 1.0:
        small = cv2.resize(image, (int(w * scale), int(h * scale)))
        small_gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    else:
        small_gray = gray
        scale = 1.0

    blurred = cv2.GaussianBlur(small_gray, (5, 5), 0)

    # Search for soundhole-sized circles
    min_radius = max(10, int(expected_sh_radius_px * scale * 0.6))
    max_radius = int(expected_sh_radius_px * scale * 1.5)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_radius * 3,
        param1=50,
        param2=30,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    if circles is None:
        return None

    # Find most centered circle (soundhole is typically centered)
    best_circle = None
    best_score = float('inf')
    center_x = small_gray.shape[1] / 2

    for cx, cy, r in circles[0]:
        dist_from_center = abs(cx - center_x)
        if dist_from_center < best_score:
            best_score = dist_from_center
            best_circle = (cx, cy, r)

    if best_circle is None:
        return None

    # Scale radius back to original image size
    _, _, r_scaled = best_circle
    r_original = r_scaled / scale
    diameter_px = r_original * 2

    # Calculate mm/px from soundhole reference
    mm_per_px = soundhole_mm / diameter_px
    return mm_per_px


def contours_to_mm(contours: list, image_height_px: int,
                   mm_per_px: float | None = None,
                   target_height_mm: float = 520.0) -> list:
    """Convert pixel coordinates to mm.

    Uses mm_per_px if provided (from calibration), otherwise estimates
    from target_height_mm.
    """
    if mm_per_px is None:
        mm_per_px = target_height_mm / image_height_px

    mm_contours = []
    for cnt in contours:
        pts = cnt.reshape(-1, 2).astype(float)
        pts[:, 0] *= mm_per_px
        pts[:, 1] = (image_height_px - pts[:, 1]) * mm_per_px
        mm_contours.append(pts)
    return mm_contours


def write_dxf_enhanced(contours_mm: list, output_path: str,
                       layer_name: str = "OUTLINE") -> bool:
    """Write contours to DXF with polylines."""
    try:
        doc = ezdxf.new("R12")
        msp = doc.modelspace()
        doc.header["$INSUNITS"] = 4
        doc.header["$MEASUREMENT"] = 1
        doc.layers.add(layer_name, color=7)

        for pts in contours_mm:
            if len(pts) < 3:
                continue
            pts_list = [(float(p[0]), float(p[1])) for p in pts]
            msp.add_lwpolyline(pts_list, dxfattribs={"layer": layer_name}, close=True)

        doc.saveas(output_path)
        return True
    except Exception as e:
        print(f"DXF error: {e}")
        return False


def write_dxf_all_lines(polylines_mm: list, output_path: str) -> bool:
    """Write all polylines to DXF (comprehensive output)."""
    try:
        doc = ezdxf.new("R12")
        msp = doc.modelspace()
        doc.header["$INSUNITS"] = 4
        doc.header["$MEASUREMENT"] = 1

        # Create layers by size
        doc.layers.add("MAJOR_LINES", color=7)  # White
        doc.layers.add("MINOR_LINES", color=8)  # Gray
        doc.layers.add("DETAIL_LINES", color=9)  # Light gray

        for idx, pts in enumerate(polylines_mm):
            if len(pts) < 2:
                continue

            pts_list = [(float(p[0]), float(p[1])) for p in pts]

            # Assign to layer based on size
            perimeter = sum(
                np.sqrt((pts_list[i][0] - pts_list[i-1][0])**2 +
                       (pts_list[i][1] - pts_list[i-1][1])**2)
                for i in range(1, len(pts_list))
            )

            if perimeter > 100:  # Major lines > 100mm
                layer = "MAJOR_LINES"
            elif perimeter > 20:  # Minor lines 20-100mm
                layer = "MINOR_LINES"
            else:  # Detail lines < 20mm
                layer = "DETAIL_LINES"

            # Don't close short lines
            close = len(pts_list) > 20 and perimeter > 50
            msp.add_lwpolyline(pts_list, dxfattribs={"layer": layer}, close=close)

        doc.saveas(output_path)
        return True
    except Exception as e:
        print(f"DXF error: {e}")
        return False


def generate_enhanced_dxfs():
    """Generate enhanced DXF files from Carlos Jumbo blueprints."""

    if not FITZ_AVAILABLE or not EZDXF_AVAILABLE:
        print("ERROR: Required packages missing")
        return

    repo_root = Path(__file__).parent.parent.parent
    jumbo_dir = repo_root / "Guitar Plans" / "Jumbo Carlos"

    if not jumbo_dir.exists():
        print(f"ERROR: Directory not found: {jumbo_dir}")
        return

    pdfs = sorted(jumbo_dir.glob("JUMBO-CARLOS-*.pdf"))
    if not pdfs:
        print(f"ERROR: No PDFs found")
        return

    print(f"Found {len(pdfs)} Carlos Jumbo PDFs")
    print("Using ENHANCED edge detection (multi-scale + contrast enhancement)")
    print("=" * 70)

    config = CoachV2Config(
        enable_multi_view_detection=True,
        multi_view_min_area_ratio=0.05,
    )
    coach = GeometryCoachV2(config)

    output_dir = Path(__file__).parent / "live_test_output" / "carlos_jumbo_dxf"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_dxfs = 0

    for pdf_path in pdfs:
        print(f"\n[PDF] {pdf_path.name}")
        print("-" * 50)

        try:
            # Higher DPI for better detail
            image = pdf_page_to_image(pdf_path, page_num=0, dpi=300)
            h, w = image.shape[:2]
            print(f"  Image: {w} x {h} px (300 DPI)")

            # Multi-view detection
            is_multi, seg_result = coach.is_multi_view_blueprint(image)

            if seg_result and seg_result.views:
                views_to_process = []
                for i, view in enumerate(seg_result.views):
                    x, y, vw, vh = view.bbox
                    area_pct = (view.area_ratio or 0) * 100
                    if area_pct >= 10:
                        views_to_process.append((x, y, vw, vh, view.label or f"view{i}"))
                        print(f"    View {i}: {vw}x{vh}, area={area_pct:.1f}%")
            else:
                views_to_process = [(0, 0, w, h, "full")]

            for x, y, vw, vh, label in views_to_process:
                x2 = min(w, x + vw)
                y2 = min(h, y + vh)
                view_image = image[y:y2, x:x2].copy()
                view_h = view_image.shape[0]

                safe_label = label.replace(" ", "_").replace("/", "_")

                # Calibrate scale from soundhole detection (102mm reference)
                mm_per_px = calibrate_scale_from_soundhole(view_image, soundhole_mm=102.0)
                if mm_per_px:
                    print(f"    Calibrated: {mm_per_px:.4f} mm/px (soundhole)")
                else:
                    # Fallback: estimate from body length (520mm Carlos Jumbo)
                    mm_per_px = CARLOS_JUMBO_BODY_LENGTH_MM / (view_h * 0.65)
                    print(f"    Estimated: {mm_per_px:.4f} mm/px (from body length)")

                # Method 1: Enhanced contour extraction
                contours = extract_contours_enhanced(view_image, min_area_ratio=0.005)
                if contours:
                    contours_mm = contours_to_mm(contours, view_h, mm_per_px=mm_per_px)
                    dxf_path = output_dir / f"{pdf_path.stem}_{safe_label}_enhanced.dxf"
                    if write_dxf_enhanced(contours_mm, str(dxf_path)):
                        size_kb = dxf_path.stat().st_size / 1024
                        print(f"    {dxf_path.name}: {len(contours)} contours ({size_kb:.1f} KB)")
                        total_dxfs += 1

                # Method 2: All edges as polylines (comprehensive)
                polylines = extract_all_edges_as_lines(view_image)
                if polylines:
                    polylines_mm = contours_to_mm(polylines, view_h, mm_per_px=mm_per_px)
                    dxf_path = output_dir / f"{pdf_path.stem}_{safe_label}_alledges.dxf"
                    if write_dxf_all_lines(polylines_mm, str(dxf_path)):
                        size_kb = dxf_path.stat().st_size / 1024
                        print(f"    {dxf_path.name}: {len(polylines)} polylines ({size_kb:.1f} KB)")
                        total_dxfs += 1

                # Save debug image showing detected edges
                gray = cv2.cvtColor(view_image, cv2.COLOR_BGR2GRAY)
                edges = multi_scale_edge_detection(gray)
                edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                debug_path = output_dir / f"{pdf_path.stem}_{safe_label}_edges.png"
                cv2.imwrite(str(debug_path), edges_bgr)

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Generated {total_dxfs} DXF files")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    generate_enhanced_dxfs()
