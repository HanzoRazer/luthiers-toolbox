#!/usr/bin/env python3
"""
Debug test - use extract_dark_lines to get all dark content
"""
import sys
from pathlib import Path
import numpy as np
import cv2

# Add blueprint-import to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))

from vectorizer_phase2 import rasterize_pdf, ColorFilter

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jaguar-Jazzmaster-Bodies-Separated.pdf"
    page_num = 2  # Page 3 (0-indexed)

    print("=" * 60)
    print("Debug: Using extract_dark_lines")
    print("=" * 60)

    # Rasterize
    print("\nRasterizing PDF...")
    image = rasterize_pdf(pdf_path, page_num=page_num, dpi=300)
    height, width = image.shape[:2]
    print(f"Image: {width} x {height} pixels")

    # Extract all dark lines
    print("\nExtracting dark lines (threshold=100)...")
    color_filter = ColorFilter(tolerance=30)
    dark_mask = color_filter.extract_dark_lines(image, threshold=100)
    non_zero = cv2.countNonZero(dark_mask)
    print(f"Dark pixels in mask: {non_zero}")

    # Find contours
    print("\nFinding contours...")
    contours, _ = cv2.findContours(
        dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    print(f"Found {len(contours)} contours total")

    # Analyze contours
    dpi = 300
    mm_per_px = 25.4 / dpi

    contour_data = []
    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px
        points = len(c)
        contour_data.append({
            'idx': i, 'area': area, 'w_mm': w_mm, 'h_mm': h_mm, 'points': points, 'contour': c
        })

    # Sort by area
    contour_data.sort(key=lambda x: -x['area'])

    print("\n" + "-" * 60)
    print("Top 20 contours by area:")
    print("-" * 60)
    print(f"{'#':<6} {'Area':>12} {'Size (mm)':>16} {'Pts':>6}")
    for d in contour_data[:20]:
        print(f"{d['idx']:<6} {d['area']:>12.0f} {d['w_mm']:>7.1f}x{d['h_mm']:<7.1f} {d['points']:>6}")

    # Look for guitar-body sized contours
    print("\n" + "=" * 60)
    print("Looking for body-sized contours (200-600mm):")
    print("=" * 60)

    candidates = []
    for d in contour_data:
        max_dim = max(d['w_mm'], d['h_mm'])
        min_dim = min(d['w_mm'], d['h_mm'])
        if max_dim > 200:  # Any large contour
            candidates.append(d)
            print(f"  #{d['idx']}: {d['w_mm']:.1f}x{d['h_mm']:.1f}mm, area={d['area']:.0f}, pts={d['points']}")

    if not candidates:
        print("  No large contours found!")

    # Save debug preview
    print("\n" + "=" * 60)
    print("Saving debug preview...")
    print("=" * 60)

    preview = cv2.cvtColor(dark_mask, cv2.COLOR_GRAY2BGR)
    colors = [(0,0,255), (0,255,0), (255,0,0), (255,255,0), (0,255,255)]
    for i, d in enumerate(contour_data[:5]):
        cv2.drawContours(preview, [d['contour']], -1, colors[i % 5], 2)
        x, y, w, h = cv2.boundingRect(d['contour'])
        cv2.putText(preview, f"#{i}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, colors[i % 5], 2)

    preview_path = r"C:\Users\thepr\Downloads\jazzmaster_darklines_debug.png"
    cv2.imwrite(preview_path, preview)
    print(f"Saved: {preview_path}")

    # Also save just the mask
    mask_path = r"C:\Users\thepr\Downloads\jazzmaster_darklines_mask.png"
    cv2.imwrite(mask_path, dark_mask)
    print(f"Mask: {mask_path}")

if __name__ == "__main__":
    main()
