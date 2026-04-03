#!/usr/bin/env python3
"""
Generate DXF files from Carlos Jumbo blueprints.

This script:
1. Converts Carlos Jumbo PDF pages to images
2. Runs multi-view detection to find separate views
3. For each view containing a body outline, extracts contours
4. Generates DXF files for each extracted view

Usage:
    python generate_carlos_jumbo_dxf.py

Output:
    live_test_output/carlos_jumbo_dxf/
        JUMBO-CARLOS-1-3_view0.dxf
        JUMBO-CARLOS-2-3_view0.dxf
        ...
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure we can import from the photo-vectorizer directory
sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np

# Try to import required modules
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    print("WARNING: PyMuPDF not available. Install with: pip install PyMuPDF")

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
    print("WARNING: ezdxf not available. Install with: pip install ezdxf")

from geometry_coach_v2 import GeometryCoachV2, CoachV2Config


def pdf_page_to_image(pdf_path: Path, page_num: int = 0, dpi: int = 200) -> np.ndarray:
    """Convert a PDF page to a numpy array (BGR format for OpenCV)."""
    if not FITZ_AVAILABLE:
        raise ImportError("PyMuPDF required for PDF conversion")

    doc = fitz.open(str(pdf_path))
    page = doc[page_num]

    # Render at specified DPI
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Convert to numpy array
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

    # Convert RGB to BGR for OpenCV
    if pix.n == 4:  # RGBA
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:  # RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    doc.close()
    return img


def extract_body_contour(image: np.ndarray, min_area_ratio: float = 0.05) -> list:
    """
    Extract the main body contour from an image.

    Returns list of contours (numpy arrays of points).
    """
    h, w = image.shape[:2]
    total_area = h * w

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply adaptive threshold for blueprints
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 21, 5
    )

    # Clean up with morphological operations
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # Find contours
    contours, hierarchy = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Filter by area and select significant contours
    significant_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area / total_area > min_area_ratio:
            # Simplify contour to reduce noise
            epsilon = 0.001 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            significant_contours.append(approx)

    # Sort by area (largest first)
    significant_contours.sort(key=lambda c: cv2.contourArea(c), reverse=True)

    return significant_contours


def contours_to_mm(contours: list, image_height_px: int,
                   target_height_mm: float = 500.0) -> list:
    """Convert contour pixel coordinates to mm coordinates."""
    mm_per_px = target_height_mm / image_height_px

    mm_contours = []
    for cnt in contours:
        pts = cnt.reshape(-1, 2).astype(float)
        # Convert coordinates: flip Y for CAD convention
        pts[:, 0] *= mm_per_px  # X in mm
        pts[:, 1] = (image_height_px - pts[:, 1]) * mm_per_px  # Y flipped and in mm
        mm_contours.append(pts)

    return mm_contours


def write_dxf(contours_mm: list, output_path: str,
              layer_name: str = "BODY_OUTLINE") -> bool:
    """Write contours to DXF file."""
    if not EZDXF_AVAILABLE:
        print("ezdxf not available - cannot write DXF")
        return False

    try:
        # Use R2010 format for better compatibility
        doc = ezdxf.new("R12")
        msp = doc.modelspace()

        # Set units to mm
        doc.header["$INSUNITS"] = 4  # mm
        doc.header["$MEASUREMENT"] = 1  # metric

        # Add layer
        doc.layers.add(layer_name, color=7)  # White/black depending on bg

        for idx, pts in enumerate(contours_mm):
            if len(pts) < 3:
                continue

            # Convert to list of tuples
            pts_list = [(float(p[0]), float(p[1])) for p in pts]

            # Add as LWPOLYLINE (cleaner than individual lines)
            msp.add_lwpolyline(
                pts_list,
                dxfattribs={"layer": layer_name},
                close=True
            )

        doc.saveas(output_path)
        return True

    except Exception as e:
        print(f"DXF export failed: {e}")
        return False


def generate_dxfs():
    """Generate DXF files from Carlos Jumbo blueprints."""

    if not FITZ_AVAILABLE:
        print("ERROR: PyMuPDF required - pip install PyMuPDF")
        return

    if not EZDXF_AVAILABLE:
        print("ERROR: ezdxf required - pip install ezdxf")
        return

    # Find the Carlos Jumbo PDFs
    repo_root = Path(__file__).parent.parent.parent
    jumbo_dir = repo_root / "Guitar Plans" / "Jumbo Carlos"

    if not jumbo_dir.exists():
        print(f"ERROR: Directory not found: {jumbo_dir}")
        return

    pdfs = sorted(jumbo_dir.glob("JUMBO-CARLOS-*.pdf"))
    if not pdfs:
        print(f"ERROR: No Carlos Jumbo PDFs found in {jumbo_dir}")
        return

    print(f"Found {len(pdfs)} Carlos Jumbo PDFs")
    print("=" * 60)

    # Create coach with multi-view detection
    config = CoachV2Config(
        enable_multi_view_detection=True,
        multi_view_min_area_ratio=0.05,
        multi_view_score_threshold=0.50,
    )
    coach = GeometryCoachV2(config)

    # Output directory for DXF files
    output_dir = Path(__file__).parent / "live_test_output" / "carlos_jumbo_dxf"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_dxfs = 0

    for pdf_path in pdfs:
        print(f"\n[PDF] {pdf_path.name}")
        print("-" * 40)

        try:
            # Convert PDF to image at higher DPI for better detail
            image = pdf_page_to_image(pdf_path, page_num=0, dpi=200)
            h, w = image.shape[:2]
            print(f"  Image size: {w} x {h} px")

            # Run multi-view detection
            is_multi, seg_result = coach.is_multi_view_blueprint(image)

            if seg_result is None:
                print("  No segmentation result - processing as single view")
                views_to_process = [(0, 0, w, h, "full")]
            elif not seg_result.views:
                print("  No views detected - processing as single view")
                views_to_process = [(0, 0, w, h, "full")]
            else:
                print(f"  Detected {len(seg_result.views)} views")
                views_to_process = []
                for i, view in enumerate(seg_result.views):
                    x, y, vw, vh = view.bbox
                    area_pct = (view.area_ratio or 0) * 100
                    label = view.label or f"view{i}"

                    # Skip small views (likely headers/footers)
                    if area_pct < 10:
                        print(f"    [{i}] {label}: skipped (area {area_pct:.1f}% < 10%)")
                        continue

                    views_to_process.append((x, y, vw, vh, label))
                    print(f"    [{i}] {label}: {vw}x{vh} at ({x},{y}), area={area_pct:.1f}%")

            # Process each view
            for idx, (x, y, vw, vh, label) in enumerate(views_to_process):
                # Extract view region
                x2 = min(w, x + vw)
                y2 = min(h, y + vh)
                view_image = image[y:y2, x:x2].copy()

                # Extract contours from this view
                contours = extract_body_contour(view_image, min_area_ratio=0.03)

                if not contours:
                    print(f"    No contours found in {label}")
                    continue

                print(f"    Found {len(contours)} contour(s) in {label}")

                # Convert to mm (assuming 500mm body height as standard)
                view_h = view_image.shape[0]
                contours_mm = contours_to_mm(contours, view_h, target_height_mm=500.0)

                # Generate DXF filename
                safe_label = label.replace(" ", "_").replace("/", "_")
                dxf_name = f"{pdf_path.stem}_{safe_label}.dxf"
                dxf_path = output_dir / dxf_name

                # Write DXF
                if write_dxf(contours_mm, str(dxf_path)):
                    file_size = dxf_path.stat().st_size / 1024
                    print(f"    Created: {dxf_name} ({file_size:.1f} KB)")
                    total_dxfs += 1
                else:
                    print(f"    Failed to create: {dxf_name}")

                # Also save annotated view image for reference
                annotated = view_image.copy()
                for cnt in contours:
                    cv2.drawContours(annotated, [cnt], -1, (0, 255, 0), 2)
                img_path = output_dir / f"{pdf_path.stem}_{safe_label}_contours.png"
                cv2.imwrite(str(img_path), annotated)

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Generated {total_dxfs} DXF files")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    generate_dxfs()
