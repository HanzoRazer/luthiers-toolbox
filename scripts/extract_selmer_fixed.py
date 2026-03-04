#!/usr/bin/env python3
"""
Extract Selmer Maccaferri with gap closing
"""
import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api" / "app"))

from vectorizer_phase2 import rasterize_pdf, ColorFilter
from dxf_compat import create_document, add_polyline

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Selmer-Maccaferri-D-hole-MM-01.pdf"
    output_path = r"C:\Users\thepr\Downloads\selmer_maccaferri_fixed.dxf"

    print("=" * 60)
    print("Extracting Selmer Maccaferri (with gap closing)")
    print("=" * 60)

    dpi = 400
    print(f"\nRasterizing at {dpi} DPI...")
    image = rasterize_pdf(pdf_path, page_num=0, dpi=dpi)
    height, width = image.shape[:2]
    mm_per_px = 25.4 / dpi
    print(f"Image: {width}x{height}px")

    # Extract dark lines with lower threshold to catch more
    print("\nExtracting dark lines...")
    color_filter = ColorFilter(tolerance=30)
    dark_mask = color_filter.extract_dark_lines(image, threshold=120)

    # CLOSE GAPS using morphological operations
    print("Closing gaps in lines...")
    # Dilate to connect nearby lines, then erode to restore thickness
    kernel_close = np.ones((5, 5), np.uint8)
    closed_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)

    # Find contours
    print("Finding contours...")
    contours, hierarchy = cv2.findContours(
        closed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    print(f"Found {len(contours)} contours")

    # Find body-sized contour (400-550mm)
    body_contour = None
    body_size = (0, 0)

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px

        if 350 < max(w_mm, h_mm) < 550 and 300 < min(w_mm, h_mm) < 450:
            area = cv2.contourArea(c)
            if body_contour is None or area > cv2.contourArea(body_contour):
                body_contour = c
                body_size = (w_mm, h_mm)

    if body_contour is None:
        print("ERROR: No body outline found!")
        # List largest contours for debugging
        contours_by_size = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            contours_by_size.append((w * mm_per_px, h * mm_per_px, c))
        contours_by_size.sort(key=lambda x: -max(x[0], x[1]))
        print("\nLargest contours:")
        for w, h, _ in contours_by_size[:10]:
            print(f"  {w:.0f}x{h:.0f}mm")
        return

    print(f"\nBody outline: {body_size[0]:.0f}x{body_size[1]:.0f}mm, {len(body_contour)} pts")

    # Convert body contour to mm
    pts = body_contour.reshape(-1, 2)
    mm_pts = []
    for px, py in pts:
        x_mm = px * mm_per_px
        y_mm = (height - py) * mm_per_px
        mm_pts.append((x_mm, y_mm))

    # Center
    xs = [p[0] for p in mm_pts]
    ys = [p[1] for p in mm_pts]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    centered = [(x - cx, y - cy) for x, y in mm_pts]

    # Simplify
    print("Simplifying contour...")
    pts_array = np.array(centered, dtype=np.float32).reshape(-1, 1, 2)
    simplified = cv2.approxPolyDP(pts_array, 0.3, closed=True)  # 0.3mm tolerance
    simplified = simplified.reshape(-1, 2).tolist()
    print(f"Simplified to {len(simplified)} points")

    # Create DXF
    print(f"\nExporting to: {output_path}")
    doc = create_document(version='R12')
    msp = doc.modelspace()

    point_tuples = [(float(x), float(y)) for x, y in simplified]
    add_polyline(msp, point_tuples, layer='BODY_OUTLINE', closed=True, version='R12')

    # Also extract D-hole from original mask (less aggressive closing)
    print("\nExtracting D-hole...")
    d_hole_mask = color_filter.extract_dark_lines(image, threshold=100)
    kernel_small = np.ones((3, 3), np.uint8)
    d_hole_mask = cv2.morphologyEx(d_hole_mask, cv2.MORPH_CLOSE, kernel_small)

    d_contours, _ = cv2.findContours(d_hole_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    for c in d_contours:
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px

        # D-hole: ~200x100mm
        if 150 < w_mm < 250 and 70 < h_mm < 130:
            pts = c.reshape(-1, 2)
            mm_pts = [(px * mm_per_px - cx, (height - py) * mm_per_px - cy) for px, py in pts]
            pts_array = np.array(mm_pts, dtype=np.float32).reshape(-1, 1, 2)
            simplified_d = cv2.approxPolyDP(pts_array, 0.2, closed=True)
            simplified_d = simplified_d.reshape(-1, 2).tolist()
            point_tuples = [(float(x), float(y)) for x, y in simplified_d]
            add_polyline(msp, point_tuples, layer='D_HOLE', closed=True, version='R12')
            print(f"  D-hole: {w_mm:.0f}x{h_mm:.0f}mm, {len(simplified_d)} pts")
            break

    doc.saveas(output_path)

    # Final dimensions
    xs = [p[0] for p in simplified]
    ys = [p[1] for p in simplified]
    print(f"\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"DXF: {output_path}")
    print(f"Body: {max(xs)-min(xs):.0f}x{max(ys)-min(ys):.0f}mm, {len(simplified)} pts")

if __name__ == "__main__":
    main()
