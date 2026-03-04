#!/usr/bin/env python3
"""
Extract Jazzmaster body with smoother curves
"""
import sys
from pathlib import Path
import numpy as np
import cv2

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api" / "app"))

from vectorizer_phase2 import rasterize_pdf, ColorFilter
from dxf_compat import create_document, add_polyline

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jaguar-Jazzmaster-Bodies-Separated.pdf"
    output_path = r"C:\Users\thepr\Downloads\jazzmaster_body_smooth.dxf"
    page_num = 2

    print("=" * 60)
    print("Extracting Jazzmaster Body - Smooth Version")
    print("=" * 60)

    # Higher DPI for better detail
    dpi = 400
    print(f"\nRasterizing PDF at {dpi} DPI...")
    image = rasterize_pdf(pdf_path, page_num=page_num, dpi=dpi)
    height, width = image.shape[:2]
    print(f"Image: {width} x {height} pixels")

    # Extract dark lines
    print("\nExtracting dark lines...")
    color_filter = ColorFilter(tolerance=30)
    dark_mask = color_filter.extract_dark_lines(image, threshold=100)

    # Find contours
    print("Finding contours...")
    contours, _ = cv2.findContours(
        dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE  # APPROX_NONE keeps all points
    )
    print(f"Found {len(contours)} contours")

    # Find largest body-sized contour
    mm_per_px = 25.4 / dpi

    best = None
    best_area = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area > best_area:
            x, y, w, h = cv2.boundingRect(c)
            w_mm = w * mm_per_px
            h_mm = h * mm_per_px
            if w_mm > 200 and h_mm > 200:
                best = c
                best_area = area

    if best is None:
        print("ERROR: No body-sized contour found!")
        return

    x, y, w, h = cv2.boundingRect(best)
    w_mm = w * mm_per_px
    h_mm = h * mm_per_px
    print(f"\nSelected contour: {w_mm:.1f} x {h_mm:.1f} mm, {len(best)} points")

    # Convert to mm coordinates
    print("\nConverting to mm...")
    points = best.reshape(-1, 2)

    mm_points = []
    for px, py in points:
        x_mm = px * mm_per_px
        y_mm = (height - py) * mm_per_px
        mm_points.append((x_mm, y_mm))

    # Center at origin
    xs = [p[0] for p in mm_points]
    ys = [p[1] for p in mm_points]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    centered = [(x - cx, y - cy) for x, y in mm_points]

    # Gentle simplification - 0.1mm tolerance for smoother curves
    print("Simplifying contour (0.1mm tolerance)...")
    pts_array = np.array(centered, dtype=np.float32).reshape(-1, 1, 2)
    epsilon = 0.1  # Very gentle simplification
    simplified = cv2.approxPolyDP(pts_array, epsilon, closed=True)
    simplified = simplified.reshape(-1, 2).tolist()
    print(f"Simplified from {len(centered)} to {len(simplified)} points")

    # Final dimensions
    xs = [p[0] for p in simplified]
    ys = [p[1] for p in simplified]
    final_width = max(xs) - min(xs)
    final_height = max(ys) - min(ys)
    print(f"Final dimensions: {final_width:.1f} x {final_height:.1f} mm")

    # Export to DXF
    print(f"\nExporting to: {output_path}")
    doc = create_document(version='R12')
    msp = doc.modelspace()

    point_tuples = [(float(x), float(y)) for x, y in simplified]
    add_polyline(msp, point_tuples, layer='BODY_OUTLINE', closed=True, version='R12')

    doc.saveas(output_path)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"DXF: {output_path}")
    print(f"Size: {final_width:.1f} x {final_height:.1f} mm")
    print(f"Points: {len(simplified)}")

if __name__ == "__main__":
    main()
