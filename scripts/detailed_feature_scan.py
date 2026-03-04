#!/usr/bin/env python3
"""
Detailed scan of all features in routing PDF
"""
import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "blueprint-import"))
from vectorizer_phase2 import rasterize_pdf, ColorFilter

def main():
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jazzmaster-Body-Route-Pickguard.pdf"

    dpi = 400
    image = rasterize_pdf(pdf_path, page_num=0, dpi=dpi)
    height, width = image.shape[:2]
    mm_per_px = 25.4 / dpi

    color_filter = ColorFilter(tolerance=30)
    dark_mask = color_filter.extract_dark_lines(image, threshold=100)

    contours, _ = cv2.findContours(dark_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Collect all features > 30mm
    features = []
    for c in contours:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        w_mm = w * mm_per_px
        h_mm = h * mm_per_px

        if max(w_mm, h_mm) > 30:
            features.append({
                'w_mm': w_mm, 'h_mm': h_mm, 'area': area, 'pts': len(c)
            })

    features.sort(key=lambda x: -x['area'])

    print(f"All features > 30mm ({len(features)} total):")
    print("-" * 70)
    print(f"{'#':<4} {'Width':>8} {'Height':>8} {'Area':>12} {'Points':>8}  Category")
    print("-" * 70)

    for i, f in enumerate(features):
        w, h = f['w_mm'], f['h_mm']
        max_d, min_d = max(w, h), min(w, h)

        # Categorize
        if 450 < max_d < 600 and 300 < min_d < 450:
            cat = "BODY"
        elif 300 < max_d < 500 and 200 < min_d < 400:
            cat = "PICKGUARD"
        elif 85 < max_d < 110 and 45 < min_d < 65:
            cat = "PICKUP?"
        elif 55 < max_d < 85 and 50 < min_d < 80:
            cat = "NECK_POCKET?"
        elif 90 < max_d < 130 and 40 < min_d < 70:
            cat = "CONTROL?"
        else:
            cat = ""

        print(f"{i:<4} {w:>7.0f}mm {h:>7.0f}mm {f['area']:>12.0f} {f['pts']:>8}  {cat}")

if __name__ == "__main__":
    main()
