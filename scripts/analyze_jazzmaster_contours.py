#!/usr/bin/env python3
"""
Analyze all contours in detail to find missing features
"""
import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
from vectorizer_phase2 import rasterize_pdf, ColorFilter

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jaguar-Jazzmaster-Bodies-Separated.pdf"
    page_num = 2

    dpi = 400
    image = rasterize_pdf(pdf_path, page_num=page_num, dpi=dpi)
    height, width = image.shape[:2]
    mm_per_px = 25.4 / dpi

    color_filter = ColorFilter(tolerance=30)
    dark_mask = color_filter.extract_dark_lines(image, threshold=100)

    contours, _ = cv2.findContours(dark_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    print(f"Total contours: {len(contours)}")
    print("\nAll contours between 20mm and 200mm (potential features):")
    print("-" * 70)
    print(f"{'#':<5} {'Size (mm)':<20} {'Area':>12} {'Points':>8}")
    print("-" * 70)

    features = []
    for i, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px
        area = cv2.contourArea(c)

        # Show contours in the "feature" size range
        if 20 < max(w_mm, h_mm) < 200:
            features.append((i, w_mm, h_mm, area, len(c)))
            print(f"{i:<5} {w_mm:>7.1f} x {h_mm:<7.1f}   {area:>12.0f} {len(c):>8}")

    print(f"\nFound {len(features)} potential feature contours")

if __name__ == "__main__":
    main()
