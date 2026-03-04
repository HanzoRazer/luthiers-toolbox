#!/usr/bin/env python3
"""
Debug test - analyze what contours are found before selection
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
    print("Debug: Analyzing Contours")
    print("=" * 60)

    # Rasterize
    print("\nRasterizing PDF...")
    image = rasterize_pdf(pdf_path, page_num=page_num, dpi=300)
    height, width = image.shape[:2]
    print(f"Image: {width} x {height} pixels")

    # Extract black mask
    print("\nExtracting black pixels...")
    color_filter = ColorFilter(tolerance=30)

    # Create black mask (BGR = 0,0,0)
    black_mask = color_filter.create_color_mask(image, 'black')
    non_zero = cv2.countNonZero(black_mask)
    print(f"Black pixels in mask: {non_zero}")

    # Find contours
    print("\nFinding contours...")
    contours, _ = cv2.findContours(
        black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    print(f"Found {len(contours)} contours total")

    # Analyze contours
    print("\n" + "-" * 60)
    print("Top 20 contours by area:")
    print("-" * 60)

    dpi = 300
    mm_per_px = 25.4 / dpi

    contour_data = []
    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px
        perimeter = cv2.arcLength(c, True)
        points = len(c)

        contour_data.append({
            'idx': i,
            'area': area,
            'w_mm': w_mm,
            'h_mm': h_mm,
            'perimeter': perimeter,
            'points': points,
            'contour': c
        })

    # Sort by area
    contour_data.sort(key=lambda x: -x['area'])

    print(f"{'#':<4} {'Area':>12} {'Size (mm)':>16} {'Perim':>10} {'Pts':>6}")
    print("-" * 60)

    for d in contour_data[:20]:
        print(f"{d['idx']:<4} {d['area']:>12.0f} {d['w_mm']:>7.1f}x{d['h_mm']:<7.1f} {d['perimeter']:>10.1f} {d['points']:>6}")

    # Look for guitar-body sized contours
    print("\n" + "=" * 60)
    print("Looking for guitar-body sized contours (300-550mm x 200-400mm):")
    print("=" * 60)

    candidates = []
    for d in contour_data:
        max_dim = max(d['w_mm'], d['h_mm'])
        min_dim = min(d['w_mm'], d['h_mm'])
        # Guitar body: ~500mm long, ~350mm wide
        if 250 < max_dim < 600 and 150 < min_dim < 450:
            candidates.append(d)
            print(f"  Candidate #{d['idx']}: {d['w_mm']:.1f}x{d['h_mm']:.1f}mm, {d['points']} pts")

    if not candidates:
        print("  No candidates found! Checking size distribution...")
        print("\n  Size histogram:")
        for d in contour_data[:30]:
            print(f"    {d['w_mm']:.0f}x{d['h_mm']:.0f}mm (area={d['area']:.0f})")

    # Save a debug preview image
    print("\n" + "=" * 60)
    print("Saving debug preview...")
    print("=" * 60)

    preview = cv2.cvtColor(black_mask, cv2.COLOR_GRAY2BGR)
    # Draw top 5 contours in different colors
    colors = [(0,0,255), (0,255,0), (255,0,0), (255,255,0), (0,255,255)]
    for i, d in enumerate(contour_data[:5]):
        cv2.drawContours(preview, [d['contour']], -1, colors[i % 5], 2)
        x, y, w, h = cv2.boundingRect(d['contour'])
        cv2.putText(preview, f"#{i}: {d['w_mm']:.0f}x{d['h_mm']:.0f}mm",
                    (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, colors[i % 5], 2)

    preview_path = r"C:\Users\thepr\Downloads\jazzmaster_contours_debug.png"
    cv2.imwrite(preview_path, preview)
    print(f"Saved: {preview_path}")

if __name__ == "__main__":
    main()
