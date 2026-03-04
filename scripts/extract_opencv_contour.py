#!/usr/bin/env python3
"""
Extract body outline using OpenCV contour detection.

Approach:
1. Rasterize PDF at high DPI
2. Apply edge detection
3. Find contours
4. Select largest closed contour (body outline)
5. Export to DXF
"""

import cv2
import numpy as np
import fitz  # PyMuPDF
from pathlib import Path
import sys

# Add system path for ezdxf compat
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api" / "app"))


def pdf_to_image(pdf_path: str, page_num: int = 0, dpi: int = 300):
    """Convert PDF page to numpy array."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    # High DPI for better edge detection
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Convert to numpy array
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )

    # Convert to BGR if needed
    if pix.n == 4:  # RGBA
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 1:  # Grayscale
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    doc.close()
    return img, dpi


def find_body_contour(img, dpi=300):
    """Find the largest closed contour (body outline)."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply threshold to get binary image - use lower threshold to catch dark lines
    # Invert so lines are white on black
    _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # Also try to isolate darker/colored lines (red appears dark in grayscale)
    # Apply morphological operations to clean up
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Find ALL contours (not just external)
    contours, hierarchy = cv2.findContours(
        binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )

    print(f"Found {len(contours)} contours")

    if not contours:
        return None

    # Find largest contour by area
    contours_with_area = [(cv2.contourArea(c), c) for c in contours]
    contours_with_area.sort(key=lambda x: x[0], reverse=True)

    print("\nTop 10 contours by area:")
    for i, (area, c) in enumerate(contours_with_area[:10]):
        x, y, w, h = cv2.boundingRect(c)
        print(f"  #{i}: area={area:.0f}, bbox={w}x{h}, points={len(c)}")

    # Convert pixel dimensions to mm for filtering
    mm_per_px = 25.4 / dpi
    img_h, img_w = img.shape[:2]

    # Find contours that are guitar-body sized (250-500mm in longest dimension)
    print("\nLooking for body-sized contours (250-500mm)...")

    candidates = []
    for area, c in contours_with_area:
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px
        max_dim = max(w_mm, h_mm)
        min_dim = min(w_mm, h_mm)

        # Guitar body: 250-500mm long, 200-400mm wide, many points
        if 200 < max_dim < 550 and min_dim > 100 and len(c) > 30:
            candidates.append((area, c, w_mm, h_mm))
            print(f"  Candidate: {w_mm:.0f}x{h_mm:.0f}mm, area={area:.0f}, pts={len(c)}")

    if candidates:
        # Return largest candidate
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0]
        print(f"\nSelected: {best[2]:.0f}x{best[3]:.0f}mm, {len(best[1])} points")
        return best[1]

    # Fallback: skip page border, return second largest
    print("\nNo body-sized contours found, using second largest")
    if len(contours_with_area) > 1:
        return contours_with_area[1][1]
    return contours_with_area[0][1]


def contour_to_mm(contour, dpi: int, img_height: int):
    """Convert contour from pixels to mm, centered at origin."""
    # Flatten contour
    points = contour.reshape(-1, 2)

    # Convert pixels to mm (at given DPI)
    mm_per_pixel = 25.4 / dpi

    mm_points = []
    for x, y in points:
        x_mm = x * mm_per_pixel
        y_mm = (img_height - y) * mm_per_pixel  # Flip Y for CAD
        mm_points.append((x_mm, y_mm))

    # Center at origin
    xs = [p[0] for p in mm_points]
    ys = [p[1] for p in mm_points]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2

    centered = [(x - cx, y - cy) for x, y in mm_points]
    return centered


def simplify_contour(points, tolerance_mm: float = 1.0):
    """Simplify contour using Douglas-Peucker algorithm."""
    # Convert to numpy for OpenCV
    pts = np.array(points, dtype=np.float32).reshape(-1, 1, 2)

    # Approximate contour
    epsilon = tolerance_mm
    approx = cv2.approxPolyDP(pts, epsilon, closed=True)

    return approx.reshape(-1, 2).tolist()


def export_to_dxf(points, output_path: str):
    """Export points to DXF using ezdxf."""
    try:
        from util.dxf_compat import create_document, add_polyline
    except ImportError:
        import ezdxf
        def create_document(version='R12', setup=False):
            return ezdxf.new(version)
        def add_polyline(msp, points, layer='0', closed=False, version='R12'):
            n = len(points)
            end = n if closed else n - 1
            for i in range(end):
                msp.add_line(points[i], points[(i + 1) % n], dxfattribs={'layer': layer})

    doc = create_document(version='R12')
    msp = doc.modelspace()

    # Convert to tuples
    point_tuples = [(float(x), float(y)) for x, y in points]

    add_polyline(msp, point_tuples, layer='BODY_OUTLINE', closed=True, version='R12')
    doc.saveas(output_path)


def main():
    # Use the separated bodies PDF, page 3 (index 2) has clean Jazzmaster outline
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jaguar-Jazzmaster-Bodies-Separated.pdf"
    output_path = r"C:\Users\thepr\Downloads\jazzmaster_body.dxf"
    page_num = 2  # Page 3 = index 2 (Jazzmaster in red)

    print(f"Processing: {pdf_path} (page {page_num + 1})\n")

    # Step 1: Rasterize PDF
    print("Rasterizing PDF at 300 DPI...")
    img, dpi = pdf_to_image(pdf_path, page_num=page_num, dpi=300)
    print(f"Image size: {img.shape[1]} x {img.shape[0]} pixels")

    # Step 2: Find body contour
    print("\nFinding contours...")
    contour = find_body_contour(img, dpi)

    if contour is None:
        print("ERROR: No contours found!")
        return

    print(f"\nBest contour has {len(contour)} points")

    # Step 3: Convert to mm
    print("\nConverting to millimeters...")
    mm_points = contour_to_mm(contour, dpi, img.shape[0])

    # Calculate dimensions
    xs = [p[0] for p in mm_points]
    ys = [p[1] for p in mm_points]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    print(f"Raw dimensions: {width:.1f} x {height:.1f} mm")

    # Step 4: Simplify
    print("\nSimplifying contour...")
    simplified = simplify_contour(mm_points, tolerance_mm=0.5)
    print(f"Simplified to {len(simplified)} points")

    # Step 5: Export to DXF
    print(f"\nExporting to: {output_path}")
    export_to_dxf(simplified, output_path)

    # Final dimensions
    xs = [p[0] for p in simplified]
    ys = [p[1] for p in simplified]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    print(f"Final dimensions: {width:.1f} x {height:.1f} mm")
    print(f"Points: {len(simplified)}")


if __name__ == "__main__":
    main()
